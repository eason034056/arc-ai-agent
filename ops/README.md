# Operations / Monitoring

This directory contains monitoring and operations-related configuration files.

## Prometheus

Prometheus is an open-source monitoring and alerting system used to collect and query Arc Payroll system metrics.

### Configuration Files

- `prometheus.yml` - Prometheus main configuration file

### Accessing Prometheus

When the backend is started using `docker-compose`, Prometheus starts automatically:

```bash
# Access Prometheus UI
http://localhost:9090
```

### Common Queries

#### HTTP Request Rate
```promql
rate(http_requests_total[5m])
```

#### Request Latency (P95)
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Agent Execution Success Rate
```promql
rate(agent_execution_total{status="success"}[5m]) / rate(agent_execution_total[5m])
```

#### Batch Processing Volume
```promql
sum(rate(batch_processed_total[1h]))
```

#### Anomaly Detection Rate
```promql
rate(anomaly_detected_total[5m]) / rate(batch_processed_total[5m])
```

## Grafana

Grafana is used to visualize metrics collected by Prometheus.

### Accessing Grafana

```bash
# Access Grafana UI
http://localhost:3000

# Default credentials
Username: admin
Password: admin
```

### Configure Data Source

1. Log in to Grafana
2. Go to Configuration → Data Sources
3. Add Prometheus data source
4. URL: `http://prometheus:9090`
5. Save and test

### Recommended Dashboards

You can import the following dashboards from the official Grafana dashboard library:

- **FastAPI Metrics**: Dashboard ID 10909
- **Prometheus Stats**: Dashboard ID 3662
- **PostgreSQL**: Dashboard ID 9628 (if using postgres_exporter)
- **Redis**: Dashboard ID 11835 (if using redis_exporter)

### Custom Dashboards

It's recommended to create custom dashboards to monitor:

1. **System Overview**
   - Batch processing volume
   - Success rate
   - Total distributed amount
   - Anomaly count

2. **Performance Metrics**
   - API request latency
   - Agent execution time
   - Transaction confirmation time

3. **Error Tracking**
   - HTTP error rate
   - Transaction failure rate
   - Anomaly detection trends

## Alert Rules (To Be Implemented)

You can create alert rules in the `alerts/` directory:

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
          summary: "High error rate detected"
          description: "{{ $labels.instance }} error rate exceeds 5%"
```

## Maintenance

### Backup Prometheus Data

```bash
docker exec arc-payroll-prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus
docker cp arc-payroll-prometheus:/tmp/prometheus-backup.tar.gz ./prometheus-backup.tar.gz
```

### Clean Old Data

Prometheus automatically cleans old data based on `storage.tsdb.retention.time` setting (default 15 days).

## Extending Monitoring

### Add PostgreSQL Monitoring

```yaml
# Add to docker-compose.yml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://user:pass@postgres:5432/arc_payroll?sslmode=disable"
  ports:
    - "9187:9187"
```

### Add Redis Monitoring

```yaml
# Add to docker-compose.yml
redis-exporter:
  image: oliver006/redis_exporter
  environment:
    REDIS_ADDR: "redis:6379"
  ports:
    - "9121:9121"
```

## License

MIT
