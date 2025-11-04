# Database Migrations

此目錄包含 Alembic 資料庫遷移腳本。

## 初始化 Alembic

```bash
alembic init migrations
```

## 創建新遷移

```bash
alembic revision --autogenerate -m "description"
```

## 執行遷移

```bash
alembic upgrade head
```

## 回滾遷移

```bash
alembic downgrade -1
```

