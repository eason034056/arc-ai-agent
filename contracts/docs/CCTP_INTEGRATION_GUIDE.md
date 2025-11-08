# CCTP Cross-Chain Integration Guide

> Complete guide for integrating Circle's Cross-Chain Transfer Protocol (CCTP) into the PayrollVault system

## Table of Contents

1. [Overview](#overview)
2. [What is CCTP?](#what-is-cctp)
3. [Architecture](#architecture)
4. [Smart Contract Integration](#smart-contract-integration)
5. [Testing Guide](#testing-guide)
6. [Deployment Guide](#deployment-guide)
7. [Backend Integration](#backend-integration)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)
10. [Reference](#reference)

---

## Overview

This guide explains how the PayrollVault system integrates with Circle's CCTP to enable cross-chain USDC transfers for payroll distribution.

### Key Features

✅ **Native USDC Transfers** - Send USDC to any CCTP-supported chain  
✅ **No Slippage** - 1:1 transfer ratio guaranteed  
✅ **No Liquidity Pools** - Direct burn-and-mint mechanism  
✅ **Fast Settlement** - Typically 15-20 minutes  
✅ **Secure** - Backed by Circle's attestation service  

### Supported Chains

**Mainnet:**
- Ethereum
- Avalanche C-Chain
- Optimism
- Arbitrum One
- Base
- Polygon PoS

**Testnet:**
- Ethereum Sepolia
- Avalanche Fuji
- Optimism Sepolia
- Arbitrum Sepolia
- Base Sepolia
- Polygon Mumbai
- Arc Testnet (check official docs)

---

## What is CCTP?

### Concept

CCTP (Cross-Chain Transfer Protocol) is Circle's solution for native USDC transfers between blockchains.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    CCTP Transfer Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Source Chain (e.g., Arc)          Destination (e.g., ETH)  │
│                                                              │
│  ┌──────────────────┐                                       │
│  │ 1. depositForBurn │                                      │
│  │    (Burn USDC)    │                                      │
│  └────────┬──────────┘                                      │
│           │                                                  │
│           │ Emit MessageSent                                │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │ Circle Attestor  │                                       │
│  │ (Off-chain)      │                                       │
│  └────────┬──────────┘                                      │
│           │                                                  │
│           │ Sign attestation                                │
│           │                                                  │
│           ▼                                                  │
│                         ┌──────────────────┐                │
│                         │ 2. receiveMessage│                │
│                         │  (Mint USDC)     │                │
│                         └──────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **TokenMessenger** - Handles burn/mint operations
2. **MessageTransmitter** - Handles message passing and verification
3. **Attestation Service** - Circle's off-chain service that signs messages

---

## Architecture

### Contract Structure

```
CrossChainPayrollVault
├── Inherits: AccessControl, Pausable
├── Dependencies: IERC20, ITokenMessenger
└── Features:
    ├── Same-chain payouts (original functionality)
    ├── Cross-chain payouts (CCTP integration)
    ├── Transfer tracking and reconciliation
    └── Role-based access control
```

### Key Functions

#### 1. Same-Chain Payout

```solidity
function batchPayout(
    address[] calldata recipients,
    uint256[] calldata amounts,
    bytes32 batchId
) external whenNotPaused onlyRole(APPROVER_ROLE)
```

**Use case:** Pay employees on the same blockchain as the vault

#### 2. Cross-Chain Payout

```solidity
function crossChainBatchPayout(
    address[] calldata recipients,
    uint256[] calldata amounts,
    bytes32 batchId,
    uint32 destinationDomain,
    string calldata destinationChainName
) external whenNotPaused onlyRole(APPROVER_ROLE)
```

**Use case:** Pay employees on a different blockchain via CCTP

#### 3. Mark Completion

```solidity
function markCrossChainTransferCompleted(
    uint64 nonce
) external onlyRole(OPERATOR_ROLE)
```

**Use case:** Update source chain records after destination mint succeeds

---

## Smart Contract Integration

### Step 1: Interface Definitions

The `ICCTP.sol` file defines the interfaces needed to interact with CCTP:

```solidity
interface ITokenMessenger {
    function depositForBurn(
        uint256 amount,
        uint32 destinationDomain,
        bytes32 mintRecipient,
        address burnToken
    ) external returns (uint64 nonce);
}
```

### Step 2: Contract Implementation

Key implementation details in `CrossChainPayrollVault.sol`:

```solidity
// Store TokenMessenger reference
ITokenMessenger public immutable tokenMessenger;

// Track cross-chain transfers
mapping(uint64 => CrossChainTransfer) public crossChainTransfers;

// Initiate cross-chain transfer
function crossChainBatchPayout(...) external {
    // 1. Approve USDC spending
    IERC20(USDC).approve(address(tokenMessenger), totalAmount);
    
    // 2. Call depositForBurn for each recipient
    for (uint256 i = 0; i < recipients.length; i++) {
        bytes32 mintRecipient = bytes32(uint256(uint160(recipients[i])));
        
        uint64 nonce = tokenMessenger.depositForBurn(
            amounts[i],
            destinationDomain,
            mintRecipient,
            USDC
        );
        
        // 3. Record transfer details
        crossChainTransfers[nonce] = CrossChainTransfer({...});
        
        // 4. Emit event
        emit CrossChainPayoutInitiated(...);
    }
}
```

### Step 3: Domain IDs

CCTP uses domain IDs to identify chains:

```solidity
uint32 constant ETHEREUM_DOMAIN = 0;
uint32 constant AVALANCHE_DOMAIN = 1;
uint32 constant OPTIMISM_DOMAIN = 2;
uint32 constant ARBITRUM_DOMAIN = 3;
uint32 constant BASE_DOMAIN = 6;
uint32 constant POLYGON_DOMAIN = 7;
```

---

## Testing Guide

### Running Tests

```bash
# Install dependencies
cd contracts
npm install

# Compile contracts
npx hardhat compile

# Run all tests
npx hardhat test

# Run only cross-chain tests
npx hardhat test test/CrossChainPayrollVault.test.ts

# Run with gas reporting
REPORT_GAS=true npx hardhat test

# Run with coverage
npx hardhat coverage
```

### Test Suite Coverage

The comprehensive test suite includes:

**1. Deployment & Initialization (11 tests)**
- Contract deployment validation
- Role assignment verification
- Initial state checks
- Invalid parameter rejection

**2. Same-Chain Batch Payout (10 tests)**
- Successful payout execution
- Event emission verification
- Duplicate prevention
- Access control
- Edge cases

**3. Cross-Chain Batch Payout (14 tests)**
- CCTP integration
- Multiple destination chains
- TokenMessenger interaction
- Transfer tracking
- Error handling

**4. Cross-Chain Completion (5 tests)**
- Transfer marking
- Duplicate prevention
- Access control

**5. Hybrid Payouts (2 tests)**
- Mixed same-chain and cross-chain
- Sequential batches

**6. Admin Functions (7 tests)**
- Pause/unpause
- Role management
- Monthly cap setting

**7. View Functions (3 tests)**
- Balance queries
- Transfer details
- Batch status

**8. Gas Optimization (2 tests)**
- Gas usage measurement
- Efficiency verification

**9. Integration Scenarios (2 tests)**
- Complete payroll cycle
- Error recovery

**Total: 56 comprehensive test cases**

### Example Test Run

```bash
$ npx hardhat test test/CrossChainPayrollVault.test.ts

  CrossChainPayrollVault
    1. Deployment & Initialization
      ✓ Should set correct USDC address
      ✓ Should set correct TokenMessenger address
      ✓ Should grant DEFAULT_ADMIN_ROLE to owner
      ...
    
    3. Cross-Chain Batch Payout (CCTP)
      ✓ Should initiate cross-chain payout to Ethereum
      ✓ Should emit CrossChainPayoutInitiated with correct parameters
      ✓ Should approve TokenMessenger to spend USDC
      ✓ Should call TokenMessenger.depositForBurn
      ...
    
  56 passing (3.2s)
```

---

## Deployment Guide

### Prerequisites

1. **Environment Setup**

Create `.env` file:

```ini
# Network Configuration
ARC_RPC_URL=https://rpc.testnet.arc.network
ARC_CHAIN_ID=462037205

# Wallet Configuration
PRIVATE_KEY=0x...
ADMIN_ADDRESS=0x...

# Contract Addresses
USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
TOKEN_MESSENGER_ADDRESS=0x...  # Get from CCTP docs

# Optional
OPERATOR_ADDRESS=0x...  # If different from admin
```

2. **Fund Wallet**

Get testnet USDC from [Circle Faucet](https://faucet.circle.com)

### Deployment Steps

```bash
# 1. Compile contracts
npx hardhat compile

# 2. Run deployment script
npx hardhat run scripts/deploy-crosschain-vault.ts --network arcTestnet

# 3. Verify deployment
npx hardhat verify --network arcTestnet \
  DEPLOYED_ADDRESS \
  USDC_ADDRESS \
  ADMIN_ADDRESS \
  TOKEN_MESSENGER_ADDRESS

# 4. Copy ABI to backend
cp artifacts/contracts/CrossChainPayrollVault.sol/CrossChainPayrollVault.json \
   ../backend/abi/
```

### Post-Deployment

1. **Fund the vault with USDC:**

```bash
# Using Hardhat console
npx hardhat console --network arcTestnet
```

```javascript
const usdc = await ethers.getContractAt("IERC20", USDC_ADDRESS);
await usdc.transfer(VAULT_ADDRESS, ethers.parseUnits("10000", 6));
```

2. **Verify vault balance:**

```javascript
const vault = await ethers.getContractAt("CrossChainPayrollVault", VAULT_ADDRESS);
const balance = await vault.getBalance();
console.log("Vault balance:", ethers.formatUnits(balance, 6), "USDC");
```

3. **Grant roles (if needed):**

```javascript
const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
await vault.grantRole(APPROVER_ROLE, AI_AGENT_ADDRESS);
```

---

## Backend Integration

### Configuration

Update `backend/.env`:

```ini
# Cross-Chain Payroll Configuration
PAYROLL_CONTRACT_ADDRESS=0x...  # Deployed vault address
USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
TOKEN_MESSENGER_ADDRESS=0x...
PAYROLL_CONTRACT_ABI_PATH=/app/abi/CrossChainPayrollVault.json

# CCTP Domain IDs
CCTP_DOMAIN_ETHEREUM=0
CCTP_DOMAIN_AVALANCHE=1
CCTP_DOMAIN_OPTIMISM=2
CCTP_DOMAIN_ARBITRUM=3
CCTP_DOMAIN_BASE=6
CCTP_DOMAIN_POLYGON=7
```

### Python Integration Example

```python
# backend/app/onchain/cctp_service.py

from web3 import Web3
from typing import List, Dict
import json

class CCTPService:
    def __init__(self, w3: Web3, vault_address: str, abi_path: str):
        self.w3 = w3
        with open(abi_path) as f:
            abi = json.load(f)['abi']
        self.vault = w3.eth.contract(address=vault_address, abi=abi)
    
    def cross_chain_payout(
        self,
        recipients: List[str],
        amounts: List[int],
        batch_id: bytes,
        destination_domain: int,
        chain_name: str
    ) -> Dict:
        """
        Execute cross-chain batch payout
        
        Args:
            recipients: List of recipient addresses on destination chain
            amounts: List of amounts in USDC smallest unit (6 decimals)
            batch_id: Unique batch identifier (32 bytes)
            destination_domain: CCTP domain ID (0=Ethereum, 1=Avalanche, etc.)
            chain_name: Human-readable chain name for logging
        
        Returns:
            Dict with transaction hash and nonces
        """
        # Build transaction
        tx = self.vault.functions.crossChainBatchPayout(
            recipients,
            amounts,
            batch_id,
            destination_domain,
            chain_name
        ).build_transaction({
            'from': self.w3.eth.default_account,
            'nonce': self.w3.eth.get_transaction_count(self.w3.eth.default_account),
            'gas': 500000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Parse events to get nonces
        nonces = []
        for log in receipt['logs']:
            try:
                event = self.vault.events.CrossChainPayoutInitiated().process_log(log)
                nonces.append(event['args']['nonce'])
            except:
                pass
        
        return {
            'tx_hash': tx_hash.hex(),
            'nonces': nonces,
            'block_number': receipt['blockNumber']
        }
```

### Attestation Fetching

After initiating a cross-chain transfer, you need to fetch the attestation:

```python
import requests
import time

def fetch_attestation(message_hash: str, max_attempts: int = 60) -> str:
    """
    Fetch CCTP attestation from Circle's API
    
    Args:
        message_hash: Hash of the CCTP message (from event)
        max_attempts: Maximum number of polling attempts
    
    Returns:
        Attestation signature (hex string)
    """
    url = f"https://iris-api.circle.com/attestations/{message_hash}"
    
    for attempt in range(max_attempts):
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'complete':
                return data['attestation']
        
        # Wait before retrying
        time.sleep(5)
    
    raise TimeoutError("Attestation not available after maximum attempts")
```

### Completing Transfer on Destination Chain

```python
def complete_transfer_on_destination(
    message: bytes,
    attestation: str,
    destination_chain_rpc: str
):
    """
    Complete CCTP transfer on destination chain
    
    Args:
        message: CCTP message from source chain
        attestation: Attestation from Circle
        destination_chain_rpc: RPC URL of destination chain
    """
    # Connect to destination chain
    dest_w3 = Web3(Web3.HTTPProvider(destination_chain_rpc))
    
    # Get MessageTransmitter contract
    transmitter = dest_w3.eth.contract(
        address=MESSAGE_TRANSMITTER_ADDRESS,
        abi=MESSAGE_TRANSMITTER_ABI
    )
    
    # Call receiveMessage
    tx = transmitter.functions.receiveMessage(
        message,
        bytes.fromhex(attestation)
    ).build_transaction({...})
    
    # Sign and send
    signed_tx = dest_w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = dest_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    # Wait for confirmation
    receipt = dest_w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return receipt
```

---

## Troubleshooting

### Common Issues

#### 1. "Insufficient USDC balance"

**Problem:** Vault doesn't have enough USDC for the payout

**Solution:**
```bash
# Check vault balance
cast call $VAULT_ADDRESS "getBalance()(uint256)" --rpc-url $RPC_URL

# Fund vault
cast send $USDC_ADDRESS "transfer(address,uint256)" \
  $VAULT_ADDRESS 10000000000 \
  --rpc-url $RPC_URL \
  --private-key $PRIVATE_KEY
```

#### 2. "Approval failed"

**Problem:** Vault cannot approve TokenMessenger to spend USDC

**Solution:** Check USDC contract is correct and vault has USDC

#### 3. "Transfer not found"

**Problem:** Trying to mark a non-existent nonce as completed

**Solution:** Verify the nonce from the CrossChainPayoutInitiated event

#### 4. "Attestation not available"

**Problem:** Circle's attestation service hasn't signed the message yet

**Solution:** Wait longer (up to 20 minutes) and retry fetching attestation

#### 5. "Message already received"

**Problem:** Trying to call receiveMessage twice with the same message

**Solution:** Check if the transfer already completed on destination chain

### Debugging Tips

1. **Monitor events:**

```bash
# Watch for CrossChainPayoutInitiated events
cast logs --address $VAULT_ADDRESS \
  --sig "CrossChainPayoutInitiated(bytes32,uint64,address,uint256,uint32,string,bytes32)" \
  --from-block latest \
  --rpc-url $RPC_URL
```

2. **Check transfer status:**

```javascript
const transfer = await vault.getCrossChainTransfer(nonce);
console.log({
  batchId: transfer.batchId,
  recipient: transfer.recipient,
  amount: ethers.formatUnits(transfer.amount, 6),
  domain: transfer.destinationDomain,
  completed: transfer.completed,
  timestamp: new Date(transfer.timestamp * 1000)
});
```

3. **Verify on destination chain:**

```bash
# Check recipient balance on destination
cast call $USDC_ADDRESS "balanceOf(address)(uint256)" \
  $RECIPIENT_ADDRESS \
  --rpc-url $DEST_RPC_URL
```

---

## Security Considerations

### Smart Contract Security

1. **Role-Based Access Control**
   - APPROVER_ROLE: Can execute payouts
   - OPERATOR_ROLE: Can mark completions
   - DEFAULT_ADMIN_ROLE: Can manage roles and pause

2. **Replay Protection**
   - Batch IDs can only be used once
   - Prevents duplicate payouts

3. **Pausable**
   - Emergency stop mechanism
   - Admin can pause all operations

4. **Immutable References**
   - USDC and TokenMessenger addresses cannot be changed
   - Prevents malicious contract swaps

### Operational Security

1. **Private Key Management**
   - Never commit private keys to git
   - Use hardware wallets for mainnet
   - Separate keys for different roles

2. **Attestation Verification**
   - Always verify attestations come from Circle
   - Check message hashes match

3. **Monitoring**
   - Set up alerts for large transfers
   - Monitor vault balance
   - Track failed transfers

4. **Testing**
   - Always test on testnet first
   - Verify with small amounts initially
   - Test error cases

### Best Practices

```solidity
// ✅ Good: Check destination domain is valid
require(destinationDomain <= 7, "Invalid domain");

// ✅ Good: Verify minimum amount
require(amount >= 1000000, "Amount too small"); // 1 USDC minimum

// ✅ Good: Emit detailed events
emit CrossChainPayoutInitiated(
    batchId,
    nonce,
    recipient,
    amount,
    destinationDomain,
    chainName,
    messageHash
);
```

---

## Reference

### Official Documentation

- **CCTP Docs:** https://developers.circle.com/stablecoins/docs/cctp-protocol-contract
- **CCTP Testnet:** https://developers.circle.com/stablecoins/docs/cctp-getting-started
- **Attestation API:** https://developers.circle.com/stablecoins/docs/cctp-attestation-service

### Contract Addresses

**TokenMessenger (Testnet):**
- Ethereum Sepolia: `0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5`
- Avalanche Fuji: `0xa9fb1b3009dcb79e2fe346c16a604b8fa8ae0a79`
- Optimism Sepolia: `0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5`
- Arbitrum Sepolia: `0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5`
- Base Sepolia: `0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5`

**USDC (Arc Testnet):**
- `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238`

### Domain IDs

| Chain | Domain ID | Network |
|-------|-----------|---------|
| Ethereum | 0 | Mainnet / Sepolia |
| Avalanche | 1 | C-Chain / Fuji |
| Optimism | 2 | Mainnet / Sepolia |
| Arbitrum | 3 | One / Sepolia |
| Base | 6 | Mainnet / Sepolia |
| Polygon | 7 | PoS / Mumbai |

### Useful Commands

```bash
# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test

# Deploy
npx hardhat run scripts/deploy-crosschain-vault.ts --network arcTestnet

# Verify contract
npx hardhat verify --network arcTestnet VAULT_ADDRESS USDC_ADDRESS ADMIN_ADDRESS TOKEN_MESSENGER_ADDRESS

# Check balance
cast call VAULT_ADDRESS "getBalance()(uint256)" --rpc-url RPC_URL

# Check transfer
cast call VAULT_ADDRESS "getCrossChainTransfer(uint64)(tuple)" NONCE --rpc-url RPC_URL
```

---

## Support

For questions or issues:

1. Check the [CCTP Documentation](https://developers.circle.com/stablecoins/docs/cctp-protocol-contract)
2. Review test cases in `test/CrossChainPayrollVault.test.ts`
3. Check deployment logs in `deployment-crosschain-*.json`
4. Contact Circle support for CCTP-specific issues

---

**Last Updated:** November 2024  
**Version:** 1.0.0  
**License:** MIT

