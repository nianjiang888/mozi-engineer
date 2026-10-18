# Spec 驱动开发（SDD）

> 先讲清楚要做什么，再讨论怎么做。

## 三层 Spec 模型

| 层 | 关注 | 输出形态 |
|---|---|---|
| **Why** | 业务目标/非目标 | 一段叙述，最多 5 行 |
| **What** | 用户故事/验收标准 | Given/When/Then 或 DoD 清单 |
| **How** | 接口契约/状态机/数据模型 | OpenAPI / protobuf / ER 图 |

三层都要**有且可改**：方向错了，三层都得改。

## 写 Spec 的硬约束

- **可测试**：每个验收条件有可二值化（pass/fail）的判据
- **可独立交付**：一个 PR 范围对应一组验收条件
- **可回滚**：每个 Spec 对应有一个 kill switch（feature flag、灰度路由、白名单）
- **可比对**：评估方案时列 A/B 各自的取舍，不能只说"用 X 更好"

## 接口约定的最小单元

```
EndPoint: POST /v1/orders
Auth:    Bearer (user JWT)
Req:     { sku_id: string, qty: int(1..99), address_id: uuid }
Resp:    201 { order_id, total_cents, pay_url }
Err:     400 INVALID_QTY / 410 SKU_OOS / 402 INSUFFICIENT_FUNDS
```

**错误码要稳定**：前端、C端、客服、监控都靠这套错误码定位。定义一次，所有层复用。

## From Spec → Task → Code 的工作流

1. Spec 在 `docs/specs/<feature>.md`，验收条件可勾
2. 拆成 `tasks/<feature>-T1.md T2.md...`，每条任务 ≤ 2 人天
3. 每个任务对应一个 branch + PR，PR 模板自动勾验收条件
4. 合并后回到 Spec 文档，把"已完成"打勾

## Spec 反模式（看见就跑）

- 模糊词："大概"、"差不多"、"原则上"、"可能"
- 不可测："性能好一点"、"用户友好"、"差不多能用"
- 范围漂移："顺带加一下 X"、"不算大改动"、"顺便优化"
- 与代码脱节：改了代码没回写 Spec → 文档腐烂根因
