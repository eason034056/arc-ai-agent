# 完整工作流程节点说明

本文档详细说明工资单自动化系统从开始到结束的完整工作流程。

## 工作流程概览

```
START
  ↓
[1] ingest (数据加载)
  ↓
[2] clean (数据清理)
  ↓
[3] compute (金额计算)
  ↓
[4] detect (异常检测)
  ↓
[5] summarize (生成摘要)
  ↓
[6] propose (发送到 Slack)
  ↓
[7] approve_gate (等待批准) ← 人工审批节点
  ↓
[分支判断]
  ├─ REJECT → END
  └─ APPROVE_ALL/APPROVE_PARTIAL
        ↓
      [8] onchain (区块链交易)
        ↓
      [9] writeback (写回数据库)
        ↓
      [10] reconcile (对账)
        ↓
      END
```

---

## 节点详细说明

### 触发入口

**文件**: `backend/app/api/main.py`
- **函数**: `trigger_payroll_batch()`
- **端点**: `POST /admin/trigger?month=2025-11`
- **功能**: 接收 HTTP 请求，启动工作流
- **输入**: `month` (字符串，格式: "YYYY-MM")
- **输出**: 返回工作流执行结果

**调用链**:
```python
trigger_payroll_batch() 
  → run_payroll_workflow() 
    → create_payroll_graph() 
      → graph.compile() 
        → graph.invoke()
```

---

### 节点 1: Ingest (数据加载)

**文件**: `backend/app/agent/nodes/node_ingest.py`
- **函数**: `run(state: AgentState) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:164`

#### 功能
从数据源加载员工工资单数据

#### 输入
```python
AgentState(
    batch_id="batch_xxx",
    month="2025-11",
    lines=[],  # 空列表
    ...
)
```

#### 处理逻辑
1. 创建演示数据（5个员工）
   - 使用 Hardhat 测试账户地址
   - 每个员工有 `employee_id`, `wallet`, `name`
2. 转换为 `PayrollLineDTO` 对象
   - `amount_usdc` 初始为 0（后续计算）
   - `flags` 为空数组
3. 记录日志

#### 输出
```python
AgentState(
    batch_id="batch_xxx",
    month="2025-11",
    lines=[  # 5个 PayrollLineDTO
        PayrollLineDTO(
            employee_id="emp_001",
            wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            amount_usdc=Decimal("0"),
            flags=[],
            metadata={"name": "Alice Smith"}
        ),
        ...  # 其他4个员工
    ],
    ...
)
```

---

### 节点 2: Clean (数据清理)

**文件**: `backend/app/agent/nodes/node_clean.py`
- **函数**: `run(state: AgentState, policy: PayrollPolicy) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:171`

#### 功能
验证和清理工资单数据，移除无效条目

#### 输入
- 来自节点 1 的 `state`，包含原始员工数据

#### 处理逻辑
1. **验证钱包地址**
   - 检查格式（42字符，0x开头）
   - 检查是否为有效十六进制
2. **检测重复**
   - 检查是否有重复的钱包地址
   - 记录错误信息
3. **验证员工ID**
   - 检查是否为空
4. **过滤无效数据**
   - 移除所有验证失败的条目
   - 将错误信息添加到 `state.errors`

#### 输出
```python
AgentState(
    ...
    lines=[  # 清理后的 PayrollLineDTO 列表（可能少于输入）
        PayrollLineDTO(...),  # 只包含有效数据
        ...
    ],
    errors=[  # 如果有错误
        "Line 0: Invalid wallet address: ...",
        "Line 2: Duplicate wallet ...",
    ],
    ...
)
```

---

### 节点 3: Compute (金额计算)

**文件**: `backend/app/agent/nodes/node_compute.py`
- **函数**: `run(state: AgentState, ruleset: Dict, policy: PayrollPolicy) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:178`

#### 功能
计算每个员工的工资金额

#### 输入
- 来自节点 2 的清理后数据
- `ruleset`: 工资规则字典（base, bonus, deduction, tax_rate）

#### 处理逻辑
1. **获取默认规则集**（如果未提供）
   ```python
   {
       "base": {"emp_001": 5000, "emp_002": 6000, ...},
       "bonus": {"emp_001": 500, ...},
       "deduction": {},
       "tax_rate": 0.0
   }
   ```
2. **为每个员工计算工资**
   ```python
   amount = base + bonus - deduction - (base * tax_rate)
   ```
3. **验证金额**
   - 检查是否为负数
   - 检查是否超过最大值
4. **更新 lines**
   - 将计算后的 `amount_usdc` 写入每个 `PayrollLineDTO`

#### 输出
```python
AgentState(
    ...
    lines=[
        PayrollLineDTO(
            employee_id="emp_001",
            amount_usdc=Decimal("5500.00"),  # 已计算
            ...
        ),
        ...
    ],
    metadata={
        "total_amount": "26700.00",
        "computation_complete": True
    },
    ...
)
```

---

### 节点 4: Detect (异常检测)

**文件**: `backend/app/agent/nodes/node_detect.py`
- **函数**: `run(state: AgentState, policy: PayrollPolicy, historical_data: Dict) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:185`

#### 功能
检测工资单中的异常情况

#### 输入
- 来自节点 3 的已计算金额数据

#### 处理逻辑
1. **统计分析**
   - 计算平均值、标准差、中位数
2. **检测异常类型**
   - **Z-score 异常**: 金额偏离平均值超过 2 个标准差
   - **高金额**: 超过阈值（如 $10,000）
   - **首次支付**: 新员工首次出现在工资单中
   - **历史对比**: 与历史数据比较（如果有）
3. **添加标志**
   - 为异常项添加 `flags` 数组
   - 例如: `["HIGH_AMOUNT", "Z_SCORE_OUTLIER"]`

#### 输出
```python
AgentState(
    ...
    lines=[
        PayrollLineDTO(
            employee_id="emp_001",
            amount_usdc=Decimal("5500.00"),
            flags=["HIGH_AMOUNT"],  # 如果异常
            ...
        ),
        ...
    ],
    metadata={
        "anomaly_count": 2,
        "detection_complete": True,
        "statistics": {
            "mean": 5340.0,
            "std": 1234.5,
            "median": 5500.0
        }
    },
    ...
)
```

---

### 节点 5: Summarize (生成摘要)

**文件**: `backend/app/agent/nodes/node_summarize.py`
- **函数**: `run(state: AgentState, use_ai: bool) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:192`

#### 功能
生成工资单批次的人类可读摘要

#### 输入
- 来自节点 4 的已检测异常的数据

#### 处理逻辑
1. **计算基本统计**
   - 总金额、员工数量、异常数量
   - 平均金额、最小值、最大值
2. **部门分组**（如果有）
   - 按部门统计人数和总金额
3. **标记项目列表**
   - 收集所有有 flags 的工资单行
4. **AI 生成叙述**（可选）
   - 如果 `use_ai=True`，调用 OpenAI API 生成自然语言描述

#### 输出
```python
AgentState(
    ...
    metadata={
        "summary": {
            "month": "2025-11",
            "batch_id": "batch_xxx",
            "total_amount": "26700.00",
            "recipient_count": 5,
            "anomaly_count": 2,
            "average_amount": "5340.00",
            "min_amount": "5000.00",
            "max_amount": "6000.00",
            "department_breakdown": {...},
            "top_amounts": [...],
            "flagged_items": [...],
            "ai_narrative": "November 2025 payroll includes..."  # 可选
        },
        "summarization_complete": True
    },
    ...
)
```

---

### 节点 6: Propose (发送到 Slack)

**文件**: `backend/app/agent/nodes/node_propose.py`
- **函数**: `run(state: AgentState, slack_client) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:199`

#### 功能
将工资单摘要发送到 Slack 等待人工批准

#### 输入
- 来自节点 5 的包含摘要的数据

#### 处理逻辑
1. **格式化 Slack 卡片**
   - 使用摘要数据创建交互式 Slack 消息
   - 包含批准/拒绝按钮
2. **发送到 Slack**
   - 调用 Slack API 发送消息
   - 保存消息时间戳 (`slack_ts`)
3. **Mock 模式**（当前实现）
   - 如果 Slack 未配置，自动批准

#### 输出
```python
AgentState(
    ...
    metadata={
        "slack_ts": "1699012345.123456",  # Slack 消息时间戳
        "proposal_sent": True
    },
    ...
)
```

---

### 节点 7: Approve Gate (等待批准)

**文件**: `backend/app/agent/nodes/node_approve_gate.py`
- **函数**: `run(state: AgentState, policy: PayrollPolicy, approval_repo) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:206`

#### 功能
**阻塞等待**人工批准决策

#### 输入
- 来自节点 6 的已发送到 Slack 的数据

#### 处理逻辑
1. **轮询循环**
   - 每 5 秒检查一次数据库中的批准状态
   - 最多等待 `policy.approval_timeout_minutes` 分钟（默认 120 分钟）
2. **检查批准记录**
   - 查询数据库中的 `Approval` 表
   - 查找 `batch_id` 对应的批准决策
3. **超时处理**
   - 如果超时仍未批准，默认拒绝
4. **Mock 模式**（当前实现）
   - 自动返回 `APPROVE_ALL`

#### 输出
```python
AgentState(
    ...
    approval={
        "decision": "APPROVE_ALL",  # 或 "APPROVE_PARTIAL", "REJECT"
        "approver": "U01234567",  # Slack 用户 ID
        "timestamp": "2025-11-05T10:30:00",
        "selected_ids": [...]  # 如果是部分批准
    },
    ...
)
```

#### 路由逻辑
**文件**: `backend/app/agent/graph.py:267-294`
- 根据 `approval.decision` 决定下一步：
  - `APPROVE_ALL` 或 `APPROVE_PARTIAL` → 继续到 `onchain` 节点
  - `REJECT` 或 `PENDING` → 结束工作流

---

### 节点 8: Onchain (区块链交易)

**文件**: `backend/app/agent/nodes/node_onchain.py`
- **函数**: `run(state: AgentState, onchain_service, policy: PayrollPolicy) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:217`

#### 功能
执行区块链交易，支付员工工资

#### 输入
- 来自节点 7 的已批准数据
- `onchain_service`: 区块链服务（MockOnchainService 或 OnchainService）

#### 处理逻辑（真实模式）
1. **检查批准**
   - 必须已获得批准
2. **分块处理**
   - 将员工列表分成多个块（每块最多 50 人）
   - 避免 gas limit 问题
3. **转换金额**
   - 将 USDC 金额转换为最小单位（6 位小数）
4. **执行交易**
   - 调用 `onchain_service.batch_payout()`
   - 调用智能合约 `PayrollVault.batchPayout()`
5. **等待确认**
   - 等待交易被打包到区块
   - 获取交易哈希

#### 处理逻辑（Mock 模式 - 当前）
```python
# 直接返回假交易哈希
mock_tx_hashes = ["0xFAKE1234567890abcdef"]
```

#### 输出
```python
AgentState(
    ...
    tx_hashes=[
        "0xabc123...",  # 真实模式：区块链交易哈希
        "0xdef456..."   # 或者多个（如果分块）
    ],
    metadata={
        "onchain_complete": True,
        "transaction_count": 1
    },
    ...
)
```

---

### 节点 9: Writeback (写回数据库)

**文件**: `backend/app/agent/nodes/node_writeback.py`
- **函数**: `run(state: AgentState, webhook_client, db_repo) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:228`

#### 功能
将交易结果保存到数据库和外部系统

#### 输入
- 来自节点 8 的包含交易哈希的数据

#### 处理逻辑
1. **保存到数据库**
   - 创建或更新 `PayrollBatch` 记录
   - 保存 `PayrollLine` 记录（每个员工一行）
   - 保存 `Transaction` 记录（每个交易哈希一条）
2. **发送 Webhook**（如果配置）
   - 准备 webhook 负载
   - 发送 POST 请求到 `expense_webhook_url`
   - 通知外部费用系统
3. **错误处理**
   - 如果失败，将错误添加到 `state.errors`
   - 不中断工作流

#### 输出
```python
AgentState(
    ...
    metadata={
        "writeback_complete": True,
        "writeback_timestamp": "2025-11-05T10:35:00",
        "database_saved": True,
        "webhook_sent": True
    },
    errors=[],  # 如果有错误会添加到这里
    ...
)
```

---

### 节点 10: Reconcile (对账)

**文件**: `backend/app/agent/nodes/node_reconcile.py`
- **函数**: `run(state: AgentState, blockchain_client) -> AgentState`
- **调用位置**: `backend/app/agent/graph.py:239`

#### 功能
最终对账和生成报告

#### 输入
- 来自节点 9 的已保存数据

#### 处理逻辑
1. **计算预期值**
   - 预期总金额 = 所有 `lines` 的 `amount_usdc` 总和
   - 预期员工数量 = `lines` 的长度
2. **检查区块链交易**（如果配置）
   - 查询每个 `tx_hash` 的交易收据
   - 验证交易状态（成功/失败）
   - 解析实际支付的金额（从事件日志）
3. **对比**
   - 比较预期 vs 实际
   - 检测差异
4. **生成报告**
   - 创建对账报告 JSON
   - 标记批次状态为 `completed` 或 `failed`

#### 输出
```python
AgentState(
    ...
    metadata={
        "reconciliation_report": {
            "expected_total": "26700.00",
            "expected_count": 5,
            "actual_total": "26700.00",  # 从区块链查询
            "actual_count": 5,
            "match": True,
            "discrepancies": [],
            "tx_details": [
                {
                    "tx_hash": "0xabc123...",
                    "status": 1,  # 1=成功, 0=失败
                    "block_number": 12345,
                    "gas_used": 250000
                }
            ]
        },
        "final_status": "completed"
    },
    ...
)
```

---

## 最终返回

**文件**: `backend/app/api/main.py:221-228`

工作流完成后，API 返回：

```json
{
    "batch_id": "batch_xxx",
    "month": "2025-11",
    "status": "completed",
    "line_count": 5,
    "tx_hashes": ["0xabc123..."],
    "errors": []
}
```

---

## 状态转换图

```
AgentState (初始)
├─ batch_id: "batch_xxx"
├─ month: "2025-11"
├─ lines: []  ← 节点 1 填充
├─ approval: None  ← 节点 7 填充
├─ tx_hashes: []  ← 节点 8 填充
├─ errors: []  ← 任何节点都可能添加
└─ metadata: {}  ← 各节点逐步填充
    ├─ summary: {...}  ← 节点 5
    ├─ slack_ts: "..."  ← 节点 6
    ├─ onchain_complete: True  ← 节点 8
    ├─ writeback_complete: True  ← 节点 9
    └─ reconciliation_report: {...}  ← 节点 10
```

---

## 关键文件索引

| 节点 | 文件路径 | 主要函数 |
|------|----------|----------|
| 入口 | `backend/app/api/main.py` | `trigger_payroll_batch()` |
| 工作流定义 | `backend/app/agent/graph.py` | `create_payroll_graph()`, `run_payroll_workflow()` |
| 1. Ingest | `backend/app/agent/nodes/node_ingest.py` | `run()` |
| 2. Clean | `backend/app/agent/nodes/node_clean.py` | `run()` |
| 3. Compute | `backend/app/agent/nodes/node_compute.py` | `run()` |
| 4. Detect | `backend/app/agent/nodes/node_detect.py` | `run()` |
| 5. Summarize | `backend/app/agent/nodes/node_summarize.py` | `run()` |
| 6. Propose | `backend/app/agent/nodes/node_propose.py` | `run()` |
| 7. Approve Gate | `backend/app/agent/nodes/node_approve_gate.py` | `run()` |
| 8. Onchain | `backend/app/agent/nodes/node_onchain.py` | `run()` |
| 9. Writeback | `backend/app/agent/nodes/node_writeback.py` | `run()` |
| 10. Reconcile | `backend/app/agent/nodes/node_reconcile.py` | `run()` |

---

## 数据模型

### AgentState
定义在: `backend/app/db/schema.py:147`

```python
class AgentState(BaseModel):
    batch_id: str
    month: str
    lines: List[PayrollLineDTO]
    approval: Optional[Dict[str, Any]]
    tx_hashes: List[str]
    errors: List[str]
    metadata: Dict[str, Any]
```

### PayrollLineDTO
定义在: `backend/app/db/schema.py:32`

```python
class PayrollLineDTO(BaseModel):
    employee_id: str
    wallet: str
    amount_usdc: Decimal
    flags: List[str]
    metadata: Dict[str, Any]
```

---

## 注意事项

1. **状态不可变性**: 每个节点必须使用 `state.model_copy(update={...})` 创建新状态，不能直接修改
2. **错误收集**: 错误不会中断工作流，而是添加到 `state.errors` 中
3. **Mock 模式**: 当前开发模式下，节点 6、7、8 使用 mock 实现，跳过 Slack 和真实区块链
4. **类型安全**: 使用 `ensure_agent_state()` 确保节点间传递的状态类型正确

