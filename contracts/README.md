# Arc Payroll Smart Contracts

This directory contains the smart contracts for the Arc Payroll system.

## Contract Description

### PayrollVault.sol

Smart contract for batch payroll distribution with the following main features:

- **Batch Payroll Distribution**: Support one-time distribution to multiple recipients
- **Role-Based Access Control**: Uses OpenZeppelin AccessControl
  - `DEFAULT_ADMIN_ROLE`: Admin, can set caps and pause contract
  - `APPROVER_ROLE`: Approver, can execute batch payouts
  - `OPERATOR_ROLE`: Operator (reserved for future extensions)
- **Security Mechanisms**:
  - Pausable/Resumable (Pausable)
  - Replay attack protection (each batchId can only be processed once)
  - Comprehensive event logging
- **Flexible Error Handling**: Uses low-level call for transfers, records success/failure status for each payout

## Environment Setup

1. **Copy environment variable template**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file**
   ```bash
   # Fill in the following information:
   # - ARC_RPC_URL: Arc Testnet RPC endpoint
   # - ARC_CHAIN_ID: Arc Testnet chain ID
   # - PRIVATE_KEY: Deployer private key
   # - USDC_ADDRESS: USDC token address
   # - ADMIN_ADDRESS: Admin address
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

## Usage

### Compile Contracts
```bash
npm run compile
```

### Run Tests
```bash
npm run test
```

### Deploy to Arc Testnet
```bash
npm run deploy
```

After deployment, the script will automatically:
- Output contract address
- Export ABI to `../backend/abi/PayrollVault.json`
- Save address to `../backend/abi/PayrollVault.address`

### Local Test Deployment
```bash
# Terminal 1: Start local node
npm run node

# Terminal 2: Deploy to local node
npm run deploy:local
```

## Directory Structure

```
contracts/
├── contracts/
│   └── PayrollVault.sol    # Main contract
├── scripts/
│   └── deploy.ts            # Deployment script
├── test/                    # Test files (to be created)
├── hardhat.config.ts        # Hardhat configuration
├── package.json             # Dependency management
├── .env.example             # Environment variable template
└── README.md                # This file
```

## Contract Function Description

### Admin Functions (DEFAULT_ADMIN_ROLE only)

- `setMonthlyCap(uint256 cap)`: Set monthly payout cap
- `pause()`: Pause contract
- `unpause()`: Resume contract

### Core Functions (APPROVER_ROLE only)

- `batchPayout(address[] recipients, uint256[] amounts, bytes32 batchId, string meta)`
  - **Function**: Batch payroll distribution
  - **Parameters**:
    - `recipients`: Array of recipient addresses
    - `amounts`: Corresponding amount array (USDC smallest unit)
    - `batchId`: Unique batch identifier
    - `meta`: Batch metadata (e.g. "2025-11 payroll")
  - **Requirements**:
    - Contract not paused
    - batchId not processed before
    - Array lengths same and not empty

### Query Functions (public)

- `USDC`: USDC token address
- `monthlyCap`: Monthly payout cap
- `processedBatch(bytes32)`: Check if batch has been processed

## Events

- `BatchApproved(bytes32 batchId, address approver, uint256 totalAmount, uint256 count)`
- `PayoutExecuted(bytes32 batchId, address from, uint256 successCount, uint256 failCount)`
- `PayoutLine(bytes32 batchId, uint256 index, address to, uint256 amount, bool success, bytes data)`

## Security Recommendations

⚠️ **Testnet Considerations**:
- Use testnet private keys only
- Don't store large amounts of funds in contract
- Regularly review admin and approver permissions

🔒 **Mainnet Deployment Recommendations**:
- Use multi-signature wallet as DEFAULT_ADMIN_ROLE
- Implement stricter approval processes
- Consider using MPC/HSM for private key management
- Conduct thorough security audits

## License

MIT
