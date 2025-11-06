# 前端开发流程与架构

## 📋 目录结构

```
frontend/src/
├── app/                    # Next.js App Router 页面
│   ├── layout.tsx         # ✅ 根布局（已完成）
│   ├── page.tsx           # ✅ 首页 Dashboard（基础版）
│   ├── globals.css        # ✅ 全局样式
│   ├── batches/           # ⏳ 批次管理页面
│   │   ├── page.tsx       # 批次列表页
│   │   └── [batchId]/     # 批次详情页
│   │       └── page.tsx
│   └── settings/          # ⏳ 设置页面
│       └── page.tsx
│
├── components/            # 📦 可复用组件
│   ├── ui/               # 基础 UI 组件
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Table.tsx
│   │   ├── Badge.tsx
│   │   └── Loading.tsx
│   ├── layout/           # 布局组件
│   │   ├── Navbar.tsx
│   │   └── Sidebar.tsx
│   └── features/         # 功能组件
│       ├── BatchCard.tsx
│       ├── BatchList.tsx
│       ├── BatchDetail.tsx
│       ├── TransactionTable.tsx
│       └── StatsCard.tsx
│
├── lib/                  # 🔧 工具函数和配置
│   ├── api/             # API 客户端
│   │   ├── client.ts    # Axios 实例
│   │   ├── batches.ts   # 批次相关 API
│   │   ├── reports.ts   # 报告相关 API
│   │   └── admin.ts     # 管理相关 API
│   ├── types/           # TypeScript 类型定义
│   │   ├── batch.ts
│   │   ├── transaction.ts
│   │   └── api.ts
│   └── utils/           # 工具函数
│       ├── format.ts    # 格式化函数（金额、日期等）
│       └── validation.ts # 验证函数
│
└── hooks/               # 🎣 React Hooks
    ├── useBatches.ts
    ├── useBatch.ts
    └── useTrigger.ts
```

## 🎯 开发流程

### 阶段 1: 基础架构搭建（优先级：高）

#### 1.1 创建 API 客户端
- [ ] 创建 `lib/api/client.ts` - Axios 实例配置
- [ ] 创建 `lib/api/batches.ts` - 批次相关 API 函数
- [ ] 创建 `lib/api/reports.ts` - 报告相关 API 函数
- [ ] 创建 `lib/api/admin.ts` - 管理相关 API 函数

#### 1.2 创建 TypeScript 类型定义
- [ ] 创建 `lib/types/batch.ts` - 批次相关类型
- [ ] 创建 `lib/types/transaction.ts` - 交易相关类型
- [ ] 创建 `lib/types/api.ts` - API 响应类型

#### 1.3 配置 React Query
- [ ] 在 `app/layout.tsx` 中添加 QueryClientProvider
- [ ] 配置 React Query 的默认选项

### 阶段 2: 基础 UI 组件（优先级：高）

#### 2.1 创建基础组件
- [ ] `components/ui/Button.tsx` - 按钮组件
- [ ] `components/ui/Card.tsx` - 卡片组件
- [ ] `components/ui/Badge.tsx` - 徽章组件（用于状态显示）
- [ ] `components/ui/Loading.tsx` - 加载状态组件
- [ ] `components/ui/Table.tsx` - 表格组件

#### 2.2 创建功能组件
- [ ] `components/features/StatsCard.tsx` - 统计卡片（Dashboard 用）
- [ ] `components/features/BatchCard.tsx` - 批次卡片

### 阶段 3: Dashboard 页面完善（优先级：高）

#### 3.1 集成真实数据
- [ ] 使用 React Query 获取批次统计数据
- [ ] 替换硬编码的数据
- [ ] 添加加载和错误状态处理

#### 3.2 添加图表
- [ ] 使用 Recharts 创建月度趋势图
- [ ] 添加成功率和异常率图表

### 阶段 4: 批次管理页面（优先级：中）

#### 4.1 批次列表页 (`app/batches/page.tsx`)
- [ ] 创建批次列表页面
- [ ] 实现筛选功能（按月份、状态）
- [ ] 实现分页功能
- [ ] 添加批次搜索功能

#### 4.2 批次详情页 (`app/batches/[batchId]/page.tsx`)
- [ ] 创建批次详情页面
- [ ] 显示批次基本信息
- [ ] 显示批次中的所有员工记录
- [ ] 显示区块链交易信息
- [ ] 添加交易状态实时更新

### 阶段 5: 设置页面（优先级：低）

#### 5.1 系统设置 (`app/settings/page.tsx`)
- [ ] 创建设置页面
- [ ] 显示系统配置信息
- [ ] 添加配置修改功能（如果需要）

### 阶段 6: 优化和增强（优先级：低）

- [ ] 添加错误处理和 Toast 通知
- [ ] 添加加载骨架屏
- [ ] 优化移动端响应式设计
- [ ] 添加数据刷新功能
- [ ] 添加导出功能（CSV 下载）

## 🔧 技术栈

- **框架**: Next.js 15 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **状态管理**: TanStack Query (React Query)
- **HTTP 客户端**: Axios
- **数据验证**: Zod
- **图表**: Recharts
- **UI 组件**: 自定义组件（基于 Tailwind）

## 📝 API 端点映射

### 批次相关
- `GET /batches` - 获取批次列表
- `GET /batches/{batch_id}` - 获取批次详情
- `POST /admin/trigger?month=YYYY-MM` - 触发新批次

### 报告相关
- `GET /reports/{month}/reconcile?format=json|csv` - 获取对账报告

### 系统相关
- `GET /healthz` - 健康检查
- `GET /metrics` - Prometheus 指标

## 🎨 设计规范

### 颜色系统
- **Primary**: `primary-600` (蓝色) - 主要操作按钮
- **Success**: `green-600` - 成功状态
- **Warning**: `orange-600` - 警告状态
- **Error**: `red-600` - 错误状态
- **Info**: `blue-600` - 信息提示

### 状态显示
- **Draft**: 灰色徽章
- **Pending Approval**: 黄色徽章
- **Approved**: 蓝色徽章
- **Processing**: 蓝色徽章 + 加载动画
- **Completed**: 绿色徽章
- **Failed**: 红色徽章
- **Rejected**: 红色徽章

### 布局规范
- **最大宽度**: `max-w-7xl` (1280px)
- **间距**: 使用 Tailwind 的间距系统（4px 倍数）
- **卡片圆角**: `rounded-lg` (8px)
- **阴影**: `shadow` (默认) / `shadow-lg` (悬停)

## 🚀 开始开发

### 1. 安装依赖
```bash
cd frontend
npm install
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env，设置 NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8080
```

### 3. 启动开发服务器
```bash
npm run dev
```

### 4. 访问应用
打开浏览器访问 http://localhost:3000

## 📚 开发建议

1. **先搭建基础架构**：先创建 API 客户端和类型定义，确保类型安全
2. **组件化开发**：将 UI 拆分成可复用的小组件
3. **数据获取**：使用 React Query 进行数据获取和缓存管理
4. **错误处理**：统一处理 API 错误，提供友好的错误提示
5. **加载状态**：所有异步操作都要有加载状态显示
6. **响应式设计**：使用 Tailwind 的响应式类，确保移动端友好

