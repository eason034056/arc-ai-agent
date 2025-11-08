# Deploy PayrollVault to Arc Testnet

> Complete guide to deploy and verify your PayrollVault smart contract on Arc Testnet

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Set Up Environment](#step-1-set-up-environment)
4. [Step 2: Configure Arc Testnet](#step-2-configure-arc-testnet)
5. [Step 3: Generate Wallet](#step-3-generate-wallet)
6. [Step 4: Fund Your Wallet](#step-4-fund-your-wallet)
7. [Step 5: Create Deployment Script](#step-5-create-deployment-script)
8. [Step 6: Deploy Contracts](#step-6-deploy-contracts)
9. [Step 7: Verify Deployment](#step-7-verify-deployment)
10. [Step 8: Interact with Deployed Contract](#step-8-interact-with-deployed-contract)
11. [Troubleshooting](#troubleshooting)

---

## Overview

Arc is a stablecoin-native blockchain where **USDC is the native gas token**. This means:

- You pay transaction fees in USDC (not ETH)
- Transactions achieve deterministic finality quickly
- Perfect for payroll and payment applications

**Important Notes:**

⚠️ Arc is currently in **testnet phase**. The network may experience:
- Instability or unplanned downtime
- Network resets (data loss)
- Breaking changes

✅ All testnet USDC is for testing only and has **no real-world value**.

---

## Prerequisites

Before deploying to Arc Testnet, ensure you have:

- ✅ Completed local testing (see `LOCAL_TESTING_GUIDE.md`)
- ✅ All tests passing (`npx hardhat test`)
- ✅ Contracts compiled successfully (`npx hardhat compile`)
- ✅ Node.js and npm installed
- ✅ A secure way to store private keys

---

## Step 1: Set Up Environment

### 1.1 Create Environment File

Create a `.env` file in the contracts directory (if it doesn't exist):

```bash
cd "/Users/wuyusen/Desktop/Arc Hackathon/arc-ai-agent/contracts"

# Create .env file
touch .env

# Add to .gitignore
echo ".env" >> .gitignore
```

### 1.2 Add Arc Testnet Configuration

Open `.env` and add the following:

```ini
# ========================================
# Arc Testnet Configuration
# ========================================

# Arc Testnet RPC URL (official endpoint)
ARC_RPC_URL=https://rpc.testnet.arc.network

# Arc Testnet Chain ID
ARC_CHAIN_ID=462037205

# Your wallet private key (will be generated in Step 3)
PRIVATE_KEY=

# USDC contract address on Arc Testnet (official)
USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238

# Admin address (your wallet address)
ADMIN_ADDRESS=

# Deployed PayrollVault address (will be filled after deployment)
PAYROLL_CONTRACT_ADDRESS=

# ========================================
# Optional: Block Explorer Configuration
# ========================================

# Arc Testnet Explorer
ETHERSCAN_BROWSER_URL=https://testnet.arcscan.app
```

**Important:**
- Never commit `.env` to version control
- Keep your private key secure
- Use different private keys for testnet and mainnet

---

## Step 2: Configure Arc Testnet

### 2.1 Verify Hardhat Configuration

Your `hardhat.config.ts` should already have Arc Testnet configured. Verify it includes:

```typescript
networks: {
  arcTestnet: {
    url: process.env.ARC_RPC_URL || "",
    accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    chainId: Number(process.env.ARC_CHAIN_ID || 0),
    gasPrice: "auto",
  },
}
```

### 2.2 Test Connection

Test your connection to Arc Testnet:

```bash
# Load environment variables
source .env

# Test RPC connection
curl -X POST $ARC_RPC_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

**Expected Output:**
```json
{"jsonrpc":"2.0","id":1,"result":"0x..."}
```

If you see a hex number, the connection is working!

---

## Step 3: Generate Wallet

### 3.1 Generate New Wallet

You need a wallet with a private key to deploy contracts and pay gas fees.

**Option A: Using Ethers.js (Recommended)**

```bash
# Create a script to generate wallet
cat > scripts/generate-wallet.ts << 'EOF'
import { ethers } from "hardhat";

async function main() {
  // Generate random wallet
  const wallet = ethers.Wallet.createRandom();
  
  console.log("\n========================================");
  console.log("New Wallet Generated");
  console.log("========================================\n");
  console.log("Address:     ", wallet.address);
  console.log("Private Key: ", wallet.privateKey);
  console.log("\n⚠️  IMPORTANT: Save these securely!");
  console.log("⚠️  Never share your private key!");
  console.log("========================================\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
EOF

# Run the script
npx hardhat run scripts/generate-wallet.ts
```

**Expected Output:**
```
========================================
New Wallet Generated
========================================

Address:      0x1234567890abcdef1234567890abcdef12345678
Private Key:  0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890

⚠️  IMPORTANT: Save these securely!
⚠️  Never share your private key!
========================================
```

**Option B: Using Foundry Cast (If Available)**

```bash
cast wallet new
```

### 3.2 Update Environment File

Add your generated private key and address to `.env`:

```ini
PRIVATE_KEY=0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
ADMIN_ADDRESS=0x1234567890abcdef1234567890abcdef12345678
```

**Security Best Practices:**

✅ **DO:**
- Store private keys in `.env` (never commit to git)
- Use hardware wallets for mainnet
- Keep separate keys for testnet and mainnet
- Backup your private key securely

❌ **DON'T:**
- Commit private keys to git
- Share private keys with anyone
- Use testnet keys on mainnet
- Store keys in plain text files

---

## Step 4: Fund Your Wallet

Arc Testnet uses **USDC as the native gas token**, so you need testnet USDC to deploy contracts.

### 4.1 Visit Arc Testnet Faucet

1. Go to **[Circle Testnet Faucet](https://faucet.circle.com)**
2. Select **"Arc Testnet"** from the network dropdown
3. Paste your wallet address (from Step 3)
4. Click **"Request Testnet USDC"**
5. Wait for confirmation (usually < 1 minute)

**Faucet Limits:**
- You can request testnet USDC multiple times
- Each request gives you enough USDC for several deployments
- If you need more, wait a few hours and request again

### 4.2 Verify Balance

Check that you received the testnet USDC:

```bash
# Using curl
curl -X POST $ARC_RPC_URL \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"$ADMIN_ADDRESS\",\"latest\"],\"id\":1}"

# Or using cast (if installed)
cast balance $ADMIN_ADDRESS --rpc-url $ARC_RPC_URL
```

**Expected Output:**
```
100000000  (100 USDC with 6 decimals)
```

If you see a non-zero value, you're ready to deploy!

---

## Step 5: Create Deployment Script

### 5.1 Create Arc Testnet Deployment Script

Create `scripts/deploy-arc-testnet.ts`:

```typescript
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
  const operatorAddress = deployer.address; // or process.env.OPERATOR_ADDRESS
  
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
```

### 5.2 Update package.json Scripts

Add a deployment script to `package.json`:

```json
{
  "scripts": {
    "deploy:arc": "hardhat run scripts/deploy-arc-testnet.ts --network arcTestnet"
  }
}
```

---

## Step 6: Deploy Contracts

### 6.1 Pre-Deployment Checklist

Before deploying, verify:

- ✅ `.env` file has `PRIVATE_KEY` and `ADMIN_ADDRESS`
- ✅ Wallet has testnet USDC (check balance)
- ✅ Contracts compile without errors (`npx hardhat compile`)
- ✅ Tests pass locally (`npx hardhat test`)

### 6.2 Deploy to Arc Testnet

```bash
# Load environment variables
source .env

# Deploy contracts
npm run deploy:arc

# Or directly:
npx hardhat run scripts/deploy-arc-testnet.ts --network arcTestnet
```

**What to expect:**

The deployment process will take **30-60 seconds**. You'll see:

1. Network configuration
2. Deployer balance check
3. PayrollVault deployment
4. Role configuration
5. Verification steps
6. Deployment information saved
7. Environment variables for backend

**Expected Output:**

```
🚀 Starting Arc Testnet deployment...

📋 Deployment Configuration:
  - Network: Arc Testnet
  - RPC URL: https://rpc.testnet.arc.network
  - Chain ID: 462037205
  - Deployer Address: 0x1234...5678

  - Deployer Balance: 100.0 USDC

💰 Using Arc Testnet USDC:
  - USDC Address: 0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238

📄 Deploying PayrollVault contract...
  ⏳ Waiting for deployment transaction to confirm...
  ✅ PayrollVault deployed successfully!
  - Contract Address: 0xabcd...ef12

🔑 Configuring roles...
  ✅ Deployer already has all roles

🔍 Verifying deployment...
  - Configured USDC address: 0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
  - Matches expected: ✅
  - Admin has DEFAULT_ADMIN_ROLE: ✅

💾 Deployment info saved to: deployment-arc-testnet.json

📝 ========================================
📝 Environment Variables for Backend
📝 ========================================

# Arc Testnet Configuration
ARC_RPC_URL=https://rpc.testnet.arc.network
PRIVATE_KEY=0xabcd...
PAYROLL_CONTRACT_ADDRESS=0xabcd...ef12
USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
PAYROLL_CONTRACT_ABI_PATH=/app/abi/PayrollVault.json
USDC_DECIMALS=6

📝 ========================================

✅ Deployment Complete!

📚 Next Steps:
  1. View contract on explorer:
     https://testnet.arcscan.app/address/0xabcd...ef12

  2. Copy ABI to backend:
     cp artifacts/contracts/PayrollVault.sol/PayrollVault.json ../backend/abi/

  3. Update backend/.env with the environment variables above

  4. Fund the PayrollVault contract with USDC:
     - Send USDC to: 0xabcd...ef12
     - Or use the faucet and transfer manually

  5. Test with AI Agent:
     cd ../backend && docker compose up

⚠️  Important: Save your deployment info securely!
```

### 6.3 Save Deployment Information

The script automatically saves deployment details to `deployment-arc-testnet.json`:

```json
{
  "network": "Arc Testnet",
  "chainId": "462037205",
  "rpcUrl": "https://rpc.testnet.arc.network",
  "timestamp": "2025-11-07T12:34:56.789Z",
  "deployer": "0x1234567890abcdef1234567890abcdef12345678",
  "admin": "0x1234567890abcdef1234567890abcdef12345678",
  "contracts": {
    "USDC": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    "PayrollVault": "0xabcdef1234567890abcdef1234567890abcdef12"
  },
  "explorer": {
    "contract": "https://testnet.arcscan.app/address/0xabcdef...",
    "deployer": "https://testnet.arcscan.app/address/0x123456..."
  }
}
```

---

## Step 7: Verify Deployment

### 7.1 Check on Block Explorer

1. Open [Arc Testnet Explorer](https://testnet.arcscan.app)
2. Paste your contract address
3. Verify:
   - Contract creation transaction
   - Contract bytecode deployed
   - Initial transactions (role grants)

### 7.2 Verify Contract Interaction

Test that you can interact with the deployed contract:

```bash
# Set variables from deployment output
export VAULT_ADDRESS="0xabcd...ef12"  # Your deployed address
export USDC_ADDRESS="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"

# Using Hardhat console
npx hardhat console --network arcTestnet
```

**In the console:**

```javascript
// Get contract instance
const PayrollVault = await ethers.getContractFactory("PayrollVault");
const vault = PayrollVault.attach("YOUR_VAULT_ADDRESS");

// Check USDC address
const usdcAddress = await vault.USDC();
console.log("USDC Address:", usdcAddress);

// Check if deployer has admin role
const [deployer] = await ethers.getSigners();
const DEFAULT_ADMIN_ROLE = await vault.DEFAULT_ADMIN_ROLE();
const hasRole = await vault.hasRole(DEFAULT_ADMIN_ROLE, deployer.address);
console.log("Has admin role:", hasRole);

// Check contract is not paused
const isPaused = await vault.paused();
console.log("Contract paused:", isPaused);
```

### 7.3 Fund PayrollVault with USDC

Your PayrollVault needs USDC to pay salaries. Transfer USDC from the faucet:

```bash
# Option A: Using Hardhat console
npx hardhat console --network arcTestnet
```

```javascript
const [deployer] = await ethers.getSigners();
const USDC = await ethers.getContractAt(
  "IERC20",
  "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
);

// Check your balance
const balance = await USDC.balanceOf(deployer.address);
console.log("Your USDC balance:", ethers.formatUnits(balance, 6));

// Transfer to PayrollVault
const vaultAddress = "0xabcd...ef12"; // Your vault address
const amount = ethers.parseUnits("50", 6); // 50 USDC
const tx = await USDC.transfer(vaultAddress, amount);
await tx.wait();
console.log("✅ Transferred 50 USDC to PayrollVault");

// Verify vault balance
const vaultBalance = await USDC.balanceOf(vaultAddress);
console.log("Vault USDC balance:", ethers.formatUnits(vaultBalance, 6));
```

---

## Step 8: Interact with Deployed Contract

### 8.1 Test Batch Payout

Create a test script to verify the full payroll flow:

```bash
# Create test script
cat > scripts/test-arc-payout.ts << 'EOF'
import { ethers } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  console.log("\n🧪 Testing PayrollVault on Arc Testnet\n");

  const [deployer] = await ethers.getSigners();
  const vaultAddress = process.env.PAYROLL_CONTRACT_ADDRESS;

  if (!vaultAddress) {
    console.error("❌ PAYROLL_CONTRACT_ADDRESS not set");
    process.exit(1);
  }

  // Get contract instance
  const vault = await ethers.getContractAt("PayrollVault", vaultAddress);
  
  // Test data
  const recipients = [
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC", // Test employee
  ];
  const amounts = [
    ethers.parseUnits("10", 6), // 10 USDC
  ];
  const batchId = ethers.keccak256(
    ethers.toUtf8Bytes(`test_${Date.now()}`)
  );
  const metadata = "Test payroll from Arc Testnet";

  console.log("📝 Payout Details:");
  console.log("  - Recipients:", recipients.length);
  console.log("  - Total Amount:", ethers.formatUnits(amounts[0], 6), "USDC");
  console.log("  - Batch ID:", ethers.hexlify(batchId));
  console.log();

  // Execute payout
  console.log("💸 Executing batch payout...");
  const tx = await vault.batchPayout(recipients, amounts, batchId, metadata);
  
  console.log("  - Transaction hash:", tx.hash);
  console.log("  - Waiting for confirmation...");
  
  const receipt = await tx.wait();
  console.log("  ✅ Transaction confirmed!");
  console.log("  - Block number:", receipt.blockNumber);
  console.log("  - Gas used:", receipt.gasUsed.toString());
  console.log();

  console.log("🔗 View on explorer:");
  console.log(`  https://testnet.arcscan.app/tx/${tx.hash}`);
  console.log();

  console.log("✅ Test completed successfully!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
EOF

# Run test
npx hardhat run scripts/test-arc-payout.ts --network arcTestnet
```

### 8.2 Copy ABI to Backend

```bash
# Copy PayrollVault ABI
cp artifacts/contracts/PayrollVault.sol/PayrollVault.json \
   ../backend/abi/PayrollVault.json

# Verify file exists
ls -la ../backend/abi/PayrollVault.json
```

### 8.3 Update Backend Configuration

Update `backend/.env` with Arc Testnet configuration:

```bash
# Navigate to backend
cd ../backend

# Edit .env file
nano .env
```

**Add or update these lines:**

```ini
# ========================================
# Arc Testnet Configuration
# ========================================
ARC_RPC_URL=https://rpc.testnet.arc.network
PRIVATE_KEY=0xYOUR_PRIVATE_KEY
PAYROLL_CONTRACT_ADDRESS=0xYOUR_VAULT_ADDRESS
USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
PAYROLL_CONTRACT_ABI_PATH=/app/abi/PayrollVault.json
USDC_DECIMALS=6
```

### 8.4 Test with AI Agent

```bash
# Start AI Agent
docker compose up --build

# In another terminal, trigger payroll
curl -X POST "http://localhost:8080/admin/seed-demo?month=2025-11"
curl -X POST "http://localhost:8080/admin/trigger?month=2025-11"

# Watch logs
docker compose logs -f app
```

---

## Troubleshooting

### Problem: "insufficient funds for gas"

**Cause:** Wallet doesn't have enough USDC for transaction fees.

**Solution:**
1. Visit [Circle Faucet](https://faucet.circle.com)
2. Select "Arc Testnet"
3. Request more testnet USDC

### Problem: "nonce too low"

**Cause:** Transaction nonce conflict (previous transaction pending).

**Solution:**
```bash
# Wait a few minutes for pending transactions
# Or reset nonce in Hardhat config:
npx hardhat clean
```

### Problem: "contract not deployed"

**Cause:** Wrong network or contract address.

**Solution:**
Verify in `deployment-arc-testnet.json`:
```bash
cat deployment-arc-testnet.json
```

Check the contract address on [Arc Explorer](https://testnet.arcscan.app).

### Problem: "BATCH_DONE" error

**Cause:** Batch ID already used.

**Solution:**
Each batch ID can only be used once. Generate a new batch ID:
```javascript
const batchId = ethers.keccak256(ethers.toUtf8Bytes(`batch_${Date.now()}`));
```

### Problem: Transaction stuck/pending

**Cause:** Network congestion or low gas price.

**Solution:**
1. Check transaction on [Arc Explorer](https://testnet.arcscan.app)
2. Wait 5-10 minutes
3. If still stuck, contact Arc support

### Problem: "Contract reverted"

**Cause:** Multiple possible reasons.

**Solution:**
Check:
1. Caller has `APPROVER_ROLE`
2. Contract is not paused
3. Vault has sufficient USDC
4. Recipients array matches amounts array
5. Batch ID not already processed

---

## Best Practices

### Security

✅ **DO:**
- Use environment variables for sensitive data
- Keep private keys secure
- Use different keys for testnet/mainnet
- Implement proper access control (roles)
- Test thoroughly on testnet before mainnet

❌ **DON'T:**
- Commit private keys to git
- Reuse testnet keys on mainnet
- Grant unnecessary roles
- Skip testing on testnet

### Gas Optimization

- Batch multiple payouts in one transaction
- Use appropriate gas limits
- Monitor gas usage in tests

### Monitoring

- Save all deployment addresses
- Monitor contract balance
- Track transaction hashes
- Set up alerts for low balance

---

## Next Steps

### Production Readiness

Before going to production (if Arc launches mainnet):

1. **Security Audit**
   - Professional smart contract audit
   - Penetration testing
   - Code review

2. **Testing**
   - Comprehensive unit tests
   - Integration tests
   - Load testing

3. **Monitoring**
   - Transaction monitoring
   - Balance alerts
   - Error logging

4. **Documentation**
   - API documentation
   - User guides
   - Incident response plan

5. **Key Management**
   - Hardware wallet (Ledger/Trezor)
   - Multi-sig wallet
   - Secure key storage

---

## Resources

### Arc Testnet

- **Faucet:** https://faucet.circle.com
- **RPC URL:** https://rpc.testnet.arc.network
- **Explorer:** https://testnet.arcscan.app
- **Chain ID:** 462037205
- **USDC Address:** 0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238

### Documentation

- **Arc Docs:** https://docs.arc.network
- **Hardhat Docs:** https://hardhat.org/docs
- **OpenZeppelin:** https://docs.openzeppelin.com

### Support

- **Arc Discord:** [Join Arc Community]
- **GitHub Issues:** [Report bugs]

---

## Quick Reference

### Deployment Commands

```bash
# Compile contracts
npx hardhat compile

# Deploy to Arc Testnet
npm run deploy:arc

# Test deployed contract
npx hardhat run scripts/test-arc-payout.ts --network arcTestnet

# Open console
npx hardhat console --network arcTestnet
```

### Important Addresses

- **USDC (Arc Testnet):** `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238`
- **Your PayrollVault:** Check `deployment-arc-testnet.json`

---

**🎉 Congratulations!** You've successfully deployed to Arc Testnet.

Your PayrollVault is now live and ready to process payroll on a real blockchain!

