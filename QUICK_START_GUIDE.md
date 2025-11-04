# Arc Payroll System - 快速啟動指南

> 5 分鐘內啟動完整的 Arc Payroll 系統！

---

## 📋 前置檢查

確保已安裝：
- ✅ Docker Desktop（已啟動）
- ✅ Node.js 20+
- ✅ Git

---

## 🚀 快速啟動（5 步驟）

### 步驟 1：克隆專案

```bash
cd "/Users/wuyusen/Desktop/Arc Hackathon"
cd arc-ai-agent
```

### 步驟 2：初始設定

```bash
# 執行自動設定腳本
make setup
```

這會自動創建：
- `backend/.env`
- `frontend/.env`
- `contracts/.env`

### 步驟 3：編輯環境變數

#### 最小必要配置

**backend/.env**（打開並修改）：
```bash
# 資料庫（使用預設值即可）
DATABASE_URL=postgresql+psycopg2://user:pass@postgres:5432/arc_payroll

# Arc Testnet（必填）
ARC_RPC_URL=https://your-arc-testnet-rpc.example.com
PRIVATE_KEY=0xYourPrivateKeyHere

# Slack（可選，暫時可跳過）
SLACK_BOT_TOKEN=xoxb-***
SLACK_SIGNING_SECRET=***
```

**contracts/.env**（打開並修改）：
```bash
ARC_RPC_URL=https://your-arc-testnet-rpc.example.com
PRIVATE_KEY=0xYourPrivateKeyHere
USDC_ADDRESS=0xYourUSDCAddressOnArcTestnet
ADMIN_ADDRESS=0xYourAdminAddress
```

**frontend/.env**（使用預設值即可）：
```bash
NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8080
```

### 步驟 4：部署智慧合約

```bash
# 進入 contracts 目錄
cd contracts

# 安裝依賴
npm install

# 編譯合約
npx hardhat compile

# 部署到 Arc Testnet
npx hardhat run scripts/deploy.ts --network arcTestnet
```

**重要**：部署完成後，複製合約地址並更新到 `backend/.env`：
```bash
PAYROLL_CONTRACT_ADDRESS=0xYourDeployedContractAddress
```

### 步驟 5：啟動所有服務

```bash
# 回到專案根目錄
cd ..

# 啟動後端和前端
make up-all
```

等待 30 秒讓所有服務啟動...

---

## ✅ 驗證安裝

### 1. 檢查服務狀態

```bash
make status
```

應該看到：
- ✅ arc-payroll-app (running)
- ✅ arc-payroll-postgres (running)
- ✅ arc-payroll-redis (running)
- ✅ arc-payroll-prometheus (running)
- ✅ arc-payroll-grafana (running)
- ✅ arc-payroll-frontend (running)

### 2. 訪問服務

在瀏覽器中打開：

| 服務 | URL | 說明 |
|------|-----|------|
| **前端 UI** | http://localhost:3000 | 管理介面 |
| **後端 API** | http://localhost:8080 | API 端點 |
| **API 文檔** | http://localhost:8080/docs | Swagger UI |
| **Prometheus** | http://localhost:9090 | 監控指標 |
| **Grafana** | http://localhost:3000 | 視覺化（端口衝突，需調整） |

### 3. 測試 API

```bash
# 健康檢查
curl http://localhost:8080/healthz

# 預期回應：
# {"status": "ok"}
```

---

## 🧪 測試系統（可選）

### 執行資料庫遷移

```bash
make backend-migrate
```

### 填充測試資料

```bash
make backend-seed
```

### 手動觸發薪資批次

```bash
curl -X POST "http://localhost:8080/admin/trigger?month=2025-11"
```

### 查看日誌

```bash
make logs
```

---

## 🎯 下一步

現在系統已經運行，你可以：

### 1. 探索前端 UI
訪問 http://localhost:3000
- 查看儀表板
- 瀏覽批次列表（目前為空）

### 2. 觸發第一個批次
```bash
# 手動觸發 2025-11 月薪資
curl -X POST "http://localhost:8080/admin/trigger?month=2025-11"
```

### 3. 監控系統
訪問 http://localhost:9090
- 查看 Prometheus 指標
- 嘗試查詢：`http_requests_total`

### 4. 開發自訂功能
參考 [ARCHITECTURE.md](ARCHITECTURE.md) 了解如何：
- 添加新的 LangGraph 節點
- 創建新的 API 端點
- 擴展前端頁面

---

## 🛠️ 常見問題

### Q1: Docker 容器無法啟動
```bash
# 檢查 Docker Desktop 是否運行
docker ps

# 如果有錯誤，嘗試清理並重啟
make clean
make up-all
```

### Q2: 無法連接到 Arc Testnet
- 檢查 `ARC_RPC_URL` 是否正確
- 確認網路連接
- 嘗試使用備用 RPC 端點

### Q3: 合約部署失敗
- 確認私鑰有足夠的測試幣
- 檢查 `USDC_ADDRESS` 是否正確
- 查看詳細錯誤訊息：`npx hardhat run scripts/deploy.ts --network arcTestnet`

### Q4: 前端無法連接後端
- 確認後端是否運行：`curl http://localhost:8080/healthz`
- 檢查 `frontend/.env` 中的 `NEXT_PUBLIC_BACKEND_BASE_URL`
- 查看瀏覽器 Console 錯誤

### Q5: 資料庫連接錯誤
```bash
# 重啟資料庫
docker compose -f backend/docker-compose.yml restart postgres

# 查看 PostgreSQL 日誌
docker logs arc-payroll-postgres
```

---

## 🔧 開發模式

### 後端開發（熱重載）

```bash
# 停止 Docker 中的後端
cd backend
docker compose stop app

# 本地運行後端（需要 Python 3.11+）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8080
```

### 前端開發（熱重載）

```bash
# 使用開發伺服器
make frontend-dev

# 或手動：
cd frontend
npm install
npm run dev
```

### 合約開發

```bash
cd contracts

# 啟動本地測試網路
npx hardhat node

# 在另一個終端部署到本地
npx hardhat run scripts/deploy.ts --network localhost
```

---

## 📚 更多資源

- [完整架構說明](ARCHITECTURE.md)
- [後端開發指南](backend/README.md)
- [合約開發指南](contracts/README.md)
- [前端開發指南](frontend/README.md)
- [詳細教學](backend/docs/TUTORIAL-01-BASICS.md)

---

## 🆘 獲取幫助

遇到問題？

1. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系統架構
2. 查看日誌：`make logs`
3. 檢查服務狀態：`make status`
4. 提交 Issue 到專案 GitHub

---

**祝你使用愉快！** 🎉

如果一切順利，你現在應該有一個運行中的 AI 薪資管理系統了！

