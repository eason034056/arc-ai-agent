// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title MockUSDC
 * @notice Mock USDC contract for local testing
 * 
 * Description:
 * - This is a simplified ERC20 token contract that simulates real USDC
 * - Inherits from OpenZeppelin's standard ERC20 implementation
 * - Uses 6 decimal places (same as real USDC)
 * - Provides mint functions for testing convenience
 * 
 * Why do we need this contract?
 * - Local testing doesn't require real USDC
 * - Can mint unlimited test tokens without needing a faucet
 * - Complete control over the test environment
 * 
 * Usage:
 *   MockUSDC usdc = new MockUSDC();
 *   usdc.mint(address(this), 1000000 * 10**6);  // Mint 1,000,000 USDC
 */

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockUSDC is ERC20 {
    // ========================================
    // State Variables
    // ========================================
    
    /**
     * _decimals: Decimal places
     * 
     * Literal meaning: Number of decimal places for the token
     * Actual significance: Defines how many smallest units equal 1 token
     * 
     * USDC uses 6 decimal places:
     * - 1 USDC = 1,000,000 smallest units
     * - 0.5 USDC = 500,000 smallest units
     * - Corresponds to two decimal places in US dollars
     */
    uint8 private constant _decimals = 6;
    
    // ========================================
    // Constructor
    // ========================================
    
    /**
     * @notice Executed when deploying the MockUSDC contract
     * 
     * Features:
     * 1. Sets token name to "Mock USDC"
     * 2. Sets token symbol to "USDC"
     * 3. Mints 1,000,000 USDC to the deployer
     * 
     * Parameter description:
     * - "Mock USDC": Full token name (literal meaning)
     * - "USDC": Token abbreviation (displayed in wallets)
     */
    constructor() ERC20("Mock USDC", "USDC") {
        // Mint 1,000,000 USDC to the deployer
        // msg.sender = address calling this function (the deployer)
        // 1000000 * 10**6 = 1,000,000,000,000 (1 million USDC in smallest units)
        _mint(msg.sender, 1000000 * 10**6);
    }
    
    // ========================================
    // Overridden Functions
    // ========================================
    
    /**
     * @notice Returns the number of decimal places for the token
     * @return Number of decimal places (6)
     * 
     * Why override?
     * - ERC20 standard defaults to 18 decimal places (Ethereum standard)
     * - USDC uses 6 decimal places (USD compatible)
     * - Need to override this function to return the correct value
     * 
     * Usage example:
     *   uint8 decimals = usdc.decimals();  // Returns 6
     */
    function decimals() public pure override returns (uint8) {
        return _decimals;
    }
    
    // ========================================
    // Test Functions (should not exist in production)
    // ========================================
    
    /**
     * @notice Mint USDC to a specified address (for testing)
     * @param to Recipient address
     * @param amount Amount (in smallest units)
     * 
     * ⚠️ Warning: This function allows anyone to mint tokens!
     * - Only suitable for test environments
     * - In real USDC, only Circle company can mint
     * 
     * Usage example:
     *   usdc.mint(alice, 5000 * 10**6);  // Mint 5,000 USDC to alice
     */
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
    
    /**
     * @notice Quick mint USDC (using human-readable amounts)
     * @param to Recipient address
     * @param amountInUSDC USDC amount (integer)
     * 
     * This function simplifies the minting process:
     * - No need to manually calculate decimal places
     * - Input amounts in human-readable format
     * 
     * Example comparison:
     *   Old way: mint(alice, 5000 * 10**6)
     *   New way: mintTo(alice, 5000)
     * 
     * Usage example:
     *   usdc.mintTo(alice, 5000);   // Mint 5,000 USDC
     *   usdc.mintTo(bob, 10000);    // Mint 10,000 USDC
     */
    function mintTo(address to, uint256 amountInUSDC) public {
        // amountInUSDC * 10**6 = conversion to smallest units
        // Example: 5000 * 10**6 = 5,000,000,000 (5,000 USDC in smallest units)
        _mint(to, amountInUSDC * 10**_decimals);
    }
    
    /**
     * @notice Batch mint USDC to multiple addresses (for testing)
     * @param recipients Array of recipient addresses
     * @param amounts Array of USDC amounts (integers)
     * 
     * Features:
     * - Mint USDC to multiple addresses at once
     * - Convenient for setting up test environments
     * 
     * Usage example:
     *   address[] memory recipients = [alice, bob, carol];
     *   uint256[] memory amounts = [5000, 6000, 5500];
     *   usdc.batchMintTo(recipients, amounts);
     */
    function batchMintTo(
        address[] calldata recipients, 
        uint256[] calldata amounts
    ) public {
        // Verify arrays have matching lengths
        require(
            recipients.length == amounts.length, 
            "Recipients and amounts length mismatch"
        );
        
        // Loop through and mint
        for (uint256 i = 0; i < recipients.length; i++) {
            _mint(recipients[i], amounts[i] * 10**_decimals);
        }
    }
}

