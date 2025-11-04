# Arc Payroll System - 架構總覽

> 本文檔詳細說明 Arc Payroll 系統的完整架構、各個目錄與文件的用途。  
> 根據使用者規則：**解釋每一行 code，並說明他們字面上分別代表什麼意思，例如：為什麼這麼 function 叫這個名字，這個 function 要怎麼使用**

---

## 📂 目錄結構總覽

```
arc-ai-agent/                          # 專案根目錄
├── backend/                           # Python 後端 + AI Agent
│   ├── app/                          # 應用程式主目錄
│   │   ├── agent/                    # LangGraph AI Agent 工作流
│   │   │   ├── graph.py              # 定義 LangGraph 工作流圖
│   │   │   ├── policies.py           # 業務策略與規則（批次大小、限額等）
│   │   │   └── nodes/                # 工作流節點（每個節點是一個處理步驟）
│   │   │       ├── node_ingest.py    # 資料匯入節點：從來源讀取薪資資料
│   │   │       ├── node_clean.py     # 資料清洗節點：驗證與清理資料
│   │   │       ├── node_compute.py   # 薪資計算節點：套用薪資規則計算金額
│   │   │       ├── node_detect.py    # 異常偵測節點：使用 AI 偵測異常薪資
│   │   │       ├── node_summarize.py # 摘要生成節點：生成審批摘要
│   │   │       ├── node_propose.py   # 提案節點：向 Slack 發送審批請求
│   │   │       ├── node_approve_gate.py # 審批閘門：等待 Slack 審批結果
│   │   │       ├── node_onchain.py   # 上鏈節點：執行區塊鏈交易
│   │   │       ├── node_writeback.py # 回寫節點：將結果寫回費用系統
│   │   │       └── node_reconcile.py # 對賬節點：驗證交易與資料一致性
│   │   ├── api/                      # FastAPI 端點
│   │   │   └── main.py               # 主 API 檔案：定義所有 HTTP 端點
│   │   ├── core/                     # 核心功能模組
│   │   │   ├── config.py             # 配置管理：載入環境變數
│   │   │   └── logging.py            # 日誌設定：結構化日誌
│   │   ├── db/                       # 資料庫相關
│   │   │   ├── connection.py         # 資料庫連接管理
│   │   │   ├── models.py             # SQLAlchemy 模型定義
│   │   │   └── schema.py             # Pydantic Schema（API 輸入輸出）
│   │   ├── onchain/                  # 區塊鏈整合
│   │   │   └── service.py            # Web3 服務：與智慧合約互動
│   │   ├── slack/                    # Slack 整合
│   │   │   └── app.py                # Slack Bot：處理指令和互動
│   │   ├── expense/                  # 費用系統整合
│   │   │   └── webhook.py            # Webhook 處理器：接收費用系統回調
│   │   └── payroll/                  # 薪資業務邏輯（保留擴展）
│   ├── abi/                          # 智慧合約 ABI
│   │   └── README.md                 # ABI 目錄說明
│   ├── migrations/                   # Alembic 資料庫遷移
│   │   └── README.md                 # 遷移說明
│   ├── scripts/                      # 工具腳本
│   │   └── seed_demo.py              # 測試資料填充腳本
│   ├── docs/                         # 後端詳細文檔
│   │   ├── TUTORIAL-01-BASICS.md     # 基礎教學
│   │   ├── INDEX.md                  # 文檔索引
│   │   ├── PROJECT_SUMMARY.md        # 專案總結
│   │   └── QUICKSTART.md             # 快速開始
│   ├── docker-compose.yml            # Docker 編排：定義所有服務
│   ├── Dockerfile                    # 後端容器建置
│   ├── requirements.txt              # Python 依賴清單
│   └── .env.example                  # 環境變數範本
│
├── contracts/                        # Solidity 智慧合約
│   ├── contracts/                    # 合約原始碼
│   │   └── PayrollVault.sol          # 薪資金庫合約：批次發薪邏輯
│   ├── scripts/                      # 部署與互動腳本
│   │   └── deploy.ts                 # 合約部署腳本
│   ├── hardhat.config.ts             # Hardhat 配置
│   ├── tsconfig.json                 # TypeScript 配置
│   ├── package.json                  # Node.js 依賴
│   ├── .env.example                  # 合約環境變數範本
│   └── README.md                     # 合約說明文檔
│
├── frontend/                         # Next.js 前端
│   ├── src/                          # 原始碼
│   │   └── app/                      # Next.js App Router
│   │       ├── layout.tsx            # 根布局：導航欄
│   │       ├── page.tsx              # 首頁：儀表板
│   │       └── globals.css           # 全域樣式
│   ├── Dockerfile                    # 前端容器建置
│   ├── next.config.js                # Next.js 配置
│   ├── tailwind.config.ts            # Tailwind CSS 配置
│   ├── tsconfig.json                 # TypeScript 配置
│   ├── package.json                  # Node.js 依賴
│   ├── .env.example                  # 前端環境變數範本
│   └── README.md                     # 前端說明文檔
│
├── ops/                              # 運維與監控
│   ├── prometheus.yml                # Prometheus 配置：指標收集
│   └── README.md                     # 監控說明
│
├── Makefile                          # 一鍵指令集合
├── .gitignore                        # Git 忽略規則
├── README.md                         # 專案主說明
└── ARCHITECTURE.md                   # 本文件
```

---

## 🔍 核心組件詳解

### 1. Backend - LangGraph Agent 工作流

#### 為什麼叫 "LangGraph"？
- **Lang**：Language（語言），代表可處理自然語言與 AI 互動
- **Graph**：圖結構，代表工作流是有向無環圖（DAG），節點間有順序依賴

#### 工作流節點說明

每個節點都是一個**純函式**（pure function），接收 `AgentState` 並回傳新的 `AgentState`。

```python
# 典型節點結構
def run(state: AgentState, dependencies) -> AgentState:
    """
    節點執行函式
    
    Args:
        state: 當前工作流狀態（不可變）
        dependencies: 外部依賴（資料庫、API 等）
        
    Returns:
        新的狀態物件（不修改原狀態）
    """
    # 處理邏輯
    new_data = process(state.data)
    
    # 回傳新狀態
    return state.model_copy(update={"data": new_data})
```

##### 1.1 `node_ingest.py` - 資料匯入節點
**用途**：從外部來源（CSV、API、資料庫）讀取薪資資料

**為什麼叫 ingest？**
- `ingest` 在資料工程中意為「攝入、匯入」資料
- 是資料處理流程的第一步

**如何使用**：
```python
from app.agent.nodes import node_ingest

# 執行匯入
state = node_ingest.run(
    state=initial_state,
    data_source="csv",  # 資料來源類型
    file_path="/path/to/payroll.csv"
)
```

##### 1.2 `node_clean.py` - 資料清洗節點
**用途**：驗證資料格式、移除無效記錄、標準化欄位

**為什麼叫 clean？**
- 清洗（clean）髒資料（dirty data）是資料科學常見術語
- 確保後續節點收到乾淨、可用的資料

**清洗項目**：
- 驗證錢包地址格式
- 檢查金額是否為正數
- 移除重複記錄
- 標準化員工 ID 格式

##### 1.3 `node_compute.py` - 薪資計算節點
**用途**：根據薪資規則計算每個員工的應付金額

**為什麼叫 compute？**
- `compute` 意為「計算」
- 這個節點執行數學運算：底薪 + 獎金 - 扣款

**計算公式**：
```python
amount = base_salary + bonus - deduction
```

##### 1.4 `node_detect.py` - 異常偵測節點
**用途**：使用 AI/規則引擎偵測異常薪資

**為什麼叫 detect？**
- `detect` 意為「偵測、檢測」
- 類似於安全領域的「異常檢測」（anomaly detection）

**偵測項目**：
- 金額異常（過高或過低）
- 突然大幅變化
- 不符合部門常規

##### 1.5 `node_summarize.py` - 摘要生成節點
**用途**：生成人類可讀的批次摘要，供審批者參考

**為什麼叫 summarize？**
- `summarize` 意為「總結、摘要」
- 將複雜資料濃縮成關鍵資訊

**摘要內容**：
- 批次總金額
- 發放人數
- 異常筆數
- 部門分布

##### 1.6 `node_propose.py` - 提案節點
**用途**：向 Slack 發送審批請求

**為什麼叫 propose？**
- `propose` 意為「提議、提案」
- 將計算結果提交給審批者

##### 1.7 `node_approve_gate.py` - 審批閘門
**用途**：暫停工作流，等待 Slack 審批結果

**為什麼叫 approve_gate？**
- `gate` 意為「閘門」
- 像一道關卡，需要通過審批才能繼續

**回傳結果**：
```python
approval = {
    "decision": "APPROVE_ALL" | "APPROVE_PARTIAL" | "REJECT",
    "selected_ids": [...],  # 部分批准時使用
    "approver": "user@example.com",
    "timestamp": "2025-11-04T10:30:00Z"
}
```

##### 1.8 `node_onchain.py` - 上鏈節點
**用途**：執行區塊鏈交易，批次發放 USDC

**為什麼叫 onchain？**
- `onchain` 意為「在鏈上」（區塊鏈術語）
- 與「offchain」（鏈下）相對

**執行流程**：
1. 將資料分批（避免 Gas 過高）
2. 對每批調用 `PayrollVault.batchPayout()`
3. 等待交易確認
4. 記錄交易 Hash

##### 1.9 `node_writeback.py` - 回寫節點
**用途**：將發薪結果回寫到費用系統

**為什麼叫 writeback？**
- `writeback` 意為「寫回」
- 更新外部系統的狀態

##### 1.10 `node_reconcile.py` - 對賬節點
**用途**：驗證交易結果與資料一致性

**為什麼叫 reconcile？**
- `reconcile` 意為「對賬、調和」
- 財務術語，確保帳目相符

**檢查項目**：
- 鏈上事件與資料庫記錄是否一致
- 成功筆數 vs 失敗筆數
- 總金額是否正確

---

### 2. Smart Contract - PayrollVault.sol

#### 為什麼叫 "PayrollVault"？
- **Payroll**：薪資（名詞）
- **Vault**：金庫、保險庫
- 合起來：薪資金庫，安全地管理和發放薪資

#### 核心函式

##### 2.1 `batchPayout()` - 批次發放
```solidity
function batchPayout(
    address[] calldata recipients,  // 收款人地址陣列
    uint256[] calldata amounts,     // 對應金額陣列
    bytes32 batchId,                // 批次唯一識別碼
    string calldata meta            // 批次元資料
) external whenNotPaused onlyRole(APPROVER_ROLE)
```

**為什麼叫 batchPayout？**
- `batch`：批次（一次處理多筆）
- `payout`：發放、支付

**如何使用**：
```typescript
// JavaScript/TypeScript 範例
await payrollVault.batchPayout(
  ["0xAddr1", "0xAddr2"],           // 收款人
  [5000000000, 6000000000],         // 金額（USDC 最小單位）
  ethers.utils.id("batch-2025-11"), // batchId
  "2025-11 Monthly Payroll"         // 元資料
)
```

##### 2.2 `setMonthlyCap()` - 設定每月上限
```solidity
function setMonthlyCap(uint256 cap) external onlyRole(DEFAULT_ADMIN_ROLE)
```

**為什麼叫 setMonthlyCap？**
- `set`：設定
- `Monthly`：每月
- `Cap`：上限（capacity 的縮寫）

##### 2.3 `pause()` / `unpause()` - 暫停/恢復
```solidity
function pause() external onlyRole(DEFAULT_ADMIN_ROLE)
function unpause() external onlyRole(DEFAULT_ADMIN_ROLE)
```

**用途**：緊急情況下暫停所有發薪操作

---

### 3. Frontend - Next.js UI

#### 頁面結構

##### 3.1 `layout.tsx` - 根布局
**用途**：定義所有頁面共用的導航欄與結構

**為什麼叫 layout？**
- `layout` 意為「布局」
- Next.js 約定：`layout.tsx` 是布局組件

**組件結構**：
```tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <nav>導航欄</nav>
        <main>{children}</main>  {/* 子頁面渲染在這裡 */}
      </body>
    </html>
  )
}
```

##### 3.2 `page.tsx` - 頁面組件
**用途**：定義該路由的頁面內容

**為什麼叫 page？**
- Next.js 約定：`page.tsx` 是頁面組件
- 檔案路徑即路由路徑

**範例**：
- `app/page.tsx` → `/`（首頁）
- `app/batches/page.tsx` → `/batches`
- `app/batches/[batchId]/page.tsx` → `/batches/123`（動態路由）

---

## 🔄 完整工作流程範例

### 場景：2025 年 11 月薪資發放

```
1. [Trigger] 定時任務或手動觸發
   POST /admin/trigger?month=2025-11

2. [node_ingest] 從 HR 系統讀取員工薪資資料
   - 讀取 CSV 或調用 API
   - 載入 50 筆員工記錄

3. [node_clean] 清洗資料
   - 驗證錢包地址：移除 2 筆無效地址
   - 檢查金額：1 筆金額為負數，標記為錯誤
   - 剩餘 47 筆有效記錄

4. [node_compute] 計算薪資
   - 套用薪資規則（底薪 + 獎金 - 扣款）
   - 員工 A: 5000 + 500 - 100 = 5400 USDC
   - 員工 B: 6000 + 0 - 200 = 5800 USDC
   - ...

5. [node_detect] 異常偵測
   - AI 偵測到員工 C 的獎金異常高（8000 USDC）
   - 標記 1 筆異常

6. [node_summarize] 生成摘要
   {
     "month": "2025-11",
     "total": "245,600 USDC",
     "count": 47,
     "anomalies": 1,
     "dept_count": 5
   }

7. [node_propose] 發送到 Slack
   - 在 #payroll-approval 頻道發送卡片
   - 包含 3 個按鈕：Approve All / Approve Partial / Reject

8. [node_approve_gate] 等待審批
   - 財務主管點擊 "Approve All"
   - 工作流繼續

9. [node_onchain] 上鏈發薪
   - 將 47 筆分成 2 批（每批 25 筆）
   - 調用 PayrollVault.batchPayout() 兩次
   - 交易 Hash: 0xabc123..., 0xdef456...

10. [node_writeback] 回寫費用系統
    - POST 到 expense 系統 webhook
    - 更新薪資狀態為「已發放」

11. [node_reconcile] 對賬
    - 驗證鏈上事件：47 筆成功，0 筆失敗
    - 總金額匹配：245,600 USDC ✓
    - 對賬報告存入資料庫

12. [Done] 工作流完成
```

---

## 🛠️ 如何擴展系統

### 1. 添加新的 LangGraph 節點

```python
# app/agent/nodes/node_notify.py

def run(state: AgentState, email_service) -> AgentState:
    """
    新節點：發送電子郵件通知
    
    Args:
        state: 當前狀態
        email_service: 郵件服務（注入的依賴）
        
    Returns:
        更新後的狀態
    """
    # 發送郵件
    email_service.send(
        to=state.admin_email,
        subject=f"批次 {state.batch_id} 已完成",
        body=f"成功發放 {len(state.lines)} 筆薪資"
    )
    
    # 回傳狀態（不修改）
    return state
```

**在 graph.py 中註冊**：
```python
graph.add_node("notify", notify.run)
graph.add_edge("reconcile", "notify")  # 對賬後發送通知
graph.add_edge("notify", END)
```

### 2. 添加新的 API 端點

```python
# app/api/main.py

@app.get("/reports/{month}/summary")
async def get_monthly_summary(month: str):
    """
    獲取月度摘要報告
    
    Args:
        month: 月份（格式：YYYY-MM）
        
    Returns:
        月度統計資料
    """
    # 從資料庫查詢
    batches = db.query(Batch).filter(Batch.month == month).all()
    
    return {
        "month": month,
        "total_batches": len(batches),
        "total_amount": sum(b.total_amount for b in batches),
        "total_employees": sum(b.line_count for b in batches)
    }
```

### 3. 添加新的前端頁面

```tsx
// frontend/src/app/reports/page.tsx

export default function ReportsPage() {
  return (
    <div>
      <h1>報表</h1>
      <p>月度報表列表</p>
    </div>
  )
}
```

**路由**：自動對應到 `/reports`

---

## 📊 監控指標說明

### Prometheus 指標

| 指標名稱 | 類型 | 說明 | 使用範例 |
|---------|------|------|---------|
| `http_requests_total` | Counter | HTTP 請求總數 | `rate(http_requests_total[5m])` |
| `http_request_duration_seconds` | Histogram | 請求處理時間 | `histogram_quantile(0.95, ...)` |
| `agent_execution_total` | Counter | Agent 執行次數 | `sum(agent_execution_total)` |
| `batch_processed_total` | Counter | 批次處理總數 | `rate(batch_processed_total[1h])` |
| `transaction_success_total` | Counter | 成功交易數 | `sum(transaction_success_total)` |
| `anomaly_detected_total` | Counter | 異常偵測數 | `rate(anomaly_detected_total[5m])` |

---

## 🔐 安全最佳實踐

### 1. 環境變數管理
- ✅ 使用 `.env` 文件（本地開發）
- ✅ 使用環境變數（生產環境）
- ❌ 絕不提交 `.env` 到 Git
- ❌ 絕不硬編碼私鑰

### 2. 智慧合約安全
- ✅ 使用 OpenZeppelin 合約庫
- ✅ 角色權限控制（AccessControl）
- ✅ 可暫停機制（Pausable）
- ✅ 防重放攻擊（batchId 檢查）
- ⚠️ 主網部署前需安全審計

### 3. API 安全
- ✅ 輸入驗證（Pydantic）
- ✅ 速率限制（Rate Limiting）
- ✅ CORS 設定
- ✅ 認證機制（可選，建議加入）

---

## 📚 延伸閱讀

- [LangGraph 官方文檔](https://langchain-ai.github.io/langgraph/)
- [Hardhat 文檔](https://hardhat.org/docs)
- [Next.js 文檔](https://nextjs.org/docs)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [Prometheus 文檔](https://prometheus.io/docs/)

---

**由 Arc Hackathon 團隊打造** ⚡

