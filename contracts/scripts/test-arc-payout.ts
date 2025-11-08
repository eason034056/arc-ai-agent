/**
 * Arc Testnet Payout Test Script
 * 
 * Tests the PayrollVault contract deployed on Arc Testnet
 * by executing a small test payout.
 * 
 * Prerequisites:
 * - PayrollVault deployed on Arc Testnet
 * - PAYROLL_CONTRACT_ADDRESS set in .env
 * - Deployer has APPROVER_ROLE
 * - Vault funded with USDC
 */

import { ethers } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  console.log("\n🧪 Testing PayrollVault on Arc Testnet\n");

  // ========================================
  // Step 1: Setup
  // ========================================
  const [deployer] = await ethers.getSigners();
  const vaultAddress = process.env.PAYROLL_CONTRACT_ADDRESS;
  const usdcAddress = process.env.USDC_ADDRESS;

  if (!vaultAddress) {
    console.error("❌ PAYROLL_CONTRACT_ADDRESS not set in .env");
    process.exit(1);
  }

  if (!usdcAddress) {
    console.error("❌ USDC_ADDRESS not set in .env");
    process.exit(1);
  }

  console.log("📋 Test Configuration:");
  console.log("  - Network: Arc Testnet");
  console.log("  - Deployer:", deployer.address);
  console.log("  - Vault Address:", vaultAddress);
  console.log("  - USDC Address:", usdcAddress);
  console.log();

  // ========================================
  // Step 2: Get contract instances
  // ========================================
  const vault = await ethers.getContractAt("PayrollVault", vaultAddress);
  const usdc = await ethers.getContractAt(
    "@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20",
    usdcAddress
  );

  // Check vault balance
  const vaultBalance = await usdc.balanceOf(vaultAddress);
  console.log("💰 Vault Balance:", ethers.formatUnits(vaultBalance, 6), "USDC");
  
  if (vaultBalance < ethers.parseUnits("10", 6)) {
    console.error("\n❌ Error: Vault has insufficient USDC!");
    console.error("Please fund the vault first.");
    console.error(`Send USDC to: ${vaultAddress}`);
    process.exit(1);
  }
  console.log();

  // ========================================
  // Step 3: Check permissions
  // ========================================
  console.log("🔑 Checking permissions...");
  const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
  const hasRole = await vault.hasRole(APPROVER_ROLE, deployer.address);
  
  if (!hasRole) {
    console.error("❌ Error: Deployer does not have APPROVER_ROLE!");
    process.exit(1);
  }
  console.log("  ✅ Deployer has APPROVER_ROLE");
  console.log();

  // ========================================
  // Step 4: Prepare test payout
  // ========================================
  // Using a hardhat test account as recipient
  const testRecipient = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC";
  
  const recipients = [testRecipient];
  const amounts = [ethers.parseUnits("10", 6)]; // 10 USDC
  const batchId = ethers.keccak256(
    ethers.toUtf8Bytes(`test_arc_${Date.now()}`)
  );
  const metadata = "Test payroll from Arc Testnet";

  console.log("📝 Payout Details:");
  console.log("  - Recipients:", recipients.length);
  console.log("  - Recipient Address:", recipients[0]);
  console.log("  - Amount:", ethers.formatUnits(amounts[0], 6), "USDC");
  console.log("  - Batch ID:", ethers.hexlify(batchId));
  console.log("  - Metadata:", metadata);
  console.log();

  // Check recipient balance before
  const balanceBefore = await usdc.balanceOf(testRecipient);
  console.log("📊 Recipient balance before:", ethers.formatUnits(balanceBefore, 6), "USDC");
  console.log();

  // ========================================
  // Step 5: Execute payout
  // ========================================
  console.log("💸 Executing batch payout...");
  
  try {
    const tx = await vault.batchPayout(recipients, amounts, batchId, metadata);
    
    console.log("  ✅ Transaction submitted!");
    console.log("  - Transaction hash:", tx.hash);
    console.log("  - Waiting for confirmation...");
    
    const receipt = await tx.wait();
    
    console.log("  ✅ Transaction confirmed!");
    console.log("  - Block number:", receipt?.blockNumber);
    console.log("  - Gas used:", receipt?.gasUsed.toString());
    console.log();

    // ========================================
    // Step 6: Verify results
    // ========================================
    console.log("🔍 Verifying results...");
    
    // Check recipient balance after
    const balanceAfter = await usdc.balanceOf(testRecipient);
    console.log("  - Recipient balance after:", ethers.formatUnits(balanceAfter, 6), "USDC");
    
    // Check balance change
    const balanceChange = balanceAfter - balanceBefore;
    console.log("  - Balance change:", ethers.formatUnits(balanceChange, 6), "USDC");
    
    if (balanceChange === amounts[0]) {
      console.log("  ✅ Payout successful!");
    } else {
      console.log("  ⚠️  Warning: Balance change doesn't match expected amount");
    }
    console.log();

    // Check vault balance after
    const vaultBalanceAfter = await usdc.balanceOf(vaultAddress);
    console.log("  - Vault balance after:", ethers.formatUnits(vaultBalanceAfter, 6), "USDC");
    console.log();

    // ========================================
    // Step 7: Output links
    // ========================================
    console.log("🔗 View on Arc Testnet Explorer:");
    console.log(`  - Transaction: https://testnet.arcscan.app/tx/${tx.hash}`);
    console.log(`  - Contract: https://testnet.arcscan.app/address/${vaultAddress}`);
    console.log(`  - Recipient: https://testnet.arcscan.app/address/${testRecipient}`);
    console.log();

    console.log("✅ Test completed successfully!");
    console.log();
    console.log("📚 Next Steps:");
    console.log("  - Verify transaction on block explorer");
    console.log("  - Test with AI Agent backend");
    console.log("  - Run full integration tests");
    console.log();

  } catch (error: any) {
    console.error("\n❌ Payout failed!");
    console.error("Error:", error.message);
    
    if (error.message.includes("BATCH_DONE")) {
      console.error("\nℹ️  This batch ID has already been processed.");
      console.error("   Try running the script again (it will generate a new batch ID).");
    } else if (error.message.includes("insufficient funds")) {
      console.error("\nℹ️  The vault doesn't have enough USDC.");
      console.error("   Fund the vault at: https://faucet.circle.com");
    }
    
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

