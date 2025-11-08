# Local Testing Guide for PayrollVault Smart Contract

> Complete guide to test your PayrollVault smart contract locally using Hardhat

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Install Dependencies](#step-1-install-dependencies)
3. [Step 2: Compile Contracts](#step-2-compile-contracts)
4. [Step 3: Start Local Blockchain](#step-3-start-local-blockchain)
5. [Step 4: Deploy to Local Network](#step-4-deploy-to-local-network)
6. [Step 5: Verify Deployment](#step-5-verify-deployment)
7. [Step 6: Test Contract Functions](#step-6-test-contract-functions)
8. [Step 7: Run Automated Tests](#step-7-run-automated-tests)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- **Node.js** (v16 or higher): `node --version`
- **npm** or **yarn**: `npm --version`
- **Git**: `git --version`

---

## Step 1: Install Dependencies

Navigate to the contracts directory and install all required packages:

```bash
cd "/Users/wuyusen/Desktop/Arc Hackathon/arc-ai-agent/contracts"

# Install dependencies
npm install

# Verify installation
npx hardhat --version
```

**What this does:**
- Installs Hardhat development environment
- Installs OpenZeppelin contracts (for AccessControl, Pausable, ERC20)
- Installs TypeScript and testing tools

**Expected Output:**
```
2.19.0
```

---

## Step 2: Compile Contracts

Compile your Solidity contracts to check for syntax errors:

```bash
npx hardhat compile
```

**What this does:**
- Compiles `PayrollVault.sol` and `MockUSDC.sol`
- Generates ABI (Application Binary Interface) files
- Creates TypeScript type definitions
- Outputs to `artifacts/` and `typechain-types/` directories

**Expected Output:**
```
Compiled 15 Solidity files successfully
```

**Generated Files:**
- `artifacts/contracts/PayrollVault.sol/PayrollVault.json` - Contract ABI
- `artifacts/contracts/MockUSDC.sol/MockUSDC.json` - MockUSDC ABI
- `typechain-types/` - TypeScript type definitions

---

## Step 3: Start Local Blockchain

Open a **new terminal window** and start the Hardhat local blockchain node:

```bash
cd "/Users/wuyusen/Desktop/Arc Hackathon/arc-ai-agent/contracts"

npx hardhat node
```

**What this does:**
- Starts a local Ethereum blockchain at `http://127.0.0.1:8545`
- Creates 20 test accounts with 10,000 ETH each
- Provides instant block mining (no waiting for confirmations)
- Displays all account addresses and private keys

**Expected Output:**
```
Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/

Accounts
========

Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

Account #1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 (10000 ETH)
Private Key: 0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
...
```

**Important Notes:**
- **Keep this terminal running** throughout your testing
- These accounts are for testing only - never use them on mainnet
- The blockchain resets every time you restart the node

---

## Step 4: Deploy to Local Network

Open a **second terminal window** and deploy your contracts to the local network:

```bash
cd "/Users/wuyusen/Desktop/Arc Hackathon/arc-ai-agent/contracts"

npx hardhat run scripts/deploy-local.ts --network localhost
```

**What this does:**
1. Deploys `MockUSDC` contract (test USDC token)
2. Deploys `PayrollVault` contract
3. Grants `APPROVER_ROLE` to the operator account
4. Mints 100,000 USDC to the deployer
5. Transfers 100,000 USDC to PayrollVault
6. Saves deployment info to `deployment-local.json`

**Expected Output:**
```
🚀 Starting local deployment...

📋 Account Information:
  - Deployer (Admin): 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
  - Operator (AI Agent): 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
  - Employee 1: 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
  - Employee 2: 0x90F79bf6EB2c4f870365E785982E1f101E93b906
  - Employee 3: 0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65

📄 Deploying MockUSDC contract...
  ✅ MockUSDC deployed successfully: 0x5FbDB2315678afecb367f032d93F642f64180aa3

📄 Deploying PayrollVault contract...
  ✅ PayrollVault deployed successfully: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

🔑 Granting AI Agent operation permissions...
  ✅ Approver role granted to: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8

💰 Funding USDC to PayrollVault...
  ✅ Minted 100,000 USDC to deployer
  ✅ Transferred 100,000 USDC to PayrollVault

🔍 Verifying deployment status...
  - PayrollVault balance: 100000.0 USDC
  - Approver permission: ✅ Granted

📝 ========================================
📝 Environment Variables (Copy to .env file)
📝 ========================================

# ========================================
# Blockchain Configuration (Local Testing)
# ========================================
ARC_RPC_URL=http://127.0.0.1:8545
# If using Docker, change to: http://host.docker.internal:8545

# AI Agent private key (using Hardhat's default second account)
PRIVATE_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d

# PayrollVault contract address
PAYROLL_CONTRACT_ADDRESS=0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

# USDC contract address
USDC_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3

# Contract ABI path (path inside Docker container)
PAYROLL_CONTRACT_ABI_PATH=/app/abi/PayrollVault.json

# USDC decimals
USDC_DECIMALS=6

📝 ========================================

💾 Deployment info saved to: deployment-local.json

✅ Local deployment complete!

📚 Next steps:
  1. Copy the environment variables above to backend/.env file
  2. Copy ABI file: cp artifacts/contracts/PayrollVault.sol/PayrollVault.json ../backend/abi/
  3. Start AI Agent: cd ../backend && docker compose up
  4. Test payroll: curl -X POST "http://localhost:8080/admin/trigger?month=2025-11"
  5. Manually approve batch: 
```
docker compose exec app python -c "
from app.db.connection import SessionLocal
from app.db.models import Approval, ApprovalDecision, PayrollBatch, BatchStatus
from datetime import datetime
import uuid

batch_id = 'batch_f375fd62'  # 您的 batch_id
month = '2025-11'             # 您的月份

db = SessionLocal()
try:
    print(f'🔍 Checking batch: {batch_id}')
    
    # === 步驟 1：確保 PayrollBatch 存在 ===
    batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
    if not batch:
        print(f'📝 Creating PayrollBatch record (for foreign key)...')
        batch = PayrollBatch(
            id=batch_id,
            month=month,
            status=BatchStatus.PENDING_APPROVAL,
            total_amount=0,
            line_count=0,
            anomaly_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(batch)
        db.flush()  # 立即寫入，建立外鍵關係
        print(f'✅ PayrollBatch created')
    else:
        print(f'✅ PayrollBatch already exists')
    
    # === 步驟 2：創建或更新 Approval ===
    approval = db.query(Approval).filter_by(batch_id=batch_id).first()
    if approval:
        print(f'🔄 Updating existing approval...')
        approval.decision = ApprovalDecision.APPROVE_ALL
        approval.approver = 'CLI_MANUAL'
        approval.updated_at = datetime.utcnow()
    else:
        print(f'📝 Creating new approval...')
        approval = Approval(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            decision=ApprovalDecision.APPROVE_ALL,
            approver='CLI_MANUAL',
            comment='Manually approved via CLI',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(approval)
    
    # === 步驟 3：提交到資料庫 ===
    db.commit()
    print(f'')
    print(f'✅ SUCCESS! Batch {batch_id} approved!')
    print(f'   - Decision: APPROVE_ALL')
    print(f'   - Approver: CLI_MANUAL')
    print(f'')
    print(f'⏳ The approve_gate node should detect this within 5 seconds...')
    
except Exception as e:
    db.rollback()
    print(f'')
    print(f'❌ ERROR: {e}')
    print(f'')
    import traceback
    traceback.print_exc()
finally:
    db.close()
"
```

```

---

## Step 5: Verify Deployment

Check that the deployment was successful by verifying the contract addresses and balances:

### 5.1 Check Deployment File

```bash
cat deployment-local.json
```

**Expected Output:**
```json
{
  "network": "localhost",
  "chainId": 31337,
  "timestamp": "2025-11-07T...",
  "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
  "operator": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "contracts": {
    "MockUSDC": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
    "PayrollVault": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
  },
  "testAccounts": {
    "employee1": {
      "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
      "privateKey": "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
    },
    "employee2": {
      "address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
      "privateKey": "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
    },
    "employee3": {
      "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
      "privateKey": "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
    }
  },
  "initialState": {
    "vaultBalance": "100000.0 USDC",
    "approverHasRole": true
  }
}
```

### 5.2 Copy ABI Files

Copy the compiled ABI files to the backend directory:

```bash
# Copy PayrollVault ABI
cp artifacts/contracts/PayrollVault.sol/PayrollVault.json \
   ../backend/abi/PayrollVault.json

# Copy MockUSDC ABI (optional, for testing)
cp artifacts/contracts/MockUSDC.sol/MockUSDC.json \
   ../backend/abi/MockUSDC.json

# Verify files exist
ls -la ../backend/abi/
```

---

## Step 6: Test Contract Functions

Now test the deployed contracts using Hardhat console or command-line tools.

### Using Hardhat Console (Interactive)

```bash
npx hardhat console --network localhost
```

**Test commands in the console:**

```javascript
// Get contract instances
const MockUSDC = await ethers.getContractFactory("MockUSDC");
const usdc = MockUSDC.attach("0x5FbDB2315678afecb367f032d93F642f64180aa3");

const PayrollVault = await ethers.getContractFactory("PayrollVault");
const vault = PayrollVault.attach("0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512");

// Check vault balance
const balance = await usdc.balanceOf("0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512");
console.log("Vault USDC balance:", ethers.formatUnits(balance, 6), "USDC");

// Check operator has APPROVER_ROLE
const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
const hasRole = await vault.hasRole(APPROVER_ROLE, "0x70997970C51812dc3A010C7d01b50e0d17dc79C8");
console.log("Operator has APPROVER_ROLE:", hasRole);

// Test batch payout (as operator)
const [deployer, operator, employee1, employee2, employee3] = await ethers.getSigners();
const vaultAsOperator = vault.connect(operator);

const recipients = ["0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"];
const amounts = [ethers.parseUnits("1000", 6)]; // 1,000 USDC
const batchId = ethers.keccak256(ethers.toUtf8Bytes("test_batch_001"));

const tx = await vaultAsOperator.batchPayout(recipients, amounts, batchId);
await tx.wait();
console.log("Transaction hash:", tx.hash);

// Check employee balance
const employeeBalance = await usdc.balanceOf("0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC");
console.log("Employee USDC balance:", ethers.formatUnits(employeeBalance, 6), "USDC");

// Exit console
.exit
```

---

## Step 7: Run Automated Tests

Create and run automated tests to ensure contract functionality.

### 7.1 Create Test File

Create `test/PayrollVault.test.ts`:

```typescript
import { expect } from "chai";
import { ethers } from "hardhat";
import { PayrollVault, MockUSDC } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("PayrollVault", function () {
  let vault: PayrollVault;
  let usdc: MockUSDC;
  let owner: SignerWithAddress;
  let operator: SignerWithAddress;
  let employee1: SignerWithAddress;
  let employee2: SignerWithAddress;

  beforeEach(async function () {
    // Get signers
    [owner, operator, employee1, employee2] = await ethers.getSigners();

    // Deploy MockUSDC
    const MockUSDC = await ethers.getContractFactory("MockUSDC");
    usdc = await MockUSDC.deploy();
    await usdc.waitForDeployment();

    // Deploy PayrollVault
    const PayrollVault = await ethers.getContractFactory("PayrollVault");
    vault = await PayrollVault.deploy(await usdc.getAddress(), owner.address);
    await vault.waitForDeployment();

    // Grant APPROVER_ROLE to operator
    const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
    await vault.grantRole(APPROVER_ROLE, operator.address);

    // Fund vault with USDC
    const fundAmount = ethers.parseUnits("100000", 6);
    await usdc.mint(owner.address, fundAmount);
    await usdc.transfer(await vault.getAddress(), fundAmount);
  });

  describe("Deployment", function () {
    it("Should set the correct USDC address", async function () {
      expect(await vault.USDC()).to.equal(await usdc.getAddress());
    });

    it("Should grant APPROVER_ROLE to operator", async function () {
      const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
      expect(await vault.hasRole(APPROVER_ROLE, operator.address)).to.be.true;
    });

    it("Should have correct initial balance", async function () {
      const balance = await usdc.balanceOf(await vault.getAddress());
      expect(balance).to.equal(ethers.parseUnits("100000", 6));
    });
  });

  describe("Batch Payout", function () {
    it("Should successfully process batch payout", async function () {
      const recipients = [employee1.address, employee2.address];
      const amounts = [
        ethers.parseUnits("5000", 6),
        ethers.parseUnits("6000", 6),
      ];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_001"));
      const metadata = "November 2025 payroll";

      // Connect as operator and execute payout
      await vault.connect(operator).batchPayout(recipients, amounts, batchId, metadata);

      // Verify balances
      expect(await usdc.balanceOf(employee1.address)).to.equal(amounts[0]);
      expect(await usdc.balanceOf(employee2.address)).to.equal(amounts[1]);
    });

    it("Should emit BatchApproved event", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_002"));
      const metadata = "Test payroll";

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId, metadata)
      )
        .to.emit(vault, "BatchApproved")
        .withArgs(batchId, operator.address, amounts[0], recipients.length);
    });

    it("Should prevent duplicate batch processing", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_003"));
      const metadata = "Test payroll";

      // First payout should succeed
      await vault.connect(operator).batchPayout(recipients, amounts, batchId, metadata);

      // Second payout with same batchId should fail
      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId, metadata)
      ).to.be.revertedWith("BATCH_DONE");
    });

    it("Should reject payout from non-approver", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_004"));
      const metadata = "Test payroll";

      // Employee trying to execute payout should fail
      await expect(
        vault.connect(employee1).batchPayout(recipients, amounts, batchId, metadata)
      ).to.be.reverted;
    });
  });

  describe("Admin Functions", function () {
    it("Should allow admin to pause contract", async function () {
      await vault.pause();
      expect(await vault.paused()).to.be.true;
    });

    it("Should prevent payout when paused", async function () {
      await vault.pause();

      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_005"));
      const metadata = "Test payroll";

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId, metadata)
      ).to.be.reverted;
    });
  });
});
```

### 7.2 Run Tests

```bash
npx hardhat test
```

**Expected Output:**
```
  PayrollVault
    Deployment
      ✔ Should set the correct USDC address (XXms)
      ✔ Should grant APPROVER_ROLE to operator (XXms)
      ✔ Should have correct initial balance (XXms)
    Batch Payout
      ✔ Should successfully process batch payout (XXms)
      ✔ Should emit BatchApproved event (XXms)
      ✔ Should prevent duplicate batch processing (XXms)
      ✔ Should reject payout from non-approver (XXms)
    Admin Functions
      ✔ Should allow admin to pause contract (XXms)
      ✔ Should prevent payout when paused (XXms)

  9 passing (XXs)
```

---

## Troubleshooting

### Problem: "Cannot find module 'hardhat'"

**Solution:**
```bash
npm install
```

### Problem: "Network localhost is not running"

**Solution:**
Start the Hardhat node in a separate terminal:
```bash
npx hardhat node
```

### Problem: "Transaction reverted without a reason"

**Solution:**
Check that:
1. The caller has the required role (APPROVER_ROLE)
2. The contract is not paused
3. The batchId has not been used before
4. The vault has sufficient USDC balance

### Problem: Contract addresses change after restarting node

**Explanation:**
This is normal behavior. Hardhat local network resets completely when restarted. The deployment script will assign new addresses each time.

**Solution:**
Re-run the deployment script after restarting the node, and update your environment variables with the new addresses.

### Problem: "insufficient funds" error

**Solution:**
Make sure you're using one of the Hardhat test accounts, which have 10,000 ETH each.

---

## Next Steps

Once local testing is complete:

1. ✅ All tests passing
2. ✅ Deployment successful
3. ✅ Contract functions working correctly

You're ready to deploy to Arc Testnet! See `ARC_TESTNET_DEPLOYMENT.md` for instructions.

---

## Quick Reference

### Useful Commands

```bash
# Compile contracts
npx hardhat compile

# Start local node
npx hardhat node

# Deploy to local network
npx hardhat run scripts/deploy-local.ts --network localhost

# Run tests
npx hardhat test

# Open Hardhat console
npx hardhat console --network localhost

# Clean build artifacts
npx hardhat clean
```

### Contract Addresses (Local Network)

After deployment, save these from the output:

- MockUSDC: `0x5FbDB2315678afecb367f032d93F642f64180aa3`
- PayrollVault: `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512`

(These are typical addresses, but may vary)

### Test Accounts (Hardhat)

- Deployer: `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266`
- Operator: `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`
- Employee 1: `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC`
- Employee 2: `0x90F79bf6EB2c4f870365E785982E1f101E93b906`
- Employee 3: `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65`

---

**🎉 Congratulations!** You've successfully tested your smart contract locally.

