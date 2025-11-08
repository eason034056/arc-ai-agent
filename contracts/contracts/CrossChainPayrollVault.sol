// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./interfaces/ICCTP.sol";

/**
 * @title CrossChainPayrollVault
 * @notice Enhanced PayrollVault with CCTP cross-chain transfer capabilities
 * 
 * Features:
 * - Batch payroll distribution on same chain (original functionality)
 * - Cross-chain batch payroll using Circle's CCTP (new functionality)
 * - Role-based access control (APPROVER_ROLE, OPERATOR_ROLE)
 * - Pausable for emergency situations
 * - Replay attack protection (batchId tracking)
 * - Cross-chain transfer tracking and reconciliation
 * 
 * Architecture:
 * ┌─────────────────────────────────────────────────────────────┐
 * │                 CrossChainPayrollVault                       │
 * ├─────────────────────────────────────────────────────────────┤
 * │                                                              │
 * │  Same-Chain Payout          Cross-Chain Payout              │
 * │  ┌──────────────┐           ┌──────────────────┐           │
 * │  │ batchPayout  │           │ crossChainBatch  │           │
 * │  │    (USDC)    │           │     Payout       │           │
 * │  └──────┬───────┘           └────────┬─────────┘           │
 * │         │                            │                      │
 * │         │ Direct Transfer            │ CCTP Bridge          │
 * │         │                            │                      │
 * │         ▼                            ▼                      │
 * │  ┌──────────────┐           ┌──────────────────┐           │
 * │  │  Employees   │           │  TokenMessenger  │           │
 * │  │  (Same Chain)│           │  (Burn USDC)     │           │
 * │  └──────────────┘           └────────┬─────────┘           │
 * │                                      │                      │
 * │                             Circle Attestation              │
 * │                                      │                      │
 * │                             ┌────────▼─────────┐           │
 * │                             │  Employees       │           │
 * │                             │  (Dest Chain)    │           │
 * │                             └──────────────────┘           │
 * └─────────────────────────────────────────────────────────────┘
 * 
 * Roles:
 * - DEFAULT_ADMIN_ROLE: Can manage all roles, pause contract, set caps
 * - APPROVER_ROLE: Can execute batch payouts (both same-chain and cross-chain)
 * - OPERATOR_ROLE: Can mark cross-chain transfers as completed
 */
contract CrossChainPayrollVault is AccessControl, Pausable {
    
    // ============================================
    // Role Definitions
    // ============================================
    
    /// @notice Role for approving and executing payroll batches
    bytes32 public constant APPROVER_ROLE = keccak256("APPROVER_ROLE");
    
    /// @notice Role for operating cross-chain transfer lifecycle (marking completion)
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    
    // ============================================
    // State Variables
    // ============================================
    
    /// @notice USDC token contract address (immutable after deployment)
    address public immutable USDC;
    
    /// @notice CCTP TokenMessenger contract for cross-chain transfers
    ITokenMessenger public immutable tokenMessenger;
    
    /// @notice Monthly payout cap (in USDC smallest unit, adjustable by admin)
    uint256 public monthlyCap;
    
    /// @notice Mapping to track processed batch IDs (prevents replay attacks)
    mapping(bytes32 => bool) public processedBatch;
    
    /// @notice Mapping to track cross-chain transfers by CCTP nonce
    mapping(uint64 => CrossChainTransfer) public crossChainTransfers;
    
    /// @notice Total number of cross-chain transfers initiated
    uint256 public totalCrossChainTransfers;
    
    // ============================================
    // Structs
    // ============================================
    
    /**
     * @notice Structure to track cross-chain transfer details
     * @param batchId Associated payroll batch ID
     * @param recipient Recipient address on destination chain
     * @param amount Transfer amount in USDC smallest unit
     * @param destinationDomain CCTP destination domain ID
     * @param timestamp When the transfer was initiated
     * @param completed Whether the transfer has been completed on destination chain
     * @param messageHash Hash of CCTP message (for attestation lookup)
     */
    struct CrossChainTransfer {
        bytes32 batchId;
        address recipient;
        uint256 amount;
        uint32 destinationDomain;
        uint256 timestamp;
        bool completed;
        bytes32 messageHash;
    }
    
    // ============================================
    // Events
    // ============================================
    
    /**
     * @notice Emitted when a batch is approved (both same-chain and cross-chain)
     * @param batchId Unique batch identifier
     * @param approver Address that approved the batch
     * @param totalAmount Total amount in the batch
     * @param count Number of recipients in the batch
     */
    event BatchApproved(
        bytes32 indexed batchId,
        address indexed approver,
        uint256 totalAmount,
        uint256 count
    );
    
    /**
     * @notice Emitted when same-chain payout execution completes
     * @param batchId Unique batch identifier
     * @param from Executor address
     * @param successCount Number of successful transfers
     * @param failCount Number of failed transfers
     */
    event PayoutExecuted(
        bytes32 indexed batchId,
        address indexed from,
        uint256 successCount,
        uint256 failCount
    );
    
    /**
     * @notice Emitted for each individual payout in a batch
     * @param batchId Unique batch identifier
     * @param index Index in the batch
     * @param to Recipient address
     * @param amount Transfer amount
     * @param success Whether the transfer succeeded
     * @param data Return data from the transfer call
     */
    event PayoutLine(
        bytes32 indexed batchId,
        uint256 index,
        address to,
        uint256 amount,
        bool success,
        bytes data
    );
    
    /**
     * @notice Emitted when a cross-chain payout is initiated
     * @param batchId Associated payroll batch ID
     * @param nonce CCTP message nonce (unique identifier)
     * @param recipient Recipient address on destination chain
     * @param amount Transfer amount
     * @param destinationDomain CCTP domain ID of destination chain
     * @param destinationChainName Human-readable destination chain name
     * @param messageHash Hash of CCTP message (for attestation lookup)
     */
    event CrossChainPayoutInitiated(
        bytes32 indexed batchId,
        uint64 indexed nonce,
        address indexed recipient,
        uint256 amount,
        uint32 destinationDomain,
        string destinationChainName,
        bytes32 messageHash
    );
    
    /**
     * @notice Emitted when a cross-chain payout is marked as completed
     * @param nonce CCTP message nonce
     * @param batchId Associated payroll batch ID
     * @param recipient Recipient address
     * @param markedBy Address that marked it as completed
     */
    event CrossChainPayoutCompleted(
        uint64 indexed nonce,
        bytes32 indexed batchId,
        address recipient,
        address markedBy
    );
    
    /**
     * @notice Emitted when monthly cap is updated
     * @param oldCap Previous cap value
     * @param newCap New cap value
     * @param updatedBy Address that updated the cap
     */
    event MonthlyCapUpdated(
        uint256 oldCap,
        uint256 newCap,
        address indexed updatedBy
    );
    
    // ============================================
    // Constructor
    // ============================================
    
    /**
     * @notice Initializes the CrossChainPayrollVault contract
     * @param usdc Address of USDC token contract
     * @param admin Address to be granted admin roles
     * @param _tokenMessenger Address of CCTP TokenMessenger contract
     * 
     * TokenMessenger addresses (examples):
     * - Ethereum Mainnet: 0xbd3fa81b58ba92a82136038b25adec7066af3155
     * - Avalanche: 0x6b25532e1060ce10cc3b0a99e5683b91bfde6982
     * - Arc Testnet: (check official documentation)
     * 
     * Requirements:
     * - All addresses must be non-zero
     * - TokenMessenger must be a valid CCTP contract
     */
    constructor(
        address usdc,
        address admin,
        address _tokenMessenger
    ) {
        require(usdc != address(0), "Invalid USDC address");
        require(admin != address(0), "Invalid admin address");
        require(_tokenMessenger != address(0), "Invalid TokenMessenger address");
        
        USDC = usdc;
        tokenMessenger = ITokenMessenger(_tokenMessenger);
        
        // Grant all roles to admin
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(APPROVER_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
    }
    
    // ============================================
    // Admin Functions
    // ============================================
    
    /**
     * @notice Sets the monthly payout cap
     * @param cap New cap amount in USDC smallest unit
     * 
     * Only callable by DEFAULT_ADMIN_ROLE
     * 
     * Example:
     * setMonthlyCap(100000000000) // Set cap to 100,000 USDC
     */
    function setMonthlyCap(uint256 cap) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 oldCap = monthlyCap;
        monthlyCap = cap;
        emit MonthlyCapUpdated(oldCap, cap, msg.sender);
    }
    
    /**
     * @notice Pauses all payout operations (emergency use)
     * 
     * Only callable by DEFAULT_ADMIN_ROLE
     * 
     * When paused:
     * - batchPayout() will revert
     * - crossChainBatchPayout() will revert
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }
    
    /**
     * @notice Resumes payout operations
     * 
     * Only callable by DEFAULT_ADMIN_ROLE
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
    
    // ============================================
    // Same-Chain Payout Functions
    // ============================================
    
    /**
     * @notice Executes batch payroll distribution on the same chain
     * @param recipients Array of recipient addresses
     * @param amounts Array of amounts (in USDC smallest unit, 6 decimals)
     * @param batchId Unique batch identifier (prevents replay)
     * 
     * Requirements:
     * - Contract must not be paused
     * - Caller must have APPROVER_ROLE
     * - batchId must not have been processed before
     * - recipients and amounts arrays must have same length and not be empty
     * - Contract must have sufficient USDC balance
     * 
     * Workflow:
     * 1. Validates parameters and marks batchId as processed
     * 2. Emits BatchApproved event
     * 3. Executes USDC transfers one by one
     * 4. Emits PayoutLine event for each transfer
     * 5. Emits PayoutExecuted event with summary
     * 
     * Example:
     * ```
     * address[] memory recipients = new address[](2);
     * recipients[0] = 0x123...;
     * recipients[1] = 0x456...;
     * 
     * uint256[] memory amounts = new uint256[](2);
     * amounts[0] = 5000000000; // 5000 USDC
     * amounts[1] = 6000000000; // 6000 USDC
     * 
     * bytes32 batchId = keccak256(abi.encodePacked("november_2025"));
     * 
     * vault.batchPayout(recipients, amounts, batchId);
     * ```
     */
    function batchPayout(
        address[] calldata recipients,
        uint256[] calldata amounts,
        bytes32 batchId
    ) external whenNotPaused onlyRole(APPROVER_ROLE) {
        // Validation
        require(!processedBatch[batchId], "BATCH_DONE");
        require(
            recipients.length == amounts.length && recipients.length > 0,
            "BAD_LEN"
        );
        
        // Mark batch as processed
        processedBatch[batchId] = true;
        
        // Calculate total amount
        uint256 totalAmount = _sum(amounts);
        
        // Emit approval event
        emit BatchApproved(batchId, msg.sender, totalAmount, recipients.length);
        
        // Counters
        uint256 successCount;
        uint256 failCount;
        
        // Execute transfers
        for (uint256 i = 0; i < recipients.length; i++) {
            (bool ok, bytes memory ret) = USDC.call(
                abi.encodeWithSignature(
                    "transfer(address,uint256)",
                    recipients[i],
                    amounts[i]
                )
            );
            
            bool lineSuccess = ok && (ret.length == 0 || abi.decode(ret, (bool)) == true);
            
            if (lineSuccess) {
                successCount++;
            } else {
                failCount++;
            }
            
            emit PayoutLine(batchId, i, recipients[i], amounts[i], lineSuccess, ret);
        }
        
        emit PayoutExecuted(batchId, msg.sender, successCount, failCount);
    }
    
    // ============================================
    // Cross-Chain Payout Functions
    // ============================================
    
    /**
     * @notice Executes cross-chain batch payroll distribution using CCTP
     * @param recipients Array of recipient addresses on destination chain
     * @param amounts Array of amounts in USDC smallest unit
     * @param batchId Unique batch identifier
     * @param destinationDomain CCTP destination domain ID
     * @param destinationChainName Human-readable destination chain name (for events)
     * 
     * Requirements:
     * - Contract must not be paused
     * - Caller must have APPROVER_ROLE
     * - batchId must not have been processed before
     * - Arrays must have matching lengths and not be empty
     * - Contract must have sufficient USDC balance
     * 
     * Process:
     * 1. Validates inputs and marks batch as processed
     * 2. Calculates total amount needed
     * 3. Approves TokenMessenger to spend USDC
     * 4. For each recipient:
     *    a. Converts address to bytes32 format
     *    b. Calls tokenMessenger.depositForBurn()
     *    c. Records transfer details with nonce
     *    d. Emits CrossChainPayoutInitiated event
     * 
     * Next steps (off-chain):
     * 1. Monitor MessageSent events from TokenMessenger
     * 2. Fetch attestation from Circle's API
     * 3. Call receiveMessage on destination chain
     * 
     * Domain IDs:
     * - 0: Ethereum
     * - 1: Avalanche
     * - 2: Optimism
     * - 3: Arbitrum
     * - 6: Base
     * - 7: Polygon
     * 
     * Example:
     * ```
     * address[] memory recipients = new address[](1);
     * recipients[0] = 0x789...; // Employee wallet on Ethereum
     * 
     * uint256[] memory amounts = new uint256[](1);
     * amounts[0] = 5000000000; // 5000 USDC
     * 
     * bytes32 batchId = keccak256(abi.encodePacked("cross_chain_nov_2025"));
     * uint32 destinationDomain = 0; // Ethereum
     * string memory chainName = "Ethereum Mainnet";
     * 
     * vault.crossChainBatchPayout(
     *     recipients,
     *     amounts,
     *     batchId,
     *     destinationDomain,
     *     chainName
     * );
     * ```
     */
    function crossChainBatchPayout(
        address[] calldata recipients,
        uint256[] calldata amounts,
        bytes32 batchId,
        uint32 destinationDomain,
        string calldata destinationChainName
    ) external whenNotPaused onlyRole(APPROVER_ROLE) {
        // Validation
        require(!processedBatch[batchId], "BATCH_DONE");
        require(
            recipients.length == amounts.length && recipients.length > 0,
            "BAD_LEN"
        );
        
        // Mark batch as processed
        processedBatch[batchId] = true;
        
        // Calculate total amount
        uint256 totalAmount = _sum(amounts);
        
        // Check balance
        require(
            IERC20(USDC).balanceOf(address(this)) >= totalAmount,
            "Insufficient USDC balance"
        );
        
        // Emit approval event
        emit BatchApproved(batchId, msg.sender, totalAmount, recipients.length);
        
        // Approve TokenMessenger to spend USDC
        require(
            IERC20(USDC).approve(address(tokenMessenger), totalAmount),
            "Approval failed"
        );
        
        // Initiate cross-chain transfers
        for (uint256 i = 0; i < recipients.length; i++) {
            // Convert address to bytes32 (CCTP format)
            bytes32 mintRecipient = bytes32(uint256(uint160(recipients[i])));
            
            // Call CCTP depositForBurn
            uint64 nonce = tokenMessenger.depositForBurn(
                amounts[i],
                destinationDomain,
                mintRecipient,
                USDC
            );
            
            // Calculate message hash (placeholder - actual implementation would compute from message)
            bytes32 messageHash = keccak256(
                abi.encodePacked(nonce, destinationDomain, recipients[i], amounts[i])
            );
            
            // Record transfer
            crossChainTransfers[nonce] = CrossChainTransfer({
                batchId: batchId,
                recipient: recipients[i],
                amount: amounts[i],
                destinationDomain: destinationDomain,
                timestamp: block.timestamp,
                completed: false,
                messageHash: messageHash
            });
            
            totalCrossChainTransfers++;
            
            // Emit event
            emit CrossChainPayoutInitiated(
                batchId,
                nonce,
                recipients[i],
                amounts[i],
                destinationDomain,
                destinationChainName,
                messageHash
            );
        }
    }
    
    /**
     * @notice Marks a cross-chain transfer as completed
     * @param nonce CCTP message nonce
     * 
     * This function should be called by an operator/relayer after successfully
     * calling receiveMessage on the destination chain.
     * 
     * Requirements:
     * - Caller must have OPERATOR_ROLE
     * - Transfer with given nonce must exist
     * - Transfer must not already be marked as completed
     * 
     * Use case:
     * After monitoring destination chain and confirming the receiveMessage
     * transaction succeeded, call this function to update the source chain records.
     */
    function markCrossChainTransferCompleted(
        uint64 nonce
    ) external onlyRole(OPERATOR_ROLE) {
        CrossChainTransfer storage transfer = crossChainTransfers[nonce];
        
        require(transfer.timestamp > 0, "Transfer not found");
        require(!transfer.completed, "Already completed");
        
        transfer.completed = true;
        
        emit CrossChainPayoutCompleted(
            nonce,
            transfer.batchId,
            transfer.recipient,
            msg.sender
        );
    }
    
    // ============================================
    // View Functions
    // ============================================
    
    /**
     * @notice Gets cross-chain transfer details by nonce
     * @param nonce CCTP message nonce
     * @return Transfer details struct
     */
    function getCrossChainTransfer(
        uint64 nonce
    ) external view returns (CrossChainTransfer memory) {
        return crossChainTransfers[nonce];
    }
    
    /**
     * @notice Gets the contract's current USDC balance
     * @return Balance in USDC smallest unit
     */
    function getBalance() external view returns (uint256) {
        return IERC20(USDC).balanceOf(address(this));
    }
    
    /**
     * @notice Checks if a batch ID has been processed
     * @param batchId Batch ID to check
     * @return True if batch has been processed
     */
    function isBatchProcessed(bytes32 batchId) external view returns (bool) {
        return processedBatch[batchId];
    }
    
    // ============================================
    // Internal Functions
    // ============================================
    
    /**
     * @notice Calculates sum of amounts array
     * @param amounts Array of amounts
     * @return s Sum of all amounts
     */
    function _sum(uint256[] memory amounts) internal pure returns (uint256 s) {
        for (uint256 i = 0; i < amounts.length; i++) {
            s += amounts[i];
        }
    }
}

