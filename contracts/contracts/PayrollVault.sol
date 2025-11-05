// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title IERC20
 * @dev ERC20 token interface for interacting with USDC
 */
interface IERC20 {
    function decimals() external view returns (uint8);
    function transfer(address to, uint256 amount) external returns (bool);
}

/**
 * @title PayrollVault
 * @dev Smart contract for batch payroll distribution
 * 
 * Features:
 * - Supports batch USDC payroll distribution
 * - Role-based access control (APPROVER_ROLE for approvals, OPERATOR_ROLE for operations)
 * - Pausable functionality
 * - Replay attack protection (each batchId can only be processed once)
 * - Comprehensive event logging
 * 
 * Roles:
 * - DEFAULT_ADMIN_ROLE: Super admin, can set caps, pause contract, grant roles
 * - APPROVER_ROLE: Approver, can execute batch payouts
 * - OPERATOR_ROLE: Operator, reserved for future extensions
 */
contract PayrollVault is AccessControl, Pausable {
    // ============ Role Definitions ============
    // APPROVER_ROLE: Payroll approver role, allows executing batchPayout
    bytes32 public constant APPROVER_ROLE = keccak256("APPROVER_ROLE");
    
    // OPERATOR_ROLE: Operator role, reserved for future feature extensions
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // ============ State Variables ============
    // USDC token contract address (immutable)
    address public immutable USDC;
    
    // Monthly payout cap (adjustable by admin)
    uint256 public monthlyCap;
    
    // Record of processed batch IDs to prevent duplicate payouts
    mapping(bytes32 => bool) public processedBatch;

    // ============ Event Definitions ============
    /**
     * @dev Batch approval event
     * @param batchId Unique batch identifier
     * @param approver Approver address
     * @param totalAmount Total batch amount
     * @param count Number of payouts
     */
    event BatchApproved(
        bytes32 indexed batchId,
        address indexed approver,
        uint256 totalAmount,
        uint256 count
    );

    /**
     * @dev Batch execution completed event
     * @param batchId Unique batch identifier
     * @param from Executor address
     * @param successCount Number of successful payouts
     * @param failCount Number of failed payouts
     */
    event PayoutExecuted(
        bytes32 indexed batchId,
        address indexed from,
        uint256 successCount,
        uint256 failCount
    );

    /**
     * @dev Individual payout event
     * @param batchId Unique batch identifier
     * @param index Index in batch
     * @param to Recipient address
     * @param amount Payout amount
     * @param success Whether successful
     * @param data Return data
     */
    event PayoutLine(
        bytes32 indexed batchId,
        uint256 index,
        address to,
        uint256 amount,
        bool success,
        bytes data
    );

    // ============ Constructor ============
    /**
     * @dev Initialize contract
     * @param usdc USDC token contract address
     * @param admin Admin address (will receive all roles)
     */
    constructor(address usdc, address admin) {
        USDC = usdc;
        
        // Grant admin all roles
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(APPROVER_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
    }

    // ============ Admin Functions ============
    /**
     * @dev Set monthly payout cap
     * @param cap New cap amount
     * 
     * Only callable by DEFAULT_ADMIN_ROLE
     */
    function setMonthlyCap(uint256 cap) external onlyRole(DEFAULT_ADMIN_ROLE) {
        monthlyCap = cap;
    }

    /**
     * @dev Pause contract (for emergency use)
     * 
     * Only callable by DEFAULT_ADMIN_ROLE
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    /**
     * @dev Resume contract operations
     * 
     * Only callable by DEFAULT_ADMIN_ROLE
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // ============ Core Functions ============
    /**
     * @dev Batch payroll distribution
     * @param recipients Array of recipient addresses
     * @param amounts Corresponding amount array (unit: USDC smallest unit, e.g. 6 decimals)
     * @param batchId Unique batch identifier (prevents duplicate payouts)
     * @param meta Batch metadata (e.g.: "2025-11 payroll")
     * 
     * Requirements:
     * - Contract not paused
     * - Caller has APPROVER_ROLE
     * - batchId not processed before
     * - recipients and amounts same length and not empty
     * 
     * Flow:
     * 1. Validate parameters and mark batchId as processed
     * 2. Emit BatchApproved event
     * 3. Execute transfers one by one
     * 4. Emit PayoutLine event for each transfer
     * 5. Emit PayoutExecuted event summary
     */
    function batchPayout(
        address[] calldata recipients,
        uint256[] calldata amounts,
        bytes32 batchId,
        string calldata meta
    ) external whenNotPaused onlyRole(APPROVER_ROLE) {
        // Verify batch not processed before
        require(!processedBatch[batchId], "BATCH_DONE");
        
        // Verify array lengths
        require(
            recipients.length == amounts.length && recipients.length > 0,
            "BAD_LEN"
        );
        
        // Mark batch as processed (replay protection)
        processedBatch[batchId] = true;

        // Emit batch approval event
        emit BatchApproved(batchId, msg.sender, _sum(amounts), recipients.length);

        // Counters
        uint256 successCount;
        uint256 failCount;
        
        // Execute transfers one by one
        for (uint256 i = 0; i < recipients.length; i++) {
            // Use low-level call for transfer (more flexible error handling)
            (bool ok, bytes memory ret) = USDC.call(
                abi.encodeWithSignature(
                    "transfer(address,uint256)",
                    recipients[i],
                    amounts[i]
                )
            );
            
            // Determine if transfer successful
            // Some tokens don't return bool, so need to check ret.length
            bool lineSuccess = ok && (ret.length == 0 || abi.decode(ret, (bool)) == true);
            
            if (lineSuccess) {
                successCount++;
            } else {
                failCount++;
            }
            
            // Emit individual payout event
            emit PayoutLine(batchId, i, recipients[i], amounts[i], lineSuccess, ret);
        }

        // Emit batch execution completed event
        emit PayoutExecuted(batchId, msg.sender, successCount, failCount);
    }

    // ============ Internal Functions ============
    /**
     * @dev Calculate array sum
     * @param a Amount array
     * @return s Sum
     */
    function _sum(uint256[] memory a) internal pure returns (uint256 s) {
        for (uint256 i = 0; i < a.length; i++) {
            s += a[i];
        }
    }
}
