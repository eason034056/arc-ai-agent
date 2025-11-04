"""
On-chain Service

This module provides high-level blockchain operations:
- Execute batch payouts via PayrollVault contract
- Check transaction status
- Handle gas estimation
- Retry failed transactions

Smart Contract: PayrollVault.sol
Network: Arc Testnet
Token: USDC (6 decimals)
"""

import json
from typing import List, Dict, Any
from decimal import Decimal

from web3 import Web3
from web3.exceptions import ContractLogicError, TimeExhausted
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OnchainService:
    """
    Blockchain Service for Payroll Operations
    
    This class encapsulates all blockchain interactions.
    It provides high-level methods for executing payroll transactions.
    
    Attributes:
        w3: Web3 instance connected to Arc Testnet
        account: Operator account (has OPERATOR_ROLE in contract)
        contract: PayrollVault contract instance
        
    Usage:
        service = OnchainService()
        
        tx_hash = service.batch_payout(
            recipients=["0x1111...", "0x2222..."],
            amounts=[5000000000, 6000000000],
            batch_id="batch_123",
            metadata="November 2025 payroll"
        )
        
        print(f"Transaction: {tx_hash}")
    """
    
    def __init__(self):
        """
        Initialize the on-chain service
        
        Steps:
        1. Connect to Arc Testnet RPC
        2. Load operator account from private key
        3. Load PayrollVault contract ABI
        4. Create contract instance
        """
        settings = get_settings()
        
        # ========================================
        # CONNECT TO BLOCKCHAIN
        # ========================================
        # Create Web3 instance connected to Arc Testnet
        # Web3 is the main interface for blockchain interactions
        self.w3 = Web3(Web3.HTTPProvider(settings.arc_rpc_url))
        
        # Verify connection
        if not self.w3.is_connected():
            raise ConnectionError(
                f"Failed to connect to Arc Testnet: {settings.arc_rpc_url}"
            )
        
        logger.info(
            "Connected to Arc Testnet",
            extra={
                "rpc_url": settings.arc_rpc_url,
                "chain_id": self.w3.eth.chain_id
            }
        )
        
        # ========================================
        # LOAD OPERATOR ACCOUNT
        # ========================================
        # The operator account sends transactions and pays gas
        # It must have OPERATOR_ROLE in the PayrollVault contract
        try:
            self.account = self.w3.eth.account.from_key(settings.private_key)
            
            logger.info(
                "Operator account loaded",
                extra={"address": self.account.address}
            )
        except Exception as e:
            raise ValueError(f"Invalid private key: {str(e)}")
        
        # ========================================
        # LOAD CONTRACT
        # ========================================
        # Load the ABI (Application Binary Interface)
        # ABI defines how to interact with the smart contract
        try:
            with open(settings.payroll_contract_abi_path, 'r') as f:
                contract_abi = json.load(f)
            
            logger.info(
                "Contract ABI loaded",
                extra={"path": settings.payroll_contract_abi_path}
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Contract ABI not found: {settings.payroll_contract_abi_path}\n"
                "Please deploy the contract and copy the ABI file."
            )
        
        # Create contract instance
        # This allows us to call contract functions
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.payroll_contract_address),
            abi=contract_abi
        )
        
        logger.info(
            "PayrollVault contract loaded",
            extra={"address": settings.payroll_contract_address}
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def batch_payout(
        self,
        recipients: List[str],
        amounts: List[int],
        batch_id: str,
        metadata: str
    ) -> str:
        """
        Execute batch payout transaction
        
        Calls PayrollVault.batchPayout() on Arc Testnet.
        Automatically retries on failure (up to 3 attempts).
        
        Args:
            recipients: List of wallet addresses
            amounts: List of USDC amounts (in smallest units, 6 decimals)
            batch_id: Unique batch identifier
            metadata: Additional information string
            
        Returns:
            Transaction hash (hex string starting with 0x)
            
        Raises:
            ContractLogicError: If contract reverts (e.g., insufficient funds)
            TimeExhausted: If transaction doesn't confirm in time
            Exception: Other blockchain errors
            
        Example:
            service = OnchainService()
            
            tx_hash = service.batch_payout(
                recipients=[
                    "0x1111111111111111111111111111111111111111",
                    "0x2222222222222222222222222222222222222222"
                ],
                amounts=[
                    5000000000,  # 5,000 USDC (6 decimals)
                    6000000000   # 6,000 USDC
                ],
                batch_id="batch_123",
                metadata="November 2025 payroll"
            )
            
            print(f"Transaction sent: {tx_hash}")
        """
        logger.info(
            "Preparing batch payout transaction",
            extra={
                "batch_id": batch_id,
                "recipient_count": len(recipients),
                "total_amount": sum(amounts)
            }
        )
        
        # ========================================
        # VALIDATE INPUTS
        # ========================================
        if len(recipients) != len(amounts):
            raise ValueError(
                f"Recipients ({len(recipients)}) and amounts ({len(amounts)}) "
                "length mismatch"
            )
        
        if len(recipients) == 0:
            raise ValueError("No recipients provided")
        
        # Ensure all addresses are checksummed
        # Ethereum addresses are case-sensitive (EIP-55)
        recipients = [Web3.to_checksum_address(addr) for addr in recipients]
        
        # Convert batch_id to bytes32
        # Solidity bytes32 = 32 bytes
        batch_id_bytes = batch_id.encode('utf-8')[:32].ljust(32, b'\x00')
        
        # ========================================
        # BUILD TRANSACTION
        # ========================================
        try:
            # Get current nonce
            # Nonce = number of transactions sent by this account
            # Each transaction must have a unique, sequential nonce
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Estimate gas
            # Gas = computational cost of the transaction
            try:
                gas_estimate = self.contract.functions.batchPayout(
                    recipients,
                    amounts,
                    batch_id_bytes,
                    metadata
                ).estimate_gas({'from': self.account.address})
                
                # Add 20% buffer to gas estimate
                # This prevents out-of-gas errors
                gas_limit = int(gas_estimate * 1.2)
                
                logger.info(
                    "Gas estimated",
                    extra={
                        "batch_id": batch_id,
                        "gas_estimate": gas_estimate,
                        "gas_limit": gas_limit
                    }
                )
            except ContractLogicError as e:
                # Gas estimation failed = transaction will revert
                logger.error(
                    "Gas estimation failed (transaction will revert)",
                    extra={
                        "batch_id": batch_id,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
            
            # Get current gas price
            # Gas price = how much to pay per unit of gas
            # Higher gas price = faster confirmation
            gas_price = self.w3.eth.gas_price
            
            # Build transaction dictionary
            # This defines all transaction parameters
            transaction = self.contract.functions.batchPayout(
                recipients,
                amounts,
                batch_id_bytes,
                metadata
            ).build_transaction({
                'from': self.account.address,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            logger.info(
                "Transaction built",
                extra={
                    "batch_id": batch_id,
                    "gas_limit": gas_limit,
                    "gas_price": gas_price,
                    "nonce": nonce
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to build transaction",
                extra={
                    "batch_id": batch_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
        # ========================================
        # SIGN AND SEND TRANSACTION
        # ========================================
        try:
            # Sign transaction with private key
            # Signing proves you own the account
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.account.key
            )
            
            logger.info(
                "Transaction signed",
                extra={"batch_id": batch_id}
            )
            
            # Send signed transaction to blockchain
            # This broadcasts the transaction to the network
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Convert bytes to hex string
            tx_hash_hex = tx_hash.hex()
            
            logger.info(
                "Transaction sent to blockchain",
                extra={
                    "batch_id": batch_id,
                    "tx_hash": tx_hash_hex
                }
            )
            
            # ========================================
            # WAIT FOR CONFIRMATION (optional)
            # ========================================
            # Wait for transaction to be mined (included in a block)
            # Timeout after 120 seconds
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(
                    tx_hash,
                    timeout=120
                )
                
                # Check if transaction succeeded
                # status = 1 means success, 0 means reverted
                if receipt['status'] == 1:
                    logger.info(
                        "Transaction confirmed successfully",
                        extra={
                            "batch_id": batch_id,
                            "tx_hash": tx_hash_hex,
                            "block_number": receipt['blockNumber'],
                            "gas_used": receipt['gasUsed']
                        }
                    )
                else:
                    logger.error(
                        "Transaction reverted",
                        extra={
                            "batch_id": batch_id,
                            "tx_hash": tx_hash_hex,
                            "block_number": receipt['blockNumber']
                        }
                    )
                    raise ContractLogicError("Transaction reverted on-chain")
                
            except TimeExhausted:
                # Transaction not confirmed within timeout
                # It might still be pending or might have failed
                logger.warning(
                    "Transaction confirmation timeout (still might succeed)",
                    extra={
                        "batch_id": batch_id,
                        "tx_hash": tx_hash_hex
                    }
                )
                # Don't raise - return tx_hash anyway
                # Caller can check status later
            
            return tx_hash_hex
        
        except Exception as e:
            logger.error(
                "Failed to send transaction",
                extra={
                    "batch_id": batch_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction receipt from blockchain
        
        Receipt includes:
        - status (1 = success, 0 = failed)
        - blockNumber (which block included this transaction)
        - gasUsed (actual gas consumed)
        - logs (events emitted)
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Receipt dictionary
            
        Example:
            receipt = service.get_transaction_receipt(
                "0xabc123..."
            )
            
            print(f"Status: {receipt['status']}")
            print(f"Block: {receipt['blockNumber']}")
            print(f"Gas: {receipt['gasUsed']}")
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            return {
                'status': receipt['status'],
                'blockNumber': receipt['blockNumber'],
                'gasUsed': receipt['gasUsed'],
                'logs': receipt['logs']
            }
        
        except Exception as e:
            logger.error(
                "Failed to get transaction receipt",
                extra={
                    "tx_hash": tx_hash,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_account_balance(self, address: str = None) -> Decimal:
        """
        Get account balance (native token, not USDC)
        
        Args:
            address: Address to check (defaults to operator address)
            
        Returns:
            Balance in ETH (or native token)
        """
        if address is None:
            address = self.account.address
        
        balance_wei = self.w3.eth.get_balance(address)
        balance_eth = self.w3.from_wei(balance_wei, 'ether')
        
        return Decimal(str(balance_eth))

