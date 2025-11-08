/**
 * Cross-Chain PayrollVault Deployment Script
 * 
 * This script deploys the CrossChainPayrollVault contract with CCTP integration
 * to Arc Testnet (or other CCTP-supported networks).
 * 
 * Prerequisites:
 * - .env file with PRIVATE_KEY and ADMIN_ADDRESS
 * - Wallet funded with sufficient gas (USDC on Arc)
 * - TokenMessenger contract address for target network
 * 
 * Usage:
 * npx hardhat run scripts/deploy-crosschain-vault.ts --network arcTestnet
 * 
 * What this script does:
 * 1. Validates environment configuration
 * 2. Checks deployer balance
 * 3. Deploys CrossChainPayrollVault with CCTP support
 * 4. Configures roles (APPROVER, OPERATOR)
 * 5. Verifies deployment
 * 6. Saves deployment information
 * 7. Outputs configuration for backend integration
 */

import { ethers } from "hardhat";
import * as fs from "fs";
import * as dotenv from "dotenv";

dotenv.config();

/**
 * CCTP TokenMessenger Contract Addresses
 * 
 * Official addresses for different networks:
 * 
 * MAINNET:
 * - Ethereum: 0xbd3fa81b58ba92a82136038b25adec7066af3155
 * - Avalanche: 0x6b25532e1060ce10cc3b0a99e5683b91bfde6982
 * - Optimism: 0x2B4069517957735bE00ceE0fadAE88a26365528f
 * - Arbitrum: 0x19330d10D9Cc8751218eaf51E8885D058642E08A
 * - Base: 0x1682Ae6375C4E4A97e4B583BC394c861A46D8962
 * - Polygon: 0x9daF8c91AEFAE50b9c0E69629D3F6Ca40cA3B3FE
 * 
 * TESTNET:
 * - Ethereum Sepolia: 0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5
 * - Avalanche Fuji: 0xa9fb1b3009dcb79e2fe346c16a604b8fa8ae0a79
 * - Optimism Sepolia: 0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5
 * - Arbitrum Sepolia: 0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5
 * - Base Sepolia: 0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5
 * 
 * Arc Testnet: (check official documentation)
 * TODO: Update with official Arc Testnet TokenMessenger address when available
 */
const TOKEN_MESSENGER_ADDRESSES: { [key: string]: string } = {
  // Testnet addresses
  sepolia: "0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
  fuji: "0xa9fb1b3009dcb79e2fe346c16a604b8fa8ae0a79",
  optimismSepolia: "0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
  arbitrumSepolia: "0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
  baseSepolia: "0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
  
  // Mainnet addresses
  mainnet: "0xbd3fa81b58ba92a82136038b25adec7066af3155",
  avalanche: "0x6b25532e1060ce10cc3b0a99e5683b91bfde6982",
  optimism: "0x2B4069517957735bE00ceE0fadAE88a26365528f",
  arbitrum: "0x19330d10D9Cc8751218eaf51E8885D058642E08A",
  base: "0x1682Ae6375C4E4A97e4B583BC394c861A46D8962",
  polygon: "0x9daF8c91AEFAE50b9c0E69629D3F6Ca40cA3B3FE",
  
  // Arc Testnet (placeholder - update with actual address)
  arcTestnet: process.env.TOKEN_MESSENGER_ADDRESS || "",
};

async function main() {
  console.log("\n🚀 Starting CrossChainPayrollVault deployment...\n");
  console.log("═".repeat(70));

  // ========================================
  // Step 1: Get deployer account
  // ========================================
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  
  console.log("\n📋 Deployment Configuration:");
  console.log("─".repeat(70));
  console.log(`  Network Name:      ${network.name}`);
  console.log(`  Chain ID:          ${network.chainId}`);
  console.log(`  Deployer Address:  ${deployer.address}`);

  // Check deployer balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`  Deployer Balance:  ${ethers.formatUnits(balance, 6)} USDC`);
  
  if (balance < ethers.parseUnits("10", 6)) {
    console.error("\n❌ Error: Insufficient balance for deployment!");
    console.error("   Minimum required: 10 USDC");
    console.error("   Please fund your wallet at: https://faucet.circle.com");
    process.exit(1);
  }

  // ========================================
  // Step 2: Get contract addresses
  // ========================================
  console.log("\n💰 Contract Configuration:");
  console.log("─".repeat(70));
  
  // USDC address
  const usdcAddress = process.env.USDC_ADDRESS || 
    "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"; // Arc Testnet default
  
  console.log(`  USDC Address:              ${usdcAddress}`);
  
  // TokenMessenger address
  let tokenMessengerAddress = TOKEN_MESSENGER_ADDRESSES[network.name] || 
    process.env.TOKEN_MESSENGER_ADDRESS;
  
  if (!tokenMessengerAddress) {
    console.error("\n❌ Error: TokenMessenger address not configured!");
    console.error("   Please set TOKEN_MESSENGER_ADDRESS in .env file");
    console.error("   Or update TOKEN_MESSENGER_ADDRESSES in this script");
    process.exit(1);
  }
  
  console.log(`  TokenMessenger Address:    ${tokenMessengerAddress}`);
  
  // Admin address
  const adminAddress = process.env.ADMIN_ADDRESS || deployer.address;
  console.log(`  Admin Address:             ${adminAddress}`);

  // ========================================
  // Step 3: Deploy CrossChainPayrollVault
  // ========================================
  console.log("\n📄 Deploying CrossChainPayrollVault...");
  console.log("─".repeat(70));
  
  const CrossChainPayrollVault = await ethers.getContractFactory("CrossChainPayrollVault");
  
  console.log("  ⏳ Sending deployment transaction...");
  const vault = await CrossChainPayrollVault.deploy(
    usdcAddress,
    adminAddress,
    tokenMessengerAddress
  );
  
  console.log("  ⏳ Waiting for deployment confirmation...");
  await vault.waitForDeployment();
  
  const vaultAddress = await vault.getAddress();
  
  console.log("  ✅ CrossChainPayrollVault deployed successfully!");
  console.log(`  📍 Contract Address: ${vaultAddress}`);

  // ========================================
  // Step 4: Configure additional roles (optional)
  // ========================================
  console.log("\n🔑 Configuring Roles...");
  console.log("─".repeat(70));
  
  const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
  const OPERATOR_ROLE = ethers.keccak256(ethers.toUtf8Bytes("OPERATOR_ROLE"));
  
  // Check if we need to grant roles to additional addresses
  const operatorAddress = process.env.OPERATOR_ADDRESS;
  
  if (operatorAddress && operatorAddress !== deployer.address && operatorAddress !== adminAddress) {
    console.log(`  ⏳ Granting APPROVER_ROLE to: ${operatorAddress}`);
    const tx1 = await vault.grantRole(APPROVER_ROLE, operatorAddress);
    await tx1.wait();
    console.log("  ✅ APPROVER_ROLE granted");
    
    console.log(`  ⏳ Granting OPERATOR_ROLE to: ${operatorAddress}`);
    const tx2 = await vault.grantRole(OPERATOR_ROLE, operatorAddress);
    await tx2.wait();
    console.log("  ✅ OPERATOR_ROLE granted");
  } else {
    console.log("  ✅ Default roles configured (admin has all roles)");
  }

  // ========================================
  // Step 5: Verify deployment
  // ========================================
  console.log("\n🔍 Verifying Deployment...");
  console.log("─".repeat(70));
  
  const deployedUSDC = await vault.USDC();
  console.log(`  USDC Address:       ${deployedUSDC}`);
  console.log(`  Matches expected:   ${deployedUSDC === usdcAddress ? "✅" : "❌"}`);
  
  const deployedMessenger = await vault.tokenMessenger();
  console.log(`  TokenMessenger:     ${deployedMessenger}`);
  console.log(`  Matches expected:   ${deployedMessenger === tokenMessengerAddress ? "✅" : "❌"}`);
  
  const hasAdminRole = await vault.hasRole(
    await vault.DEFAULT_ADMIN_ROLE(),
    adminAddress
  );
  console.log(`  Admin Role:         ${hasAdminRole ? "✅" : "❌"}`);
  
  const isPaused = await vault.paused();
  console.log(`  Contract Status:    ${isPaused ? "⏸️  Paused" : "▶️  Active"}`);

  // ========================================
  // Step 6: Save deployment information
  // ========================================
  console.log("\n💾 Saving Deployment Information...");
  console.log("─".repeat(70));
  
  const deploymentInfo = {
    network: network.name,
    chainId: network.chainId.toString(),
    timestamp: new Date().toISOString(),
    deployer: deployer.address,
    admin: adminAddress,
    contracts: {
      CrossChainPayrollVault: vaultAddress,
      USDC: usdcAddress,
      TokenMessenger: tokenMessengerAddress,
    },
    roles: {
      DEFAULT_ADMIN_ROLE: await vault.DEFAULT_ADMIN_ROLE(),
      APPROVER_ROLE: APPROVER_ROLE,
      OPERATOR_ROLE: OPERATOR_ROLE,
    },
    cctp: {
      supportsEthereum: true,
      supportsAvalanche: true,
      supportsOptimism: true,
      supportsArbitrum: true,
      supportsBase: true,
      supportsPolygon: true,
    },
    explorer: {
      contract: `https://testnet.arcscan.app/address/${vaultAddress}`,
      deployer: `https://testnet.arcscan.app/address/${deployer.address}`,
    },
  };

  const deploymentFile = `deployment-crosschain-${network.name}.json`;
  fs.writeFileSync(
    deploymentFile,
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log(`  ✅ Saved to: ${deploymentFile}`);

  // ========================================
  // Step 7: Output backend configuration
  // ========================================
  console.log("\n📝 Backend Configuration");
  console.log("═".repeat(70));
  console.log("Copy these variables to your backend .env file:\n");
  console.log("# Cross-Chain Payroll Configuration");
  console.log(`PAYROLL_CONTRACT_ADDRESS=${vaultAddress}`);
  console.log(`USDC_ADDRESS=${usdcAddress}`);
  console.log(`TOKEN_MESSENGER_ADDRESS=${tokenMessengerAddress}`);
  console.log(`PAYROLL_CONTRACT_ABI_PATH=/app/abi/CrossChainPayrollVault.json`);
  console.log(`USDC_DECIMALS=6`);
  console.log(`\n# CCTP Domain IDs`);
  console.log(`CCTP_DOMAIN_ETHEREUM=0`);
  console.log(`CCTP_DOMAIN_AVALANCHE=1`);
  console.log(`CCTP_DOMAIN_OPTIMISM=2`);
  console.log(`CCTP_DOMAIN_ARBITRUM=3`);
  console.log(`CCTP_DOMAIN_BASE=6`);
  console.log(`CCTP_DOMAIN_POLYGON=7`);

  // ========================================
  // Step 8: Next steps
  // ========================================
  console.log("\n");
  console.log("═".repeat(70));
  console.log("✅ Deployment Complete!");
  console.log("═".repeat(70));
  console.log("\n📚 Next Steps:\n");
  console.log("1. View contract on explorer:");
  console.log(`   ${deploymentInfo.explorer.contract}\n`);
  
  console.log("2. Copy ABI to backend:");
  console.log("   cp artifacts/contracts/CrossChainPayrollVault.sol/CrossChainPayrollVault.json \\");
  console.log("      ../backend/abi/\n");
  
  console.log("3. Update backend/.env with configuration above\n");
  
  console.log("4. Fund the vault with USDC:");
  console.log(`   - Contract address: ${vaultAddress}`);
  console.log("   - Get testnet USDC: https://faucet.circle.com\n");
  
  console.log("5. Test same-chain payout:");
  console.log("   npx hardhat run scripts/test-same-chain-payout.ts --network arcTestnet\n");
  
  console.log("6. Test cross-chain payout:");
  console.log("   npx hardhat run scripts/test-cross-chain-payout.ts --network arcTestnet\n");
  
  console.log("7. Start backend with cross-chain support:");
  console.log("   cd ../backend && docker compose up --build\n");
  
  console.log("⚠️  Important Security Notes:");
  console.log("   - Store deployment info securely");
  console.log("   - Never commit private keys to git");
  console.log("   - Use hardware wallet for mainnet");
  console.log("   - Audit contract before production use");
  
  console.log("\n" + "═".repeat(70) + "\n");
}

// Execute deployment
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment Failed:");
    console.error("═".repeat(70));
    console.error(error);
    console.error("═".repeat(70));
    process.exit(1);
  });

