/**
 * PayrollVault 部署腳本
 * 
 * 功能說明：
 * 1. 部署 PayrollVault 合約到 Arc Testnet
 * 2. 等待合約部署確認
 * 3. 輸出合約地址
 * 4. 將 ABI 和地址匯出到 backend/abi/ 目錄供後端使用
 * 
 * 使用方式：
 * npx hardhat run scripts/deploy.ts --network arcTestnet
 * 
 * 環境變數需求：
 * - USDC_ADDRESS: Arc Testnet 上的 USDC 代幣地址
 * - ADMIN_ADDRESS: 管理員地址（將獲得所有角色）
 */

import { ethers, artifacts } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  console.log("🚀 開始部署 PayrollVault 合約...\n");

  // 從環境變數讀取配置
  const usdc = process.env.USDC_ADDRESS;
  const admin = process.env.ADMIN_ADDRESS;

  // 驗證環境變數
  if (!usdc) {
    throw new Error("❌ 缺少環境變數: USDC_ADDRESS");
  }
  if (!admin) {
    throw new Error("❌ 缺少環境變數: ADMIN_ADDRESS");
  }

  console.log("📋 部署參數:");
  console.log(`   USDC 地址: ${usdc}`);
  console.log(`   管理員地址: ${admin}\n`);

  // 獲取部署者帳戶
  const [deployer] = await ethers.getSigners();
  console.log(`📝 部署者: ${deployer.address}`);
  console.log(`💰 餘額: ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH\n`);

  // 部署合約
  console.log("⏳ 正在部署合約...");
  const Vault = await ethers.getContractFactory("PayrollVault");
  const vault = await Vault.deploy(usdc, admin);
  
  // 等待部署完成
  await vault.waitForDeployment();
  const address = await vault.getAddress();
  
  console.log(`✅ PayrollVault 已部署到: ${address}\n`);

  // 匯出 ABI 到 backend/abi/ 目錄
  console.log("📦 匯出 ABI 和地址...");
  const artifact = await artifacts.readArtifact("PayrollVault");
  
  // 確保 backend/abi 目錄存在
  const abiDir = path.join(__dirname, "../../backend/abi");
  if (!fs.existsSync(abiDir)) {
    fs.mkdirSync(abiDir, { recursive: true });
  }

  // 寫入 ABI JSON
  const abiPath = path.join(abiDir, "PayrollVault.json");
  fs.writeFileSync(abiPath, JSON.stringify(artifact.abi, null, 2));
  console.log(`   ✓ ABI 已保存到: ${abiPath}`);

  // 寫入合約地址
  const addressPath = path.join(abiDir, "PayrollVault.address");
  fs.writeFileSync(addressPath, address);
  console.log(`   ✓ 地址已保存到: ${addressPath}`);

  console.log("\n🎉 部署完成！");
  console.log("\n📌 下一步:");
  console.log("   1. 更新 backend/.env 中的 PAYROLL_CONTRACT_ADDRESS");
  console.log(`   2. PAYROLL_CONTRACT_ADDRESS=${address}`);
  console.log("   3. 授予後端服務帳戶 APPROVER_ROLE（如果需要）");
}

// 執行部署腳本
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ 部署失敗:", error);
    process.exit(1);
  });

