// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ITokenMessenger
 * @notice Interface for Circle's CCTP TokenMessenger contract
 * 
 * The TokenMessenger is responsible for:
 * - Burning USDC on the source chain
 * - Generating cross-chain transfer messages
 * 
 * Documentation: https://developers.circle.com/stablecoins/docs/cctp-protocol-contract
 */
interface ITokenMessenger {
    /**
     * @notice Deposits and burns tokens from sender to be minted on destination domain
     * @param amount Amount of tokens to burn (in token's smallest unit)
     * @param destinationDomain Destination domain identifier
     * @param mintRecipient Address of mint recipient on destination domain (32-byte format)
     * @param burnToken Address of contract to burn deposited tokens on source domain
     * @return nonce Unique nonce reserved by message
     * 
     * Requirements:
     * - Caller must approve TokenMessenger to spend `amount` of `burnToken`
     * - `burnToken` must be a supported token
     * - `amount` must be greater than 0
     * 
     * Example:
     * ```
     * // Convert address to bytes32
     * bytes32 recipient = bytes32(uint256(uint160(recipientAddress)));
     * 
     * // Approve USDC
     * IERC20(usdc).approve(tokenMessenger, amount);
     * 
     * // Burn and initiate cross-chain transfer
     * uint64 nonce = ITokenMessenger(tokenMessenger).depositForBurn(
     *     5000000000,              // 5000 USDC (6 decimals)
     *     0,                       // Ethereum mainnet
     *     recipient,               // Recipient on Ethereum
     *     usdcAddress              // USDC contract
     * );
     * ```
     */
    function depositForBurn(
        uint256 amount,
        uint32 destinationDomain,
        bytes32 mintRecipient,
        address burnToken
    ) external returns (uint64 nonce);
    
    /**
     * @notice Deposits and burns tokens with a specified caller on destination domain
     * @param amount Amount of tokens to burn
     * @param destinationDomain Destination domain identifier
     * @param mintRecipient Address of mint recipient on destination domain
     * @param burnToken Address of contract to burn deposited tokens
     * @param destinationCaller Authorized caller on destination domain (bytes32(0) = anyone)
     * @return nonce Unique nonce reserved by message
     * 
     * Use case: Restrict who can call receiveMessage on the destination chain
     * - Set to specific address: Only that address can complete the transfer
     * - Set to bytes32(0): Anyone can complete the transfer (gas payment by relayer)
     * 
     * Example:
     * ```
     * bytes32 authorizedCaller = bytes32(uint256(uint160(myRelayerAddress)));
     * 
     * uint64 nonce = ITokenMessenger(tokenMessenger).depositForBurnWithCaller(
     *     amount,
     *     destinationDomain,
     *     mintRecipient,
     *     burnToken,
     *     authorizedCaller  // Only myRelayerAddress can complete transfer
     * );
     * ```
     */
    function depositForBurnWithCaller(
        uint256 amount,
        uint32 destinationDomain,
        bytes32 mintRecipient,
        address burnToken,
        bytes32 destinationCaller
    ) external returns (uint64 nonce);
}

/**
 * @title IMessageTransmitter
 * @notice Interface for Circle's CCTP MessageTransmitter contract
 * 
 * The MessageTransmitter is responsible for:
 * - Receiving and validating cross-chain messages
 * - Minting USDC on the destination chain
 * 
 * Workflow:
 * 1. Monitor source chain for depositForBurn events
 * 2. Wait for Circle's attestation service to sign the message
 * 3. Call receiveMessage on destination chain with message + attestation
 * 4. USDC is minted to the recipient
 */
interface IMessageTransmitter {
    /**
     * @notice Receives an incoming message and processes it
     * @param message Formatted message bytes (from source chain event)
     * @param attestation Attestation bytes signed by Circle
     * @return success True if message was successfully received
     * 
     * Process:
     * 1. Listen for MessageSent event on source chain after depositForBurn
     * 2. Extract message from event
     * 3. Fetch attestation from Circle's API:
     *    GET https://iris-api.circle.com/attestations/{messageHash}
     * 4. Call receiveMessage on destination chain
     * 
     * Example workflow:
     * ```
     * // On source chain (e.g., Arc):
     * uint64 nonce = tokenMessenger.depositForBurn(...);
     * 
     * // Off-chain: Listen for MessageSent event
     * MessageSent(message) = contract.events.MessageSent({nonce})
     * 
     * // Off-chain: Get attestation from Circle
     * messageHash = keccak256(message)
     * attestation = fetch(`https://iris-api.circle.com/attestations/${messageHash}`)
     * 
     * // On destination chain (e.g., Ethereum):
     * IMessageTransmitter(transmitter).receiveMessage(message, attestation);
     * // USDC is now minted to recipient!
     * ```
     */
    function receiveMessage(
        bytes calldata message,
        bytes calldata attestation
    ) external returns (bool success);
    
    /**
     * @notice Returns true if message has already been used
     * @param messageHash Hash of the message
     * @return used True if message has been received
     * 
     * Use case: Check if a cross-chain transfer has been completed
     */
    function usedNonces(bytes32 messageHash) external view returns (bool used);
}

/**
 * @title CCTP Domain IDs
 * @notice Domain identifiers for CCTP supported chains
 * 
 * Official Domain IDs (as of 2024):
 * - 0: Ethereum Mainnet
 * - 1: Avalanche C-Chain
 * - 2: Optimism
 * - 3: Arbitrum One
 * - 6: Base
 * - 7: Polygon PoS
 * 
 * Testnet Domain IDs:
 * - 0: Ethereum Sepolia
 * - 1: Avalanche Fuji
 * - 2: Optimism Sepolia
 * - 3: Arbitrum Sepolia
 * - 6: Base Sepolia
 * - 7: Polygon Mumbai
 * 
 * Note: Arc Testnet domain ID should be confirmed from official documentation
 * 
 * Usage:
 * ```
 * uint32 constant ETHEREUM_DOMAIN = 0;
 * uint32 constant AVALANCHE_DOMAIN = 1;
 * uint32 constant OPTIMISM_DOMAIN = 2;
 * uint32 constant ARBITRUM_DOMAIN = 3;
 * uint32 constant BASE_DOMAIN = 6;
 * uint32 constant POLYGON_DOMAIN = 7;
 * ```
 */
library CCTPDomains {
    uint32 public constant ETHEREUM = 0;
    uint32 public constant AVALANCHE = 1;
    uint32 public constant OPTIMISM = 2;
    uint32 public constant ARBITRUM = 3;
    uint32 public constant BASE = 6;
    uint32 public constant POLYGON = 7;
}

