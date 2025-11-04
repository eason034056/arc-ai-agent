# Smart Contract ABI

此目錄存放智慧合約的 ABI (Application Binary Interface) 文件。

## 文件

- `PayrollVault.json` - PayrollVault 合約的 ABI
- `PayrollVault.address` - 部署後的合約地址

## 生成方式

這些文件由 `contracts/` 目錄中的部署腳本自動生成：

```bash
cd contracts
npx hardhat run scripts/deploy.ts --network arcTestnet
```

部署腳本會自動將 ABI 複製到此目錄。

