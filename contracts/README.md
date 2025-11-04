# Arc Payroll Smart Contracts

此目錄包含 Arc Payroll 系統的智慧合約。

## 合約說明

### PayrollVault.sol

薪資批次發放智慧合約，主要功能：

- **批次發放薪資**：支援一次發放給多個收款人
- **角色權限控制**：使用 OpenZeppelin AccessControl
  - `DEFAULT_ADMIN_ROLE`：管理員，可設定限額、暫停合約
  - `APPROVER_ROLE`：批准者，可執行批次發薪
  - `OPERATOR_ROLE`：操作者（保留給未來擴展）
- **安全機制**：
  - 可暫停/恢復（Pausable）
  - 防重放攻擊（每個 batchId 只能處理一次）
  - 完整事件記錄
- **靈活錯誤處理**：使用低階 call 處理轉帳，記錄每筆成功/失敗狀態

## 環境設定

1. **複製環境變數範本**
   ```bash
   cp .env.example .env
   ```

2. **編輯 .env 文件**
   ```bash
   # 填入以下資訊：
   # - ARC_RPC_URL: Arc Testnet RPC 端點
   # - ARC_CHAIN_ID: Arc Testnet 鏈 ID
   # - PRIVATE_KEY: 部署者私鑰
   # - USDC_ADDRESS: USDC 代幣地址
   # - ADMIN_ADDRESS: 管理員地址
   ```

3. **安裝依賴**
   ```bash
   npm install
   ```

## 使用方式

### 編譯合約
```bash
npm run compile
```

### 執行測試
```bash
npm run test
```

### 部署到 Arc Testnet
```bash
npm run deploy
```

部署完成後，腳本會自動：
- 輸出合約地址
- 將 ABI 匯出到 `../backend/abi/PayrollVault.json`
- 將地址保存到 `../backend/abi/PayrollVault.address`

### 本地測試部署
```bash
# 終端 1：啟動本地節點
npm run node

# 終端 2：部署到本地節點
npm run deploy:local
```

## 目錄結構

```
contracts/
├── contracts/
│   └── PayrollVault.sol    # 主合約
├── scripts/
│   └── deploy.ts            # 部署腳本
├── test/                    # 測試文件（待建立）
├── hardhat.config.ts        # Hardhat 配置
├── package.json             # 依賴管理
├── .env.example             # 環境變數範本
└── README.md                # 本文件
```

## 合約函式說明

### 管理函式（僅 DEFAULT_ADMIN_ROLE）

- `setMonthlyCap(uint256 cap)`：設定每月發薪上限
- `pause()`：暫停合約
- `unpause()`：恢復合約

### 核心函式（僅 APPROVER_ROLE）

- `batchPayout(address[] recipients, uint256[] amounts, bytes32 batchId, string meta)`
  - **功能**：批次發放薪資
  - **參數**：
    - `recipients`：收款人地址陣列
    - `amounts`：對應金額陣列（USDC 最小單位）
    - `batchId`：批次唯一識別碼
    - `meta`：批次元資料（例如 "2025-11 payroll"）
  - **要求**：
    - 合約未暫停
    - batchId 未被處理過
    - 陣列長度相同且不為空

### 查詢函式（公開）

- `USDC`：USDC 代幣地址
- `monthlyCap`：每月發薪上限
- `processedBatch(bytes32)`：檢查批次是否已處理

## 事件

- `BatchApproved(bytes32 batchId, address approver, uint256 totalAmount, uint256 count)`
- `PayoutExecuted(bytes32 batchId, address from, uint256 successCount, uint256 failCount)`
- `PayoutLine(bytes32 batchId, uint256 index, address to, uint256 amount, bool success, bytes data)`

## 安全建議

⚠️ **測試網注意事項**：
- 僅使用測試網私鑰
- 不要在合約中存放大量資金
- 定期檢查管理員和批准者權限

🔒 **主網部署建議**：
- 使用多簽錢包作為 DEFAULT_ADMIN_ROLE
- 實施更嚴格的審批流程
- 考慮使用 MPC/HSM 管理私鑰
- 進行完整的安全審計

## License

MIT

