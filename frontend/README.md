# Arc Payroll Frontend

這是 Arc Payroll 系統的前端管理介面，使用 Next.js 15 建構。

## 功能特色

- 📊 **儀表板總覽**：顯示當月批次、金額、成功率、異常統計
- 📋 **批次管理**：查看批次列表、詳情、交易狀態
- 📈 **報表下載**：下載對賬報表（CSV）
- ⚙️ **系統設定**：配置 RPC、限額等參數
- 🎨 **現代 UI**：使用 Tailwind CSS，響應式設計

## 技術棧

- **框架**：Next.js 15 (App Router)
- **UI 樣式**：Tailwind CSS
- **狀態管理**：React Query (TanStack Query)
- **資料驗證**：Zod
- **圖表**：Recharts
- **HTTP 客戶端**：Axios

## 環境設定

1. **複製環境變數範本**
   ```bash
   cp .env.example .env
   ```

2. **編輯 .env 文件**
   ```bash
   # 設定後端 API URL
   NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8080
   ```

3. **安裝依賴**
   ```bash
   npm install
   ```

## 開發

### 啟動開發伺服器
```bash
npm run dev
```

開啟瀏覽器訪問 [http://localhost:3000](http://localhost:3000)

### 建置生產版本
```bash
npm run build
npm start
```

### 類型檢查
```bash
npm run type-check
```

### Lint 檢查
```bash
npm run lint
```

## Docker 部署

### 建置映像
```bash
docker build -t arc-payroll-frontend .
```

### 執行容器
```bash
docker run -d \
  -p 3000:3000 \
  --env-file .env \
  --name arc-payroll-frontend \
  arc-payroll-frontend
```

## 頁面結構

```
src/app/
├── layout.tsx           # 根布局（導航欄）
├── page.tsx             # 首頁 - 儀表板
├── globals.css          # 全域樣式
├── batches/
│   ├── page.tsx         # 批次列表頁
│   └── [batchId]/
│       └── page.tsx     # 批次詳情頁
└── settings/
    └── page.tsx         # 設定頁
```

## API 整合

前端透過 Axios 與後端 API 通訊：

```typescript
// 範例：獲取批次列表
const response = await axios.get(
  `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}/batches`
)
```

### 主要 API 端點

- `GET /healthz` - 健康檢查
- `GET /batches` - 獲取批次列表
- `GET /batches/:batchId` - 獲取批次詳情
- `POST /admin/trigger` - 手動觸發批次
- `GET /reports/:month/reconcile` - 下載對賬報表

## 開發指南

### 組件命名規則

- **頁面組件**：使用 PascalCase（例如 `BatchListPage`）
- **UI 組件**：使用 PascalCase（例如 `StatCard`）
- **檔案名稱**：使用 kebab-case（例如 `stat-card.tsx`）

### 樣式規範

- 優先使用 Tailwind CSS utility classes
- 避免自定義 CSS（除非必要）
- 使用預設的 Design Token（定義在 `tailwind.config.ts`）

### 程式碼風格

- 使用 TypeScript strict 模式
- 遵循 ESLint 規則
- 每個函式都應有 JSDoc 註解（中文）

## 目錄結構

```
frontend/
├── src/
│   ├── app/              # Next.js App Router 頁面
│   ├── components/       # 共用組件（待建立）
│   ├── lib/              # 工具函式（待建立）
│   └── types/            # TypeScript 型別定義（待建立）
├── public/               # 靜態資源
├── .env.example          # 環境變數範本
├── Dockerfile            # Docker 建置文件
├── next.config.js        # Next.js 配置
├── tailwind.config.ts    # Tailwind CSS 配置
├── tsconfig.json         # TypeScript 配置
├── package.json          # 依賴管理
└── README.md             # 本文件
```

## 待實作功能

- [ ] 完整的批次列表頁
- [ ] 批次詳情頁（含交易紀錄）
- [ ] 報表下載功能
- [ ] 設定頁面
- [ ] 身份驗證（NextAuth）
- [ ] 錯誤處理與 Toast 通知
- [ ] Loading 狀態
- [ ] 深色模式

## License

MIT

