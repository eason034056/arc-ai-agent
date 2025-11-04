# Arc Payroll System - 目錄結構總覽

> 一目了然的完整架構

---

## 🌳 完整目錄樹

```
arc-ai-agent/                                    專案根目錄
│
├── 📄 README.md                                 專案主說明（入口文檔）
├── 📄 ARCHITECTURE.md                           詳細架構說明（含中文註解）
├── 📄 QUICK_START_GUIDE.md                      5分鐘快速啟動指南
├── 📄 MIGRATION_SUMMARY.md                      架構重構總結
├── 📄 STRUCTURE_OVERVIEW.md                     本文件
├── 📄 Makefile                                  一鍵指令集合
├── 📄 .gitignore                                Git 忽略規則
│
├── 📁 backend/                                  【Python 後端 + AI Agent】
│   │
│   ├── 📁 app/                                  應用程式主目錄
│   │   ├── 📄 __init__.py                       包初始化
│   │   │
│   │   ├── 📁 agent/                            【LangGraph AI Agent】
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 graph.py                      工作流圖定義
│   │   │   ├── 📄 policies.py                   業務策略與規則
│   │   │   │
│   │   │   └── 📁 nodes/                        【工作流節點】
│   │   │       ├── 📄 __init__.py
│   │   │       ├── 📄 node_ingest.py            ① 資料匯入
│   │   │       ├── 📄 node_clean.py             ② 資料清洗
│   │   │       ├── 📄 node_compute.py           ③ 薪資計算
│   │   │       ├── 📄 node_detect.py            ④ 異常偵測
│   │   │       ├── 📄 node_summarize.py         ⑤ 摘要生成
│   │   │       ├── 📄 node_propose.py           ⑥ 提案審批
│   │   │       ├── 📄 node_approve_gate.py      ⑦ 審批閘門
│   │   │       ├── 📄 node_onchain.py           ⑧ 上鏈發薪
│   │   │       ├── 📄 node_writeback.py         ⑨ 回寫費用
│   │   │       └── 📄 node_reconcile.py         ⑩ 對賬驗證
│   │   │
│   │   ├── 📁 api/                              【FastAPI 端點】
│   │   │   └── 📄 main.py                       API 主文件（所有路由）
│   │   │
│   │   ├── 📁 core/                             【核心功能】
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 config.py                     配置管理（環境變數）
│   │   │   └── 📄 logging.py                    日誌設定（結構化）
│   │   │
│   │   ├── 📁 db/                               【資料庫】
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 connection.py                 連接管理（Session）
│   │   │   ├── 📄 models.py                     SQLAlchemy 模型
│   │   │   └── 📄 schema.py                     Pydantic Schema
│   │   │
│   │   ├── 📁 onchain/                          【區塊鏈整合】
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 service.py                    Web3 服務（合約互動）
│   │   │
│   │   ├── 📁 slack/                            【Slack 整合】
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 app.py                        Slack Bot（指令/互動）
│   │   │
│   │   ├── 📁 expense/                          【費用系統整合】
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 webhook.py                    Webhook 處理器
│   │   │
│   │   └── 📁 payroll/                          【薪資業務邏輯】
│   │       └── 📄 __init__.py                   （保留擴展）
│   │
│   ├── 📁 abi/                                  【智慧合約 ABI】
│   │   └── 📄 README.md                         ABI 目錄說明
│   │   └── (PayrollVault.json)                  部署後自動生成
│   │   └── (PayrollVault.address)               部署後自動生成
│   │
│   ├── 📁 migrations/                           【Alembic 資料庫遷移】
│   │   └── 📄 README.md                         遷移說明
│   │
│   ├── 📁 scripts/                              【工具腳本】
│   │   ├── 📄 __init__.py
│   │   └── 📄 seed_demo.py                      測試資料填充
│   │
│   ├── 📁 docs/                                 【後端文檔】
│   │   ├── 📄 INDEX.md                          文檔索引
│   │   ├── 📄 PROJECT_SUMMARY.md                專案總結
│   │   ├── 📄 QUICKSTART.md                     快速開始
│   │   └── 📄 TUTORIAL-01-BASICS.md             基礎教學
│   │
│   ├── 📄 docker-compose.yml                    Docker 編排（所有服務）
│   ├── 📄 Dockerfile                            後端容器建置
│   ├── 📄 requirements.txt                      Python 依賴清單
│   └── 📄 .env.example                          環境變數範本
│
├── 📁 contracts/                                【Solidity 智慧合約】
│   │
│   ├── 📁 contracts/                            【合約原始碼】
│   │   └── 📄 PayrollVault.sol                  薪資金庫合約（完整註解）
│   │
│   ├── 📁 scripts/                              【部署與互動腳本】
│   │   └── 📄 deploy.ts                         合約部署腳本
│   │
│   ├── 📄 hardhat.config.ts                     Hardhat 配置（Arc Testnet）
│   ├── 📄 tsconfig.json                         TypeScript 配置
│   ├── 📄 package.json                          Node.js 依賴
│   ├── 📄 .env.example                          環境變數範本
│   └── 📄 README.md                             合約說明文檔
│
├── 📁 frontend/                                 【Next.js 前端】
│   │
│   ├── 📁 src/                                  【原始碼】
│   │   └── 📁 app/                              Next.js App Router
│   │       ├── 📄 layout.tsx                    根布局（導航欄）
│   │       ├── 📄 page.tsx                      首頁（儀表板）
│   │       └── 📄 globals.css                   全域樣式
│   │
│   ├── 📄 Dockerfile                            前端容器建置
│   ├── 📄 next.config.js                        Next.js 配置
│   ├── 📄 tailwind.config.ts                    Tailwind CSS 配置
│   ├── 📄 tsconfig.json                         TypeScript 配置
│   ├── 📄 postcss.config.js                     PostCSS 配置
│   ├── 📄 package.json                          Node.js 依賴
│   ├── 📄 .env.example                          環境變數範本
│   └── 📄 README.md                             前端說明文檔
│
└── 📁 ops/                                      【運維與監控】
    ├── 📄 prometheus.yml                        Prometheus 配置
    └── 📄 README.md                             監控說明
```

---

## 🎯 核心流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Arc Payroll System                        │
└─────────────────────────────────────────────────────────────────┘

┌────────────┐      ┌────────────┐      ┌────────────┐
│   Frontend │◄────►│   Backend  │◄────►│ Blockchain │
│  (Next.js) │      │  (FastAPI) │      │ (PayrollVault)
│            │      │            │      │            │
│ - Dashboard│      │ - API      │      │ - batchPayout()
│ - Batches  │      │ - LangGraph│      │ - Events   │
│ - Reports  │      │ - Agent    │      │            │
└────────────┘      └────┬───────┘      └────────────┘
                         │
                    ┌────┴────┐
                    │         │
              ┌─────▼───┐ ┌──▼─────┐
              │PostgreSQL│ │ Redis  │
              │          │ │        │
              │ Batches  │ │ Cache  │
              │ Lines    │ │ Tasks  │
              └──────────┘ └────────┘
```

---

## 📊 LangGraph 工作流

```
開始
 │
 ▼
[node_ingest] ────► 資料匯入
 │                  ├─ CSV / API / DB
 ▼                  └─ 載入員工薪資資料
[node_clean] ─────► 資料清洗
 │                  ├─ 驗證錢包地址
 │                  ├─ 檢查金額
 ▼                  └─ 移除無效記錄
[node_compute] ───► 薪資計算
 │                  └─ amount = base + bonus - deduction
 ▼
[node_detect] ────► 異常偵測
 │                  ├─ 規則引擎
 │                  └─ AI/LLM 偵測
 ▼
[node_summarize] ─► 摘要生成
 │                  ├─ 總金額
 │                  ├─ 人數
 │                  └─ 異常數
 ▼
[node_propose] ───► Slack 審批
 │                  └─ 發送審批卡片
 ▼
[node_approve_gate] 審批閘門 ◄─── 等待 Slack 回應
 │
 ├─── REJECT ───► 結束
 │
 └─── APPROVE ──► [node_onchain] ──► 上鏈發薪
                   │                  ├─ 分批
                   │                  └─ 調用合約
                   ▼
                  [node_writeback] ─► 回寫費用系統
                   │
                   ▼
                  [node_reconcile] ─► 對賬驗證
                   │                  ├─ 鏈上事件
                   │                  └─ 資料庫記錄
                   ▼
                  結束
```

---

## 🔄 資料流

```
1. 觸發 (Trigger)
   └─► POST /admin/trigger?month=2025-11

2. 資料匯入 (Ingest)
   HR System ──► node_ingest ──► AgentState.lines

3. 清洗與計算 (Clean & Compute)
   AgentState ──► node_clean ──► node_compute ──► 更新 lines

4. 異常偵測 (Detect)
   lines ──► AI/Rules ──► 標記異常 (flags)

5. 審批 (Approval)
   Slack ◄──► node_propose ◄──► node_approve_gate
                                      │
                                      └─► approval.decision

6. 上鏈 (On-chain)
   lines ──► node_onchain ──► Web3 ──► PayrollVault.batchPayout()
                                              │
                                              └─► 發出事件

7. 回寫 (Writeback)
   tx_hashes ──► node_writeback ──► Expense System

8. 對賬 (Reconcile)
   Events (鏈上) ─┐
                   ├─► node_reconcile ──► 對賬報告
   Records (DB)  ─┘
```

---

## 🗂️ 檔案用途速查表

| 檔案 | 用途 | 執行時機 |
|------|------|---------|
| `backend/app/agent/graph.py` | 定義 LangGraph 工作流 | 啟動時載入 |
| `backend/app/agent/policies.py` | 業務規則（批次大小、限額） | 節點執行時使用 |
| `backend/app/api/main.py` | FastAPI 路由定義 | 啟動時載入 |
| `backend/app/onchain/service.py` | Web3 合約互動 | node_onchain 調用 |
| `backend/app/slack/app.py` | Slack Bot 處理器 | Slack 事件觸發 |
| `backend/scripts/seed_demo.py` | 填充測試資料 | 手動執行 |
| `contracts/contracts/PayrollVault.sol` | 薪資合約 | 部署到鏈上 |
| `contracts/scripts/deploy.ts` | 合約部署腳本 | 手動執行 |
| `frontend/src/app/page.tsx` | 首頁儀表板 | 訪問 / 時渲染 |
| `ops/prometheus.yml` | 監控配置 | Prometheus 啟動時載入 |
| `Makefile` | 一鍵指令 | 開發時使用 |

---

## 🚀 快速指令參考

```bash
# 初始設定
make setup                    # 創建所有 .env 文件

# 啟動服務
make up-all                   # 啟動所有服務（後端+前端）
make backend-up               # 僅啟動後端
make frontend-dev             # 前端開發模式（熱重載）

# 資料庫
make backend-migrate          # 執行資料庫遷移
make backend-seed             # 填充測試資料

# 合約
make contracts-compile        # 編譯合約
make contracts-deploy         # 部署到 Arc Testnet

# 監控與除錯
make logs                     # 查看所有日誌
make status                   # 查看服務狀態
make backend-shell            # 進入後端容器

# 清理
make down-all                 # 停止所有服務
make clean                    # 清理所有容器和資料
```

---

## 🌐 服務端點

| 服務 | URL | 說明 |
|------|-----|------|
| 前端 | http://localhost:3000 | 管理介面 |
| 後端 API | http://localhost:8080 | REST API |
| API 文檔 | http://localhost:8080/docs | Swagger UI |
| Prometheus | http://localhost:9090 | 監控指標 |
| Grafana | http://localhost:3000 | 視覺化（端口衝突） |
| PostgreSQL | localhost:5432 | 資料庫 |
| Redis | localhost:6379 | 快取 |

---

## 📚 文檔導航

```
README.md                     專案入口（從這裡開始）
    │
    ├─► QUICK_START_GUIDE.md  快速啟動（5分鐘）
    │
    ├─► ARCHITECTURE.md        詳細架構（含中文註解）
    │
    ├─► STRUCTURE_OVERVIEW.md  目錄結構（本文件）
    │
    └─► MIGRATION_SUMMARY.md   重構總結

backend/docs/
    ├─► INDEX.md               文檔索引
    ├─► QUICKSTART.md          後端快速開始
    ├─► PROJECT_SUMMARY.md     專案總結
    └─► TUTORIAL-01-BASICS.md  基礎教學

contracts/README.md            合約開發指南
frontend/README.md             前端開發指南
ops/README.md                  監控配置說明
```

---

## 🎓 學習路徑

### 1️⃣ 新手入門
1. 閱讀 `README.md`
2. 執行 `QUICK_START_GUIDE.md` 的步驟
3. 訪問 http://localhost:3000 查看 UI

### 2️⃣ 了解架構
1. 閱讀 `ARCHITECTURE.md`（詳細中文註解）
2. 查看 `STRUCTURE_OVERVIEW.md`（本文件）
3. 探索 `backend/app/agent/nodes/` 的各個節點

### 3️⃣ 開發新功能
1. 參考 `ARCHITECTURE.md` 的「如何擴展系統」章節
2. 添加新的 LangGraph 節點
3. 創建新的 API 端點
4. 擴展前端頁面

### 4️⃣ 部署到生產
1. 閱讀安全最佳實踐
2. 配置生產環境變數
3. 執行安全審計（合約）
4. 設定監控告警

---

## ✅ 關鍵特色

- 🤖 **AI-Powered**：LangGraph 驅動的智慧工作流
- ⛓️ **On-Chain**：Arc Testnet 上的智慧合約
- 💬 **Slack 整合**：即時審批與通知
- 📊 **完整監控**：Prometheus + Grafana
- 🎨 **現代 UI**：Next.js + Tailwind CSS
- 📚 **豐富文檔**：中文註解，符合使用者規則
- 🚀 **一鍵啟動**：Makefile 簡化開發流程

---

**此架構完全符合 `arc-payroll-unified-devdoc.md` 規範** ✅

開始探索吧！ 🎉

