/**
 * Wallet Generator Script
 * 
 * Generates a new Ethereum wallet with address and private key.
 * Use this to create a new wallet for Arc Testnet deployment.
 * 
 * ⚠️  SECURITY WARNING:
 * - Save the private key securely
 * - Never share your private key
 * - Never commit private keys to version control
 * - Use different keys for testnet and mainnet
 */

import { ethers } from "hardhat";

async function main() {
  console.log("\n========================================");
  console.log("🔑 Ethereum Wallet Generator");
  console.log("========================================\n");

  // Generate random wallet
  const wallet = ethers.Wallet.createRandom();
  
  console.log("✅ New Wallet Generated:\n");
  console.log("Address:     ", wallet.address);
  console.log("Private Key: ", wallet.privateKey);
  console.log();
  
  // Also show the mnemonic phrase
  if (wallet.mnemonic) {
    console.log("Mnemonic Phrase (12 words):");
    console.log(wallet.mnemonic.phrase);
    console.log();
  }

  console.log("========================================");
  console.log("⚠️  IMPORTANT SECURITY NOTES:");
  console.log("========================================");
  console.log("1. Save these credentials securely");
  console.log("2. Never share your private key");
  console.log("3. Never commit to version control");
  console.log("4. Add to .env file:");
  console.log(`   PRIVATE_KEY=${wallet.privateKey}`);
  console.log(`   ADMIN_ADDRESS=${wallet.address}`);
  console.log();
  console.log("========================================");
  console.log("📚 Next Steps:");
  console.log("========================================");
  console.log("1. Add credentials to .env file");
  console.log("2. Fund wallet at: https://faucet.circle.com");
  console.log("   - Select 'Arc Testnet'");
  console.log(`   - Paste address: ${wallet.address}`);
  console.log("   - Request testnet USDC");
  console.log();
  console.log("3. Deploy contract:");
  console.log("   npm run deploy:arc");
  console.log();
  console.log("========================================\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

