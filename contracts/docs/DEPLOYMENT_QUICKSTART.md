# PayrollVault Deployment Quick Start

> Fast track guide to test locally and deploy to Arc Testnet

## 📋 Overview

This guide provides a streamlined path to:
1. ✅ Test your smart contracts locally (5-10 minutes)
2. ✅ Deploy to Arc Testnet (10-15 minutes)
3. ✅ Integrate with AI Agent backend

---

## 🚀 Quick Start: Local Testing

### Step 1: Install & Compile

```bash
cd "/Users/wuyusen/Desktop/Arc Hackathon/arc-ai-agent/contracts"

# Install dependencies
npm install

# Compile contracts
npm run compile
```

**Expected:** `Compiled 15 Solidity files successfully`

### Step 2: Start Local Blockchain

**Terminal 1:**
```bash
npm run node
```

Keep this running! ✋

### Step 3: Deploy Locally

**Terminal 2:**
```bash
npm run deploy:local
```

**Expected:** 
- MockUSDC deployed ✅
- PayrollVault deployed ✅
- Roles configured ✅
- 100,000 USDC funded ✅

### Step 4: Copy ABI

```bash
cp artifacts/contracts/PayrollVault.sol/PayrollVault.json ../backend/abi/
```

### Step 5: Run Tests

```bash
npm test
```

**Expected:** All tests passing ✅

**✨ Local testing complete!** See [`LOCAL_TESTING_GUIDE.md`](./LOCAL_TESTING_GUIDE.md) for detailed instructions.

---

## 🌐 Quick Start: Arc Testnet Deployment

### Step 1: Generate Wallet

```bash
npm run generate-wallet
```

**Save these securely!**
- Address: `0x...`
- Private Key: `0x...`

### Step 2: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env file
nano .env
```

**Add your credentials:**
```ini
ARC_RPC_URL=https://rpc.testnet.arc.network
ARC_CHAIN_ID=462037205
PRIVATE_KEY=0xYOUR_PRIVATE_KEY
ADMIN_ADDRESS=0xYOUR_ADDRESS
USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
```

### Step 3: Fund Your Wallet

1. Visit: **https://faucet.circle.com**
2. Select: **Arc Testnet**
3. Paste: Your address from Step 1
4. Click: **Request Testnet USDC**
5. Wait: ~1 minute for confirmation

### Step 4: Deploy to Arc Testnet

```bash
npm run deploy:arc
```

**Expected output:**
```
🚀 Starting Arc Testnet deployment...
✅ PayrollVault deployed successfully!
  - Contract Address: 0x...
```

### Step 5: Copy ABI & Update Backend

```bash
# Copy ABI
cp artifacts/contracts/PayrollVault.sol/PayrollVault.json ../backend/abi/

# Update backend .env with the output from Step 4
cd ../backend
nano .env
```

### Step 6: Test Deployment (Optional)

```bash
# Back to contracts directory
cd ../contracts

# Run test payout
npm run test:arc
```

**✨ Arc Testnet deployment complete!** See [`ARC_TESTNET_DEPLOYMENT.md`](./ARC_TESTNET_DEPLOYMENT.md) for detailed instructions.

---

## 📚 Available Commands

### Development

```bash
npm run compile          # Compile contracts
npm test                 # Run tests
npm run clean            # Clean build artifacts
```

### Local Testing

```bash
npm run node             # Start local blockchain
npm run deploy:local     # Deploy to local network
```

### Arc Testnet

```bash
npm run generate-wallet  # Generate new wallet
npm run deploy:arc       # Deploy to Arc Testnet
npm run test:arc         # Test deployed contract
```

---

## 📖 Documentation

### Detailed Guides

- **[LOCAL_TESTING_GUIDE.md](./LOCAL_TESTING_GUIDE.md)** - Complete local testing guide
- **[ARC_TESTNET_DEPLOYMENT.md](./ARC_TESTNET_DEPLOYMENT.md)** - Arc Testnet deployment guide
- **[README.md](./README.md)** - General contract information

### Quick Reference

#### Contract Addresses

**Local Network** (after deployment):
- MockUSDC: `0x5FbDB2315678afecb367f032d93F642f64180aa3`
- PayrollVault: `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512`

**Arc Testnet** (official):
- USDC: `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238`
- PayrollVault: Check `deployment-arc-testnet.json` after deployment

#### Network Configuration

**Local Hardhat:**
- RPC: `http://127.0.0.1:8545`
- Chain ID: `31337`
- Gas Token: ETH (test)

**Arc Testnet:**
- RPC: `https://rpc.testnet.arc.network`
- Chain ID: `462037205`
- Gas Token: USDC
- Explorer: `https://testnet.arcscan.app`
- Faucet: `https://faucet.circle.com`

---

## 🔍 Troubleshooting

### Local Testing Issues

**Problem:** `Cannot find module 'hardhat'`
```bash
npm install
```

**Problem:** `Network localhost is not running`
```bash
# Start hardhat node in separate terminal
npm run node
```

### Arc Testnet Issues

**Problem:** `insufficient funds for gas`
```bash
# Get more testnet USDC from faucet
# Visit: https://faucet.circle.com
```

**Problem:** `nonce too low`
```bash
# Wait a few minutes or:
npx hardhat clean
```

**Problem:** Can't connect to Arc RPC
```bash
# Test connection:
curl -X POST https://rpc.testnet.arc.network \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

---

## ✅ Verification Checklist

### Before Deploying to Arc Testnet

- [ ] Local tests pass (`npm test`)
- [ ] Contracts compile without errors
- [ ] Generated wallet and saved credentials
- [ ] Funded wallet with testnet USDC
- [ ] Updated `.env` file with correct values

### After Arc Testnet Deployment

- [ ] Contract deployed successfully
- [ ] Verified on Arc Explorer
- [ ] Copied ABI to backend
- [ ] Updated backend `.env`
- [ ] Funded PayrollVault with USDC
- [ ] Tested with `npm run test:arc`

---

## 🎯 For Hackathon Demo

### Recommended Setup

**For Demo:** Use **local testing** (faster, more reliable)
- Instant transactions (<1 second)
- No network dependencies
- Can reset anytime
- Perfect for live demos

**For Showcase:** Deploy to **Arc Testnet** (optional)
- Real blockchain transactions
- Verifiable on block explorer
- Shows production readiness
- Have as backup if asked

### Demo Preparation

```bash
# Terminal 1: Start local node
npm run node

# Terminal 2: Deploy contracts
npm run deploy:local

# Terminal 3: Start backend
cd ../backend
docker compose up

# Terminal 4: Test payroll
curl -X POST http://localhost:8080/admin/trigger?month=2025-11
```

**Demo takes ~10 seconds total!** ⚡

---

## 🔗 Resources

### Arc Network

- **Faucet:** https://faucet.circle.com
- **RPC:** https://rpc.testnet.arc.network
- **Explorer:** https://testnet.arcscan.app
- **Docs:** https://docs.arc.network

### Smart Contract Info

- **Language:** Solidity 0.8.24
- **Framework:** Hardhat
- **Libraries:** OpenZeppelin
- **Token Standard:** ERC20 (USDC)

### Support

- Review detailed guides in this directory
- Check troubleshooting sections
- Verify network status on Arc Explorer

---

## 📊 Project Structure

```
contracts/
├── contracts/
│   ├── PayrollVault.sol      # Main payroll contract
│   └── MockUSDC.sol           # Test USDC token
├── scripts/
│   ├── deploy-local.ts        # Local deployment
│   ├── deploy-arc-testnet.ts # Arc Testnet deployment
│   ├── generate-wallet.ts    # Wallet generator
│   └── test-arc-payout.ts    # Test script
├── test/                      # Test files (optional)
├── hardhat.config.ts          # Hardhat configuration
├── .env                       # Your secrets (DO NOT COMMIT!)
├── .env.example               # Template for .env
├── deployment-local.json      # Local deployment info
├── deployment-arc-testnet.json # Arc Testnet deployment info
├── LOCAL_TESTING_GUIDE.md     # Detailed local testing guide
├── ARC_TESTNET_DEPLOYMENT.md  # Detailed Arc guide
└── DEPLOYMENT_QUICKSTART.md   # This file
```

---

## 🎉 Success Indicators

### Local Testing ✅
- Hardhat node running
- Contracts deployed
- All tests passing
- AI Agent can connect

### Arc Testnet ✅
- Wallet funded with USDC
- PayrollVault deployed
- Transaction on block explorer
- Backend connected successfully

---

**Ready to deploy?** Start with [local testing](#-quick-start-local-testing), then proceed to [Arc Testnet](#-quick-start-arc-testnet-deployment) when ready!

**Questions?** Check the detailed guides:
- [`LOCAL_TESTING_GUIDE.md`](./LOCAL_TESTING_GUIDE.md)
- [`ARC_TESTNET_DEPLOYMENT.md`](./ARC_TESTNET_DEPLOYMENT.md)

Good luck with your hackathon! 🚀

