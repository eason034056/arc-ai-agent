# ============================================
# Stage 1: 安裝依賴
# ============================================
FROM node:20-alpine AS deps

WORKDIR /app

# 複製 package 文件
COPY package.json package-lock.json* pnpm-lock.yaml* ./

# 安裝依賴
RUN \
  if [ -f pnpm-lock.yaml ]; then \
    corepack enable && pnpm install --frozen-lockfile; \
  elif [ -f package-lock.json ]; then \
    npm ci; \
  else \
    npm install; \
  fi

# ============================================
# Stage 2: 建置應用
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# 從 deps 複製 node_modules
COPY --from=deps /app/node_modules ./node_modules

# 複製原始碼
COPY . .

# 設定環境變數（建置時）
ENV NEXT_TELEMETRY_DISABLED 1

# 建置 Next.js 應用
RUN npm run build

# ============================================
# Stage 3: 執行應用
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

# 設定生產環境
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED 1

# 建立非 root 使用者
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 複製必要文件
COPY --from=builder /app/public ./public

# 設定正確的權限
RUN mkdir .next && chown nextjs:nodejs .next

# 複製建置產物
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切換到非 root 使用者
USER nextjs

# 暴露端口
EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# 啟動應用
CMD ["node", "server.js"]

