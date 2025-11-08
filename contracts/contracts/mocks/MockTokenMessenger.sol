// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title MockTokenMessenger
 * @notice Mock implementation of Circle's CCTP TokenMessenger for testing
 * 
 * This contract simulates the behavior of the real CCTP TokenMessenger without
 * actually performing cross-chain operations. It's designed for unit testing
 * the CrossChainPayrollVault contract.
 * 
 * What it simulates:
 * - depositForBurn() - Burns (transfers to this contract) USDC and returns a nonce
 * - depositForBurnWithCaller() - Same as above with caller restriction
 * - MessageSent event emission
 * 
 * What it doesn't do:
 * - Actual cross-chain communication
 * - Circle attestation service interaction
 * - Real USDC burning (just transfers to this contract)
 * 
 * Usage in tests:
 * ```
 * MockTokenMessenger messenger = new MockTokenMessenger();
 * CrossChainPayrollVault vault = new CrossChainPayrollVault(
 *     usdcAddress,
 *     admin,
 *     address(messenger)
 * );
 * ```
 */
contract MockTokenMessenger {
    
    // ============================================
    // State Variables
    // ============================================
    
    /// @notice Counter for generating unique nonces
    uint64 private _nonce;
    
    /// @notice Total amount of USDC "burned" (transferred to this contract)
    uint256 public totalBurned;
    
    /// @notice Mapping of nonce to burn details
    mapping(uint64 => BurnDetails) public burns;
    
    // ============================================
    // Structs
    // ============================================
    
    /**
     * @notice Details of a burn transaction
     * @param burnToken Address of token that was burned
     * @param amount Amount burned
     * @param depositor Address that initiated the burn
     * @param mintRecipient Recipient on destination chain
     * @param destinationDomain Destination domain ID
     * @param timestamp When the burn occurred
     */
    struct BurnDetails {
        address burnToken;
        uint256 amount;
        address depositor;
        bytes32 mintRecipient;
        uint32 destinationDomain;
        uint256 timestamp;
    }
    
    // ============================================
    // Events
    // ============================================
    
    /**
     * @notice Emitted when tokens are burned for cross-chain transfer
     * @param nonce Unique identifier for the burn
     * @param burnToken Token that was burned
     * @param amount Amount burned
     * @param depositor Address that initiated the burn
     * @param mintRecipient Recipient address on destination chain (bytes32)
     * @param destinationDomain Destination chain domain ID
     * @param destinationTokenMessenger TokenMessenger address on destination (unused in mock)
     * @param destinationCaller Authorized caller on destination (bytes32(0) = anyone)
     */
    event DepositForBurn(
        uint64 indexed nonce,
        address indexed burnToken,
        uint256 amount,
        address indexed depositor,
        bytes32 mintRecipient,
        uint32 destinationDomain,
        bytes32 destinationTokenMessenger,
        bytes32 destinationCaller
    );
    
    /**
     * @notice Emitted when a message is sent (for compatibility with CCTP)
     * @param message The message bytes (contains burn details)
     */
    event MessageSent(bytes message);
    
    // ============================================
    // Mock Functions
    // ============================================
    
    /**
     * @notice Simulates CCTP depositForBurn
     * @param amount Amount to burn
     * @param destinationDomain Destination chain domain ID
     * @param mintRecipient Recipient on destination chain (bytes32)
     * @param burnToken Token to burn (USDC)
     * @return nonce Unique identifier for this burn
     * 
     * Behavior:
     * 1. Increments nonce counter
     * 2. Transfers tokens from caller to this contract (simulates burn)
     * 3. Records burn details
     * 4. Emits DepositForBurn event
     * 5. Emits MessageSent event (for compatibility)
     * 
     * Requirements:
     * - Caller must have approved this contract to spend `amount` of `burnToken`
     * - Amount must be greater than 0
     */
    function depositForBurn(
        uint256 amount,
        uint32 destinationDomain,
        bytes32 mintRecipient,
        address burnToken
    ) external returns (uint64 nonce) {
        require(amount > 0, "Amount must be greater than 0");
        
        // Increment nonce
        _nonce++;
        nonce = _nonce;
        
        // Simulate burning by transferring to this contract
        require(
            IERC20(burnToken).transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );
        
        // Record burn details
        burns[nonce] = BurnDetails({
            burnToken: burnToken,
            amount: amount,
            depositor: msg.sender,
            mintRecipient: mintRecipient,
            destinationDomain: destinationDomain,
            timestamp: block.timestamp
        });
        
        totalBurned += amount;
        
        // Emit events
        emit DepositForBurn(
            nonce,
            burnToken,
            amount,
            msg.sender,
            mintRecipient,
            destinationDomain,
            bytes32(0), // Mock: no destination messenger
            bytes32(0)  // Anyone can call
        );
        
        // Emit message sent (with mock message)
        bytes memory message = abi.encode(
            nonce,
            burnToken,
            amount,
            msg.sender,
            mintRecipient,
            destinationDomain
        );
        
        emit MessageSent(message);
        
        return nonce;
    }
    
    /**
     * @notice Simulates CCTP depositForBurnWithCaller
     * @param amount Amount to burn
     * @param destinationDomain Destination chain domain ID
     * @param mintRecipient Recipient on destination chain
     * @param burnToken Token to burn (USDC)
     * @param destinationCaller Authorized caller on destination chain
     * @return nonce Unique identifier for this burn
     * 
     * In the mock, this behaves identically to depositForBurn, but in the real
     * CCTP contract, destinationCaller restricts who can call receiveMessage.
     */
    function depositForBurnWithCaller(
        uint256 amount,
        uint32 destinationDomain,
        bytes32 mintRecipient,
        address burnToken,
        bytes32 destinationCaller
    ) external returns (uint64 nonce) {
        require(amount > 0, "Amount must be greater than 0");
        
        _nonce++;
        nonce = _nonce;
        
        require(
            IERC20(burnToken).transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );
        
        burns[nonce] = BurnDetails({
            burnToken: burnToken,
            amount: amount,
            depositor: msg.sender,
            mintRecipient: mintRecipient,
            destinationDomain: destinationDomain,
            timestamp: block.timestamp
        });
        
        totalBurned += amount;
        
        emit DepositForBurn(
            nonce,
            burnToken,
            amount,
            msg.sender,
            mintRecipient,
            destinationDomain,
            bytes32(0),
            destinationCaller
        );
        
        bytes memory message = abi.encode(
            nonce,
            burnToken,
            amount,
            msg.sender,
            mintRecipient,
            destinationDomain,
            destinationCaller
        );
        
        emit MessageSent(message);
        
        return nonce;
    }
    
    // ============================================
    // Helper Functions (for testing)
    // ============================================
    
    /**
     * @notice Gets the current nonce value
     * @return Current nonce
     */
    function getCurrentNonce() external view returns (uint64) {
        return _nonce;
    }
    
    /**
     * @notice Gets burn details for a specific nonce
     * @param nonce The burn nonce to query
     * @return Burn details struct
     */
    function getBurnDetails(uint64 nonce) external view returns (BurnDetails memory) {
        return burns[nonce];
    }
    
    /**
     * @notice Gets the balance of a specific token held by this contract
     * @param token Token address to check
     * @return Balance
     */
    function getTokenBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }
    
    /**
     * @notice Allows withdrawing "burned" tokens (for test cleanup)
     * @param token Token to withdraw
     * @param to Recipient address
     * @param amount Amount to withdraw
     * 
     * Note: In a real CCTP contract, burned tokens are permanently destroyed.
     * This function only exists in the mock for test convenience.
     */
    function withdrawBurnedTokens(
        address token,
        address to,
        uint256 amount
    ) external {
        require(IERC20(token).transfer(to, amount), "Withdrawal failed");
    }
}

