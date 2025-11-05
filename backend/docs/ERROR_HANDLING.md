# 错误处理策略文档

本文档说明系统实现的错误处理机制，确保工作流的健壮性和优雅降级。

## 🛡️ 三层错误保护

### 1. 节点级别保护（Node-Level Protection）

每个节点函数内部都有 try/except 保护层。

**示例**：`node_ingest.py`, `node_compute.py`

```python
def run(state: AgentState) -> AgentState:
    try:
        # === Core logic ===
        # ... 节点主要逻辑 ...
        return new_state
    except Exception as e:
        logger.error(
            "[Error in node_xxx]",
            extra={
                "batch_id": state.batch_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        # 返回带错误的状态，不中断工作流
        errors = list(state.errors) + [f"node_xxx: {str(e)}"]
        return state.model_copy(update={"errors": errors})
```

**优点**：
- 节点内部错误不会传播
- 错误信息统一记录到 `state.errors`
- 工作流继续执行

---

### 2. 装饰器级别保护（Decorator-Level Protection）

**文件**: `backend/app/agent/utils.py`

所有节点都通过 `safe_node` 装饰器包装，提供统一的错误处理。

```python
from app.agent.utils import safe_node

@safe_node
def run(state: AgentState) -> AgentState:
    # 节点逻辑
    return new_state
```

**功能**：
- 自动捕获所有异常
- 记录节点执行日志（开始/完成/失败）
- 将错误添加到 `state.errors`
- 在 metadata 中标记失败的节点
- 即使出错也返回状态（不中断工作流）

**应用位置**: `backend/app/agent/graph.py`

所有节点都使用 `safe_node` 装饰器：

```python
graph.add_node(
    "compute",
    safe_node(lambda state: node_compute.run(ensure_agent_state(state), ...))
)
```

**日志输出示例**：
```
[Node: node_compute] Starting...
[Node: node_compute] ✅ Completed successfully
```

或出错时：
```
[Node: node_compute] ❌ Failed: Division by zero
```

---

### 3. 数据库优雅降级（Database Graceful Degradation）

**文件**: `backend/app/agent/nodes/node_writeback.py`

数据库操作失败时使用 WARNING 级别日志，而不是 ERROR。

```python
try:
    save_batch_to_database(state)
except Exception as e:
    # 使用 WARNING 级别（优雅降级）
    logger.warning(
        "[DB WARN] Direct database save failed",
        extra={
            "batch_id": state.batch_id,
            "error": str(e),
            "error_type": type(e).__name__
        },
        exc_info=True
    )
    error_msg = f"db_save: {str(e)}"
    errors.append(error_msg)
    # 不抛出异常，让工作流继续
```

**分级策略**：
- **WARNING**: 数据库保存失败（非关键操作）
- **ERROR**: 核心业务逻辑失败（金额计算、交易执行等）
- **INFO**: 正常流程日志

---

## 📊 错误收集流程

```
节点执行
  ↓
[节点内部 try/except]
  ├─ 成功 → 返回新状态
  └─ 失败 → 添加到 state.errors，返回原状态
  ↓
[safe_node 装饰器]
  ├─ 成功 → 记录日志，返回状态
  └─ 失败 → 记录日志，添加到 state.errors，返回状态
  ↓
工作流继续执行下一个节点
  ↓
最终返回
  ├─ state.errors: 所有错误列表
  └─ state.metadata: 包含失败节点标记
```

---

## 🔍 错误查看

### API 响应

```json
{
    "batch_id": "batch_xxx",
    "month": "2025-11",
    "status": "completed",
    "line_count": 5,
    "tx_hashes": ["0xabc123..."],
    "errors": [
        "node_compute: Division by zero",
        "db_save: Connection timeout"
    ]
}
```

### 日志文件

所有错误都会记录到日志，包含：
- 错误类型
- 错误消息
- 完整堆栈跟踪（`exc_info=True`）
- 批次ID和上下文信息

---

## ✅ 实现的优势

1. **工作流不中断**: 即使某个节点失败，后续节点仍会执行
2. **错误可追踪**: 所有错误统一收集到 `state.errors`
3. **优雅降级**: 非关键操作失败不影响整体流程
4. **详细日志**: 每个错误都有完整的上下文信息
5. **用户友好**: API 返回所有错误，用户可以查看详情

---

## 📝 最佳实践

### 何时使用 try/except

✅ **应该**在节点函数内部使用：
- 数据处理逻辑
- 外部服务调用（数据库、API）
- 计算密集型操作

✅ **应该**在装饰器层使用：
- 所有节点函数（已通过 `safe_node` 实现）

### 何时记录为 WARNING vs ERROR

- **WARNING**: 非关键操作失败（数据库保存、webhook 通知）
- **ERROR**: 核心业务逻辑失败（金额计算、交易执行、数据验证）

### 错误消息格式

统一格式：`{node_name}: {error_message}`

示例：
- `ingest: Connection timeout`
- `compute: Division by zero`
- `db_save: Invalid keyword argument`

---

## 🔧 未来改进

1. **错误重试机制**: 对于临时性错误（网络超时），自动重试
2. **错误分类**: 区分可恢复错误和不可恢复错误
3. **告警系统**: 关键错误发送告警通知
4. **错误恢复**: 支持从失败点继续执行

