/**
 * Arc Testnet Deployment Script
 * 
 * This script:
 * 1. Deploys PayrollVault to Arc Testnet
 * 2. Uses existing USDC contract (no need to deploy MockUSDC)
 * 3. Configures admin and operator roles
 * 4. Saves deployment information
 * 
 * Prerequisites:
 * - .env file configured with PRIVATE_KEY and ADMIN_ADDRESS
 * - Wallet funded with testnet USDC from faucet
 */

import { ethers } from "hardhat";
import * as fs from "fs";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  console.log("\n🚀 Starting Arc Testnet deployment...\n");

  // ========================================
  // Step 1: Get deployer account
  // ========================================
  const [deployer] = await ethers.getSigners();
  
  console.log("📋 Deployment Configuration:");
  console.log("  - Network: Arc Testnet");
  console.log("  - RPC URL:", process.env.ARC_RPC_URL);
  console.log("  - Chain ID:", process.env.ARC_CHAIN_ID);
  console.log("  - Deployer Address:", deployer.address);
  console.log();

  // Check deployer balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("  - Deployer Balance:", ethers.formatUnits(balance, 6), "USDC");
  
  if (balance < ethers.parseUnits("10", 6)) {
    console.error("\n❌ Error: Insufficient USDC balance!");
    console.error("Please fund your wallet at: https://faucet.circle.com");
    process.exit(1);
  }
  console.log();

  // ========================================
  // Step 2: Use existing USDC contract
  // ========================================
  // On Arc Testnet, USDC is already deployed
  const usdcAddress = process.env.USDC_ADDRESS;
  
  if (!usdcAddress) {
    console.error("❌ Error: USDC_ADDRESS not set in .env file");
    process.exit(1);
  }
  
  console.log("💰 Using Arc Testnet USDC:");
  console.log("  - USDC Address:", usdcAddress);
  console.log();

  // ========================================
  // Step 3: Deploy PayrollVault
  // ========================================
  console.log("📄 Deploying PayrollVault contract...");
  
  const adminAddress = process.env.ADMIN_ADDRESS || deployer.address;
  
  const PayrollVault = await ethers.getContractFactory("PayrollVault");
  const vault = await PayrollVault.deploy(
    usdcAddress,    // USDC contract address
    adminAddress    // Admin address
  );
  
  console.log("  ⏳ Waiting for deployment transaction to confirm...");
  await vault.waitForDeployment();
  
  const vaultAddress = await vault.getAddress();
  console.log("  ✅ PayrollVault deployed successfully!");
  console.log("  - Contract Address:", vaultAddress);
  console.log();

  // ========================================
  // Step 4: Grant operator role (optional)
  // ========================================
  console.log("🔑 Configuring roles...");
  
  // Calculate APPROVER_ROLE
  const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
  
  // For now, grant APPROVER_ROLE to deployer
  // You can change this later to your AI Agent address
  const operatorAddress = process.env.OPERATOR_ADDRESS || deployer.address;
  
  if (operatorAddress !== deployer.address) {
    console.log("  - Granting APPROVER_ROLE to:", operatorAddress);
    const tx = await vault.grantRole(APPROVER_ROLE, operatorAddress);
    await tx.wait();
    console.log("  ✅ APPROVER_ROLE granted");
  } else {
    console.log("  ✅ Deployer already has all roles");
  }
  console.log();

  // ========================================
  // Step 5: Verify deployment
  // ========================================
  console.log("🔍 Verifying deployment...");
  
  const deployedUSDC = await vault.USDC();
  console.log("  - Configured USDC address:", deployedUSDC);
  console.log("  - Matches expected:", deployedUSDC === usdcAddress ? "✅" : "❌");
  
  const hasAdminRole = await vault.hasRole(
    await vault.DEFAULT_ADMIN_ROLE(),
    adminAddress
  );
  console.log("  - Admin has DEFAULT_ADMIN_ROLE:", hasAdminRole ? "✅" : "❌");
  console.log();

  // ========================================
  // Step 6: Save deployment information
  // ========================================
  const deploymentInfo = {
    network: "Arc Testnet",
    chainId: process.env.ARC_CHAIN_ID,
    rpcUrl: process.env.ARC_RPC_URL,
    timestamp: new Date().toISOString(),
    deployer: deployer.address,
    admin: adminAddress,
    operator: operatorAddress,
    contracts: {
      USDC: usdcAddress,
      PayrollVault: vaultAddress
    },
    explorer: {
      contract: `https://testnet.arcscan.app/address/${vaultAddress}`,
      deployer: `https://testnet.arcscan.app/address/${deployer.address}`
    }
  };

  const deploymentFile = "deployment-arc-testnet.json";
  fs.writeFileSync(
    deploymentFile,
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log("💾 Deployment info saved to:", deploymentFile);
  console.log();

  // ========================================
  // Step 7: Output configuration
  // ========================================
  console.log("📝 ========================================");
  console.log("📝 Environment Variables for Backend");
  console.log("📝 ========================================\n");
  console.log("# Arc Testnet Configuration");
  console.log(`ARC_RPC_URL=${process.env.ARC_RPC_URL}`);
  console.log(`PRIVATE_KEY=${process.env.PRIVATE_KEY}`);
  console.log(`PAYROLL_CONTRACT_ADDRESS=${vaultAddress}`);
  console.log(`USDC_ADDRESS=${usdcAddress}`);
  console.log(`PAYROLL_CONTRACT_ABI_PATH=/app/abi/PayrollVault.json`);
  console.log(`USDC_DECIMALS=6`);
  console.log();
  console.log("📝 ========================================\n");

  // ========================================
  // Step 8: Next steps
  // ========================================
  console.log("✅ Deployment Complete!\n");
  console.log("📚 Next Steps:");
  console.log("  1. View contract on explorer:");
  console.log(`     ${deploymentInfo.explorer.contract}`);
  console.log();
  console.log("  2. Copy ABI to backend:");
  console.log("     cp artifacts/contracts/PayrollVault.sol/PayrollVault.json ../backend/abi/");
  console.log();
  console.log("  3. Update backend/.env with the environment variables above");
  console.log();
  console.log("  4. Fund the PayrollVault contract with USDC:");
  console.log(`     - Send USDC to: ${vaultAddress}`);
  console.log("     - Or use the faucet and transfer manually");
  console.log();
  console.log("  5. Test with AI Agent:");
  console.log("     cd ../backend && docker compose up");
  console.log();
  console.log("⚠️  Important: Save your deployment info securely!");
  console.log();
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:");
    console.error(error);
    process.exit(1);
  });

