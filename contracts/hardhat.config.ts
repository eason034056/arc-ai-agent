/**
 * Hardhat 配置文件
 * 
 * 設定說明：
 * - solidity: 使用 0.8.24 版本（與 PayrollVault.sol 一致）
 * - networks: 配置 Arc Testnet 網路
 * - etherscan: 配置區塊鏈瀏覽器驗證（如需要）
 */

import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";

// 載入環境變數
dotenv.config();

const config: HardhatUserConfig = {
  // Solidity 編譯器版本
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },

  // 網路配置
  networks: {
    // Arc Testnet 配置
    arcTestnet: {
      url: process.env.ARC_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: Number(process.env.ARC_CHAIN_ID || 0),
      gasPrice: "auto",
    },

    // Hardhat 本地網路（用於測試）
    hardhat: {
      chainId: 31337,
    },

    // 可選：添加其他網路
    // localhost: {
    //   url: "http://127.0.0.1:8545",
    // },
  },

  // 區塊鏈瀏覽器驗證配置（如果 Arc Testnet 支援）
  etherscan: {
    apiKey: {
      arcTestnet: process.env.ETHERSCAN_API_KEY || "",
    },
    customChains: [
      {
        network: "arcTestnet",
        chainId: Number(process.env.ARC_CHAIN_ID || 0),
        urls: {
          apiURL: process.env.ETHERSCAN_API_URL || "",
          browserURL: process.env.ETHERSCAN_BROWSER_URL || "",
        },
      },
    ],
  },

  // 路徑配置
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};

export default config;

