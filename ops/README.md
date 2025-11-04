# Operations / Monitoring

此目錄包含系統監控和運維相關的配置文件。

## Prometheus

Prometheus 是一個開源的監控和告警系統，用於收集和查詢 Arc Payroll 系統的指標。

### 配置文件

- `prometheus.yml` - Prometheus 主配置文件

### 訪問 Prometheus

當使用 `docker-compose` 啟動後端時，Prometheus 會自動啟動：

```bash
# 訪問 Prometheus UI
http://localhost:9090
```

### 常見查詢

#### HTTP 請求率
```promql
rate(http_requests_total[5m])
```

#### 請求延遲（P95）
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Agent 執行成功率
```promql
rate(agent_execution_total{status="success"}[5m]) / rate(agent_execution_total[5m])
```

#### 批次處理量
```promql
sum(rate(batch_processed_total[1h]))
```

#### 異常偵測率
```promql
rate(anomaly_detected_total[5m]) / rate(batch_processed_total[5m])
```

## Grafana

Grafana 用於視覺化 Prometheus 收集的指標。

### 訪問 Grafana

```bash
# 訪問 Grafana UI
http://localhost:3000

# 預設帳號
Username: admin
Password: admin
```

### 配置資料源

1. 登入 Grafana
2. 進入 Configuration → Data Sources
3. 新增 Prometheus 資料源
4. URL: `http://prometheus:9090`
5. 儲存並測試

### 建議的儀表板

可以從 Grafana 官方儀表板庫匯入以下儀表板：

- **FastAPI Metrics**: Dashboard ID 10909
- **Prometheus Stats**: Dashboard ID 3662
- **PostgreSQL**: Dashboard ID 9628 (如果使用 postgres_exporter)
- **Redis**: Dashboard ID 11835 (如果使用 redis_exporter)

### 自訂儀表板

建議創建自訂儀表板來監控：

1. **系統總覽**
   - 批次處理量
   - 成功率
   - 總發放金額
   - 異常數量

2. **效能指標**
   - API 請求延遲
   - Agent 執行時間
   - 交易確認時間

3. **錯誤追蹤**
   - HTTP 錯誤率
   - 交易失敗率
   - 異常偵測趨勢

## 告警規則（待實作）

可以在 `alerts/` 目錄下創建告警規則：

```yaml
# alerts/backend.yml
groups:
  - name: backend_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高錯誤率偵測"
          description: "{{ $labels.instance }} 錯誤率超過 5%"
```

## 維護

### 備份 Prometheus 資料

```bash
docker exec arc-payroll-prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus
docker cp arc-payroll-prometheus:/tmp/prometheus-backup.tar.gz ./prometheus-backup.tar.gz
```

### 清理舊資料

Prometheus 會根據 `storage.tsdb.retention.time` 設定自動清理舊資料（預設 15 天）。

## 擴展監控

### 添加 PostgreSQL 監控

```yaml
# 在 docker-compose.yml 中添加
postgres-exporter:
  image: prometheuscommunity/postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://user:pass@postgres:5432/arc_payroll?sslmode=disable"
  ports:
    - "9187:9187"
```

### 添加 Redis 監控

```yaml
# 在 docker-compose.yml 中添加
redis-exporter:
  image: oliver006/redis_exporter
  environment:
    REDIS_ADDR: "redis:6379"
  ports:
    - "9121:9121"
```

## License

MIT

