/**
 * Local Deployment Script
 * 
 * Features:
 * 1. Deploy MockUSDC contract (test USDC token)
 * 2. Deploy PayrollVault contract (payroll management contract)
 * 3. Set up role permissions (grant AI Agent operation permissions)
 * 4. Fund test USDC to the contract
 * 5. Output all configuration parameters (can be directly copied to .env file)
 * 
 * Usage:
 *   1. Start Hardhat local node: npx hardhat node
 *   2. Run this script: npx hardhat run scripts/deploy-local.ts --network localhost
 *   3. Copy the output environment variables to backend/.env file
 * 
 * Why do we need this script?
 * - Automate deployment process, avoid manual errors
 * - Complete all setup in one go
 * - Output standardized configuration format
 */

import { ethers } from "hardhat";
import * as fs from "fs";

/**
 * main function: entry point for deployment process
 * 
 * Execution steps:
 * 1. Get test accounts
 * 2. Deploy MockUSDC
 * 3. Deploy PayrollVault
 * 4. Set permissions
 * 5. Fund USDC
 * 6. Verify deployment
 * 7. Output configuration
 */
async function main() {
  console.log("🚀 Starting local deployment...\n");

  // ========================================
  // Step 1: Get test accounts
  // ========================================
  /**
   * getSigners(): Get test accounts provided by Hardhat
   * 
   * Hardhat provides 20 test accounts by default, each account:
   * - Has 10,000 ETH (local test coins)
   * - Has fixed private keys (same after each restart)
   * - Can be used to test various scenarios
   * 
   * Account allocation:
   * - deployer (Account #0): Deploys contracts, acts as admin
   * - operator (Account #1): Account used by AI Agent
   * - employee1-3 (Account #2-4): Test employee accounts
   */
  const [deployer, operator, employee1, employee2, employee3] = await ethers.getSigners();

  console.log("📋 Account Information:");
  console.log("  - Deployer (Admin):", deployer.address);
  console.log("  - Operator (AI Agent):", operator.address);
  console.log("  - Employee 1:", employee1.address);
  console.log("  - Employee 2:", employee2.address);
  console.log("  - Employee 3:", employee3.address);
  console.log();

  // ========================================
  // Step 2: Deploy MockUSDC
  // ========================================
  /**
   * What is MockUSDC?
   * - A simplified ERC20 token contract
   * - Simulates real USDC stablecoin
   * - Anyone can mint tokens, convenient for testing
   * 
   * Deployment process:
   * 1. getContractFactory(): Get contract factory (used to deploy contracts)
   * 2. deploy(): Deploy contract to blockchain
   * 3. waitForDeployment(): Wait for deployment transaction confirmation
   * 4. getAddress(): Get deployed contract address
   */
  console.log("📄 Deploying MockUSDC contract...");
  const MockUSDC = await ethers.getContractFactory("MockUSDC");
  const usdc = await MockUSDC.deploy();
  await usdc.waitForDeployment();
  
  const usdcAddress = await usdc.getAddress();
  console.log("  ✅ MockUSDC deployed successfully:", usdcAddress);
  console.log();

  // ========================================
  // Step 3: Deploy PayrollVault
  // ========================================
  /**
   * What is PayrollVault?
   * - Payroll management smart contract
   * - Responsible for batch sending USDC to employees
   * - Has role-based access control (admin, operator)
   * 
   * Deployment parameters:
   * 1. usdcAddress: USDC contract address (MockUSDC we just deployed)
   * 2. deployer.address: Admin address (deployer)
   * 
   * Constructor automatically:
   * - Sets deployer as ADMIN_ROLE
   * - Sets deployer as OPERATOR_ROLE (initially)
   * - Sets deployer as DEFAULT_ADMIN_ROLE (highest permission)
   */
  console.log("📄 Deploying PayrollVault contract...");
  const PayrollVault = await ethers.getContractFactory("PayrollVault");
  const vault = await PayrollVault.deploy(
    usdcAddress,      // USDC contract address
    deployer.address  // Admin address
  );
  await vault.waitForDeployment();
  
  const vaultAddress = await vault.getAddress();
  console.log("  ✅ PayrollVault deployed successfully:", vaultAddress);
  console.log();

  // ========================================
  // Step 4: Set up AI Agent permissions
  // ========================================
  /**
   * Why do we need to grant permissions?
   * - PayrollVault's batchPayout() function has onlyRole(APPROVER_ROLE) modifier
   * - Only accounts with APPROVER_ROLE can call it
   * - AI Agent needs this permission to process payroll
   * 
   * What is APPROVER_ROLE?
   * - A bytes32 type role ID
   * - Calculated using keccak256("APPROVER_ROLE")
   * - Used for access control system (AccessControl)
   * 
   * grantRole(role, account):
   * - Grants role to account address
   * - Only DEFAULT_ADMIN_ROLE can call this
   * - Here we grant it to operator address (AI Agent)
   */
  console.log("🔑 Granting AI Agent operation permissions...");
  
  // Calculate APPROVER_ROLE hash
  // keccak256 is Ethereum's hash function
  // toUtf8Bytes converts string to bytes
  const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
  
  // Grant APPROVER_ROLE to operator address
  await vault.grantRole(APPROVER_ROLE, operator.address);
  console.log("  ✅ Approver role granted to:", operator.address);
  console.log();

  // ========================================
  // Step 5: Fund USDC to PayrollVault
  // ========================================
  /**
   * Why do we need to fund?
   * - PayrollVault needs USDC balance to process payroll
   * - Like a bank account needs funds before transfers
   * 
   * Funding process (three steps):
   * 1. mint(): Mint USDC to deployer
   * 2. approve(): Authorize PayrollVault to use deployer's USDC
   * 3. deposit(): PayrollVault calls transferFrom() to transfer USDC
   * 
   * Why do we need approve?
   * - ERC20 standard security mechanism
   * - Prevents contracts from transferring tokens without authorization
   * - Must approve first, then contract can call transferFrom
   */
  console.log("💰 Funding USDC to PayrollVault...");
  
  // 1. Mint 100,000 USDC to deployer
  // parseUnits(value, decimals): Convert human-readable number to smallest units
  // "100000" USDC × 10^6 = 100,000,000,000 smallest units
  const fundAmount = ethers.parseUnits("100000", 6);
  
   await usdc.mint(deployer.address, fundAmount);
   console.log("  ✅ Minted 100,000 USDC to deployer");
   
   // 2. Transfer USDC directly to PayrollVault
   // This contract doesn't have a deposit() function
   // USDC is transferred directly to the contract address
   await usdc.transfer(vaultAddress, fundAmount);
   console.log("  ✅ Transferred 100,000 USDC to PayrollVault");
  console.log();

  // ========================================
  // Step 6: Verify deployment
  // ========================================
  /**
   * What to verify?
   * 1. PayrollVault's USDC balance is correct
   * 2. Operator role has been granted
   * 
   * Why verify?
   * - Ensure all steps executed successfully
   * - Discover potential configuration errors
   * - Provide snapshot of deployment state
   */
  console.log("🔍 Verifying deployment status...");
  
  // Query PayrollVault's USDC balance
  // balanceOf(address): ERC20 standard function, returns token balance of address
  const vaultBalance = await usdc.balanceOf(vaultAddress);
  
  // formatUnits(value, decimals): Convert smallest units to human-readable number
  // 100,000,000,000 ÷ 10^6 = 100,000 USDC
  console.log("  - PayrollVault balance:", ethers.formatUnits(vaultBalance, 6), "USDC");
  
  // Check if operator has APPROVER_ROLE
  // hasRole(role, account): Returns true/false
  const hasApproverRole = await vault.hasRole(APPROVER_ROLE, operator.address);
  console.log("  - Approver permission:", hasApproverRole ? "✅ Granted" : "❌ Not granted");
  console.log();

  // ========================================
  // Step 7: Output configuration parameters
  // ========================================
  /**
   * Why output these parameters?
   * - AI Agent needs to know how to connect to blockchain
   * - Needs contract addresses to call functions
   * - Needs private key to sign transactions
   * 
   * These parameters will be copied to backend/.env file
   */
  console.log("📝 ========================================");
  console.log("📝 Environment Variables (Copy to .env file)");
  console.log("📝 ========================================\n");
  
  console.log("# ========================================");
  console.log("# Blockchain Configuration (Local Testing)");
  console.log("# ========================================");
  console.log(`ARC_RPC_URL=http://127.0.0.1:8545`);
  console.log("# If using Docker, change to: http://host.docker.internal:8545");
  console.log();
  
  console.log("# AI Agent private key (using Hardhat's default second account)");
  console.log("# This is the operator account's private key");
  console.log(`PRIVATE_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d`);
  console.log();
  
  console.log("# PayrollVault contract address");
  console.log(`PAYROLL_CONTRACT_ADDRESS=${vaultAddress}`);
  console.log();
  
  console.log("# USDC contract address");
  console.log(`USDC_ADDRESS=${usdcAddress}`);
  console.log();
  
  console.log("# Contract ABI path (path inside Docker container)");
  console.log(`PAYROLL_CONTRACT_ABI_PATH=/app/abi/PayrollVault.json`);
  console.log();
  
  console.log("# USDC decimals");
  console.log(`USDC_DECIMALS=6`);
  console.log();
  
  console.log("📝 ========================================\n");

  // ========================================
  // Step 8: Save deployment info to file
  // ========================================
  /**
   * Why save to file?
   * - Convenient for automated tests to read
   * - Provides complete deployment record
   * - Includes test account private keys (for testing)
   * 
   * File format: JSON
   * Location: contracts/deployment-local.json
   */
  const deploymentInfo = {
    network: "localhost",
    chainId: 31337,  // Hardhat local network Chain ID
    timestamp: new Date().toISOString(),
    deployer: deployer.address,
    operator: operator.address,
    contracts: {
      MockUSDC: usdcAddress,
      PayrollVault: vaultAddress
    },
    testAccounts: {
      employee1: {
        address: employee1.address,
        privateKey: "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
      },
      employee2: {
        address: employee2.address,
        privateKey: "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
      },
      employee3: {
        address: employee3.address,
        privateKey: "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
      }
    },
    privateKeys: {
      deployer: "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
      operator: "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    },
    initialState: {
      vaultBalance: ethers.formatUnits(vaultBalance, 6) + " USDC",
      approverHasRole: hasApproverRole
    }
  };

  // Write to JSON file
  // JSON.stringify(obj, null, 2): Format JSON with 2-space indentation
  fs.writeFileSync(
    'deployment-local.json',
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log("💾 Deployment info saved to: deployment-local.json\n");
  
  // ========================================
  // Complete
  // ========================================
  console.log("✅ Local deployment complete!");
  console.log("\n📚 Next steps:");
  console.log("  1. Copy the environment variables above to backend/.env file");
  console.log("  2. Copy ABI file: cp artifacts/contracts/PayrollVault.sol/PayrollVault.json ../backend/abi/");
  console.log("  3. Start AI Agent: cd ../backend && docker compose up");
  console.log("  4. Test payroll: curl -X POST http://localhost:8080/admin/trigger?month=2025-11");
}

/**
 * Error handling
 * 
 * If an error occurs during deployment:
 * - Catch the error and output detailed information
 * - Exit with error code (1)
 */
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:");
    console.error(error);
    process.exit(1);
  });

