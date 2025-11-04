/**
 * PayrollVault Deployment Script
 * 
 * Features:
 * 1. Deploy PayrollVault contract to Arc Testnet
 * 2. Wait for deployment confirmation
 * 3. Output contract address
 * 4. Export ABI and address to backend/abi/ directory for backend use
 * 
 * Usage:
 * npx hardhat run scripts/deploy.ts --network arcTestnet
 * 
 * Required Environment Variables:
 * - USDC_ADDRESS: USDC token address on Arc Testnet
 * - ADMIN_ADDRESS: Admin address (will receive all roles)
 */

import { ethers, artifacts } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  console.log("🚀 Starting PayrollVault contract deployment...\n");

  // Read configuration from environment variables
  const usdc = process.env.USDC_ADDRESS;
  const admin = process.env.ADMIN_ADDRESS;

  // Validate environment variables
  if (!usdc) {
    throw new Error("❌ Missing environment variable: USDC_ADDRESS");
  }
  if (!admin) {
    throw new Error("❌ Missing environment variable: ADMIN_ADDRESS");
  }

  console.log("📋 Deployment Parameters:");
  console.log(`   USDC Address: ${usdc}`);
  console.log(`   Admin Address: ${admin}\n`);

  // Get deployer account
  const [deployer] = await ethers.getSigners();
  console.log(`📝 Deployer: ${deployer.address}`);
  console.log(`💰 Balance: ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH\n`);

  // Deploy contract
  console.log("⏳ Deploying contract...");
  const Vault = await ethers.getContractFactory("PayrollVault");
  const vault = await Vault.deploy(usdc, admin);
  
  // Wait for deployment to complete
  await vault.waitForDeployment();
  const address = await vault.getAddress();
  
  console.log(`✅ PayrollVault deployed to: ${address}\n`);

  // Export ABI to backend/abi/ directory
  console.log("📦 Exporting ABI and address...");
  const artifact = await artifacts.readArtifact("PayrollVault");
  
  // Ensure backend/abi directory exists
  const abiDir = path.join(__dirname, "../../backend/abi");
  if (!fs.existsSync(abiDir)) {
    fs.mkdirSync(abiDir, { recursive: true });
  }

  // Write ABI JSON
  const abiPath = path.join(abiDir, "PayrollVault.json");
  fs.writeFileSync(abiPath, JSON.stringify(artifact.abi, null, 2));
  console.log(`   ✓ ABI saved to: ${abiPath}`);

  // Write contract address
  const addressPath = path.join(abiDir, "PayrollVault.address");
  fs.writeFileSync(addressPath, address);
  console.log(`   ✓ Address saved to: ${addressPath}`);

  console.log("\n🎉 Deployment complete!");
  console.log("\n📌 Next Steps:");
  console.log("   1. Update PAYROLL_CONTRACT_ADDRESS in backend/.env");
  console.log(`   2. PAYROLL_CONTRACT_ADDRESS=${address}`);
  console.log("   3. Grant APPROVER_ROLE to backend service account (if needed)");
}

// Execute deployment script
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
