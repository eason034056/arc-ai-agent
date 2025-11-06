# ============================================
# Arc Payroll System - Makefile
# Provides one-click commands to manage the entire system
# ============================================

.PHONY: help backend-up backend-down backend-migrate backend-seed \
        frontend-dev frontend-up frontend-down \
        contracts-install contracts-compile contracts-deploy \
        up-all down-all logs clean

# Default target: Display help message
help:
	@echo "=========================================="
	@echo "Arc Payroll System - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Backend Commands:"
	@echo "  make backend-up        - Start backend services (Docker Compose)"
	@echo "  make backend-down      - Stop backend services"
	@echo "  make backend-migrate   - Run database migrations"
	@echo "  make backend-seed      - Seed test data"
	@echo "  make backend-logs      - View backend logs"
	@echo ""
	@echo "Frontend Commands:"
	@echo "  make frontend-dev      - Start frontend dev server"
	@echo "  make frontend-up       - Build and start frontend (Docker)"
	@echo "  make frontend-down     - Stop frontend container"
	@echo ""
	@echo "Contract Commands:"
	@echo "  make contracts-install - Install contract dependencies"
	@echo "  make contracts-compile - Compile smart contracts"
	@echo "  make contracts-deploy  - Deploy contracts to Arc Testnet"
	@echo ""
	@echo "Integration Commands:"
	@echo "  make up-all            - Start backend and frontend"
	@echo "  make down-all          - Stop all services"
	@echo "  make logs              - View all logs"
	@echo "  make clean             - Clean all containers and data"
	@echo "=========================================="

# ============================================
# Backend Commands
# ============================================

# Start backend services (Postgres, Redis, App, Prometheus, Grafana)
backend-up:
	@echo "🚀 Starting backend services..."
	cd backend && docker compose up -d --build
	@echo "✅ Backend services started"
	@echo "   - API: http://localhost:8080"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3001"

# Stop backend services
backend-down:
	@echo "🛑 Stopping backend services..."
	cd backend && docker compose down
	@echo "✅ Backend services stopped"

# Run database migrations
backend-migrate:
	@echo "📦 Running database migrations..."
	cd backend && docker compose exec app alembic upgrade head
	@echo "✅ Migrations complete"

# Seed test data
backend-seed:
	@echo "🌱 Seeding test data..."
	cd backend && docker compose exec app python scripts/seed_demo.py
	@echo "✅ Test data seeded"

# View backend logs
backend-logs:
	cd backend && docker compose logs -f app

# ============================================
# Frontend Commands
# ============================================

# Start frontend development server (local)
frontend-dev:
	@echo "🎨 Starting frontend dev server..."
	cd frontend && npm install && npm run dev

# Build and start frontend (Docker)
frontend-up:
	@echo "🚀 Building and starting frontend..."
	cd frontend && docker build -t arc-payroll-frontend .
	docker run -d -p 3000:3000 \
		--env-file frontend/.env \
		--name arc-payroll-frontend \
		--network arc-ai-agent_default \
		arc-payroll-frontend
	@echo "✅ Frontend started: http://localhost:3000"

# Stop frontend container
frontend-down:
	@echo "🛑 Stopping frontend container..."
	docker stop arc-payroll-frontend || true
	docker rm arc-payroll-frontend || true
	@echo "✅ Frontend stopped"

# ============================================
# Contract Commands
# ============================================

# Install contract dependencies
contracts-install:
	@echo "📦 Installing contract dependencies..."
	cd contracts && npm install
	@echo "✅ Dependencies installed"

# Compile smart contracts
contracts-compile:
	@echo "🔨 Compiling smart contracts..."
	cd contracts && npx hardhat compile
	@echo "✅ Contracts compiled"

# Deploy contracts to Arc Testnet
contracts-deploy:
	@echo "🚀 Deploying contracts to Arc Testnet..."
	cd contracts && npx hardhat run scripts/deploy.ts --network arcTestnet
	@echo "✅ Contracts deployed"
	@echo "⚠️  Please update PAYROLL_CONTRACT_ADDRESS in backend/.env"

# ============================================
# Integration Commands
# ============================================

# Start all services (backend + frontend)
up-all: backend-up frontend-up
	@echo ""
	@echo "=========================================="
	@echo "🎉 All services started!"
	@echo "=========================================="
	@echo "Backend API: http://localhost:8080"
	@echo "Frontend UI:  http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3001"
	@echo "=========================================="

# Stop all services
down-all: backend-down frontend-down
	@echo "✅ All services stopped"

# View all logs
logs:
	cd backend && docker compose logs -f

# Clean all containers, images and data
clean:
	@echo "🧹 Cleaning all containers and data..."
	@read -p "⚠️  This will delete all containers, images and volumes. Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd backend && docker compose down -v --rmi all || true; \
		docker stop arc-payroll-frontend || true; \
		docker rm arc-payroll-frontend || true; \
		docker rmi arc-payroll-frontend || true; \
		echo "✅ Cleanup complete"; \
	else \
		echo "❌ Cleanup cancelled"; \
	fi

# ============================================
# Development Helper Commands
# ============================================

# Enter backend container shell
backend-shell:
	cd backend && docker compose exec app /bin/bash

# Run backend tests
backend-test:
	cd backend && docker compose exec app pytest

# Run frontend type check
frontend-type-check:
	cd frontend && npm run type-check

# Run frontend lint
frontend-lint:
	cd frontend && npm run lint

# ============================================
# Quick Start (for first-time users)
# ============================================

# Initial setup
setup:
	@echo "🎯 Initial setup..."
	@echo ""
	@echo "1️⃣ Setup backend environment variables"
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "   ✅ Created backend/.env, please edit and fill in correct values"; \
	else \
		echo "   ⚠️  backend/.env already exists"; \
	fi
	@echo ""
	@echo "2️⃣ Setup frontend environment variables"
	@if [ ! -f frontend/.env ]; then \
		cp frontend/.env.example frontend/.env; \
		echo "   ✅ Created frontend/.env"; \
	else \
		echo "   ⚠️  frontend/.env already exists"; \
	fi
	@echo ""
	@echo "3️⃣ Setup contract environment variables"
	@if [ ! -f contracts/.env ]; then \
		cp contracts/.env.example contracts/.env; \
		echo "   ✅ Created contracts/.env, please edit and fill in correct values"; \
	else \
		echo "   ⚠️  contracts/.env already exists"; \
	fi
	@echo ""
	@echo "4️⃣ Install dependencies"
	@$(MAKE) contracts-install
	@echo ""
	@echo "=========================================="
	@echo "✅ Setup complete!"
	@echo "=========================================="
	@echo "Next steps:"
	@echo "  1. Edit backend/.env and contracts/.env"
	@echo "  2. Run 'make contracts-compile' to compile contracts"
	@echo "  3. Run 'make contracts-deploy' to deploy contracts"
	@echo "  4. Run 'make up-all' to start all services"
	@echo "=========================================="

# Quick restart (for development)
restart: down-all up-all

# View system status
status:
	@echo "=========================================="
	@echo "System Status"
	@echo "=========================================="
	@echo "Backend containers:"
	@cd backend && docker compose ps || echo "  Not started"
	@echo ""
	@echo "Frontend container:"
	@docker ps | grep arc-payroll-frontend || echo "  Not started"
	@echo "=========================================="
