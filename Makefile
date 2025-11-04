# ============================================
# Arc Payroll System - Makefile
# 提供一鍵指令來管理整個系統
# ============================================

.PHONY: help backend-up backend-down backend-migrate backend-seed \
        frontend-dev frontend-up frontend-down \
        contracts-install contracts-compile contracts-deploy \
        up-all down-all logs clean

# 預設目標：顯示幫助訊息
help:
	@echo "=========================================="
	@echo "Arc Payroll System - 可用指令"
	@echo "=========================================="
	@echo ""
	@echo "後端指令:"
	@echo "  make backend-up        - 啟動後端服務 (Docker Compose)"
	@echo "  make backend-down      - 停止後端服務"
	@echo "  make backend-migrate   - 執行資料庫遷移"
	@echo "  make backend-seed      - 填充測試資料"
	@echo "  make backend-logs      - 查看後端日誌"
	@echo ""
	@echo "前端指令:"
	@echo "  make frontend-dev      - 啟動前端開發伺服器"
	@echo "  make frontend-up       - 建置並啟動前端 (Docker)"
	@echo "  make frontend-down     - 停止前端容器"
	@echo ""
	@echo "合約指令:"
	@echo "  make contracts-install - 安裝合約依賴"
	@echo "  make contracts-compile - 編譯智慧合約"
	@echo "  make contracts-deploy  - 部署合約到 Arc Testnet"
	@echo ""
	@echo "整合指令:"
	@echo "  make up-all            - 啟動後端和前端"
	@echo "  make down-all          - 停止所有服務"
	@echo "  make logs              - 查看所有日誌"
	@echo "  make clean             - 清理所有容器和資料"
	@echo "=========================================="

# ============================================
# 後端指令
# ============================================

# 啟動後端服務（Postgres, Redis, App, Prometheus, Grafana）
backend-up:
	@echo "🚀 啟動後端服務..."
	cd backend && docker compose up -d --build
	@echo "✅ 後端服務已啟動"
	@echo "   - API: http://localhost:8080"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000"

# 停止後端服務
backend-down:
	@echo "🛑 停止後端服務..."
	cd backend && docker compose down
	@echo "✅ 後端服務已停止"

# 執行資料庫遷移
backend-migrate:
	@echo "📦 執行資料庫遷移..."
	cd backend && docker compose exec app alembic upgrade head
	@echo "✅ 遷移完成"

# 填充測試資料
backend-seed:
	@echo "🌱 填充測試資料..."
	cd backend && docker compose exec app python scripts/seed_demo.py
	@echo "✅ 測試資料已填充"

# 查看後端日誌
backend-logs:
	cd backend && docker compose logs -f app

# ============================================
# 前端指令
# ============================================

# 啟動前端開發伺服器（本地）
frontend-dev:
	@echo "🎨 啟動前端開發伺服器..."
	cd frontend && npm install && npm run dev

# 建置並啟動前端（Docker）
frontend-up:
	@echo "🚀 建置並啟動前端..."
	cd frontend && docker build -t arc-payroll-frontend .
	docker run -d -p 3000:3000 \
		--env-file frontend/.env \
		--name arc-payroll-frontend \
		--network arc-ai-agent_default \
		arc-payroll-frontend
	@echo "✅ 前端已啟動: http://localhost:3000"

# 停止前端容器
frontend-down:
	@echo "🛑 停止前端容器..."
	docker stop arc-payroll-frontend || true
	docker rm arc-payroll-frontend || true
	@echo "✅ 前端已停止"

# ============================================
# 合約指令
# ============================================

# 安裝合約依賴
contracts-install:
	@echo "📦 安裝合約依賴..."
	cd contracts && npm install
	@echo "✅ 依賴安裝完成"

# 編譯智慧合約
contracts-compile:
	@echo "🔨 編譯智慧合約..."
	cd contracts && npx hardhat compile
	@echo "✅ 合約編譯完成"

# 部署合約到 Arc Testnet
contracts-deploy:
	@echo "🚀 部署合約到 Arc Testnet..."
	cd contracts && npx hardhat run scripts/deploy.ts --network arcTestnet
	@echo "✅ 合約部署完成"
	@echo "⚠️  請更新 backend/.env 中的 PAYROLL_CONTRACT_ADDRESS"

# ============================================
# 整合指令
# ============================================

# 啟動所有服務（後端 + 前端）
up-all: backend-up frontend-up
	@echo ""
	@echo "=========================================="
	@echo "🎉 所有服務已啟動！"
	@echo "=========================================="
	@echo "後端 API: http://localhost:8080"
	@echo "前端 UI:  http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3000 (Grafana port conflicts with frontend)"
	@echo "=========================================="

# 停止所有服務
down-all: backend-down frontend-down
	@echo "✅ 所有服務已停止"

# 查看所有日誌
logs:
	cd backend && docker compose logs -f

# 清理所有容器、映像和資料
clean:
	@echo "🧹 清理所有容器和資料..."
	@read -p "⚠️  這將刪除所有容器、映像和 volume。確定嗎？ [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd backend && docker compose down -v --rmi all || true; \
		docker stop arc-payroll-frontend || true; \
		docker rm arc-payroll-frontend || true; \
		docker rmi arc-payroll-frontend || true; \
		echo "✅ 清理完成"; \
	else \
		echo "❌ 取消清理"; \
	fi

# ============================================
# 開發輔助指令
# ============================================

# 進入後端容器的 shell
backend-shell:
	cd backend && docker compose exec app /bin/bash

# 執行後端測試
backend-test:
	cd backend && docker compose exec app pytest

# 執行前端類型檢查
frontend-type-check:
	cd frontend && npm run type-check

# 執行前端 lint
frontend-lint:
	cd frontend && npm run lint

# ============================================
# 快速開始（適合首次使用）
# ============================================

# 首次設定
setup:
	@echo "🎯 首次設定..."
	@echo ""
	@echo "1️⃣ 設定後端環境變數"
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "   ✅ 已創建 backend/.env，請編輯並填入正確的值"; \
	else \
		echo "   ⚠️  backend/.env 已存在"; \
	fi
	@echo ""
	@echo "2️⃣ 設定前端環境變數"
	@if [ ! -f frontend/.env ]; then \
		cp frontend/.env.example frontend/.env; \
		echo "   ✅ 已創建 frontend/.env"; \
	else \
		echo "   ⚠️  frontend/.env 已存在"; \
	fi
	@echo ""
	@echo "3️⃣ 設定合約環境變數"
	@if [ ! -f contracts/.env ]; then \
		cp contracts/.env.example contracts/.env; \
		echo "   ✅ 已創建 contracts/.env，請編輯並填入正確的值"; \
	else \
		echo "   ⚠️  contracts/.env 已存在"; \
	fi
	@echo ""
	@echo "4️⃣ 安裝依賴"
	@$(MAKE) contracts-install
	@echo ""
	@echo "=========================================="
	@echo "✅ 設定完成！"
	@echo "=========================================="
	@echo "下一步："
	@echo "  1. 編輯 backend/.env 和 contracts/.env"
	@echo "  2. 執行 'make contracts-compile' 編譯合約"
	@echo "  3. 執行 'make contracts-deploy' 部署合約"
	@echo "  4. 執行 'make up-all' 啟動所有服務"
	@echo "=========================================="

# 快速重啟（開發時使用）
restart: down-all up-all

# 查看系統狀態
status:
	@echo "=========================================="
	@echo "系統狀態"
	@echo "=========================================="
	@echo "後端容器："
	@cd backend && docker compose ps || echo "  未啟動"
	@echo ""
	@echo "前端容器："
	@docker ps | grep arc-payroll-frontend || echo "  未啟動"
	@echo "=========================================="

