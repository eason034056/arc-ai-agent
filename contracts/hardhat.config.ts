/**
 * Hardhat Configuration File
 * 
 * Configuration:
 * - solidity: Using version 0.8.24 (consistent with PayrollVault.sol)
 * - networks: Configure Arc Testnet network
 * - etherscan: Configure blockchain explorer verification (if needed)
 */

import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config();

const config: HardhatUserConfig = {
  // Solidity compiler version
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      viaIR: true,  // Enable IR-based compiler to avoid "Stack too deep" errors
    },
  },

  // Network configuration
  networks: {
    // Arc Testnet configuration
    arcTestnet: {
      url: process.env.ARC_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: Number(process.env.ARC_CHAIN_ID || 0),
      gasPrice: "auto",
    },

    // Hardhat local network (for testing)
    hardhat: {
      chainId: 31337,
    },

    // Optional: Add other networks
    // localhost: {
    //   url: "http://127.0.0.1:8545",
    // },
  },

  // Blockchain explorer verification configuration (if Arc Testnet supports it)
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

  // Path configuration
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};

export default config;
