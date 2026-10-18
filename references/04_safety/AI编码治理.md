# AI 编码治理

> AI 写代码不是 IF，是 WHEN。WHEN 之后**必须有治理**——不然是负债不是杠杆。

## 三件必做的事

1. **每条 AI 写的代码都有作者**：commit 里标 `Co-authored-by: Cursor/Claude/...`，reviewer 知道这段是 AI 输出
2. **每段 AI 输出都要走和人类代码同等 review**：不因为"AI 写的"就放水，也不因为"AI 写的"就刁难
3. **每段 AI 输出都要被测试覆盖**：没有测试的 AI 代码 = 高风险代码

## AI 代码的"高风险三类"

### 1. 安全类（认证、密码、支付、风控）
- 不让 AI 直接改这些代码
- AI 写其他模块时若涉及这些 → 强制人工 review + 加测试 + 加监控

### 2. 不可逆操作（删数据、merge PR、commit、push 镜像）
- AI agent 操作前后必须有 diff 让人类点确认
- 关键操作（删库、关流量、合并主线）→ **永远要二次确认**

### 3. 跨越多模块的"重构"
- AI 容易大规模动文件
- 一个 PR 改 > 20 个文件 → 强拆 PR

## AI Agent 的"工具使用规范"

| 行为 | 规范 |
|---|---|
| 跑 shell 命令 | 必须白名单 / dry-run / 用户确认 |
| 写文件 | 不写到用户未授权路径 |
| 联网 | 走代理，URL 白名单 |
| 调用工具 | 每个工具有 schema 验证，超出 schema 自动拒 |
| 长 session | 每 N 分钟做 summary 防止 context 漂移 |

## Cursor / Copilot / Claude Code 等的规则配置

存仓库根目录 `.cursorrules` 或 `.clauderules`，写：

```
# 项目级 AI 规则
- 先读 README.md 再生成
- 不要触碰 src/auth/** src/payments/**
- 单 PR 不超过 400 行
- 任何 commit message 用中文/英文，按团队规范
- 测试覆盖率不许降
- 不要自动 push，必须本地 commit 后由人合并
```

## Agent 输出审计

每个 agent session 结束后：

- [ ] 改了哪些文件？diff 总行数
- [ ] 调用了哪些外部工具/网络？
- [ ] 测试是否仍绿？
- [ ] 是否动了风控/支付/认证相关？
- [ ] 是否有未提交的临时文件？

## AI 编码的"红线"

- 不得让 AI 自己 merge PR 到 main
- 不得让 AI 改 .github/、CI、密钥、IaC
- 不得让 AI 直接 deploy 到生产
- 不得让 AI 跨 PR 重构数据库 schema（必须人手）

## 出问题时追溯链

```
事故 → 这段代码来自哪个 PR → 哪个 PR 来自哪个 AI session → 哪个 session 由谁启动
                                                  ↓
                                          谁点了 confirm
```

把所有环节写入 audit log。事故问责时，AI 不背锅，**最终点头的人**背锅。

## 治理的常见误区

- ❌ "AI 写的代码错了是 AI 的问题" → AI 是工具，责任人是你
- ❌ "完全禁用 AI" → 越禁越落后，要治理不是禁
- ❌ "越快就越好" → 跳过 review 是把债挪到未来
