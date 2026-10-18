# FAQ · 墨子·工程指挥官

## 1. 与 dev-expert 的主要差异？

详见 README。但最关键一点：**dev-expert 64 个文件平铺**，每次调用模型要自己挑（常常挑错或不全）；本包 19 文件 + 引擎精准 Top-3，**每次只灌进最相关的 3 篇 knowledge**。

## 2. 为什么不直接复制 dev-expert 的 17 个 hooks？

dev-expert 的 hooks 是文件级防御（pre-commit + 文件系统级），需要 `install_hooks.py` 装到 git hook 里才能起效；本包聚焦 **LLM 交互层防线**（prompt 注入/secret/License），即时可用、不挑环境。 文件级 hooks 属于生态范畴，未来按用户反馈再加。

## 3. 引擎会不会路由错？

会的，特别是含糊的请求。处理方式：
- 不准 → 引擎输出的"匹配场景（按相关度）"会显示分数，把低分项忽略就行
- 强制场景：`python3 scripts/mega_engine.py --scene bug "<text>"` 直接锁
- 加反馈：把你认为最贴合的场景 ID 写到 `resources/mega_kb.json` 的 keyword 字典，我下次更准

## 4. 3 道防线会不会误伤？

**会**。已知的几个场景：
- `guard_injection.py` 把"假装没有 X"类话术也判越权 → 可能误伤某些合规讨论
- `guard_license.py` 把"AGPL"出现就 warn → 但 AGPL 讨论本身合法，只是要注意怎么用

误伤反馈：把样本给我（不要带敏感字段），我加白名单/调权值。

## 5. 怎么升级到 v1.1.0？

升级策略是**保 name = mozi-engineer 不变**，只升 version，覆盖上传。下载量不重置。

## 6. 能不能给个"完美的架构模板"？

不能。本包不替用户拍板——给前提 + 备选 + 取舍，让你自己选。 体系级决策（用 K8s 还是 ECS）请走**子房·人脉借力**或**孔明·方案策划**。

## 7. 和我的模型对话会被记录吗？

不会。本包所有处理都在你的本地 SkillHub 内置的沙箱里跑；脚本是纯 Python stdlib，**没有任何网络请求、没有上传代码逻辑**。

## 8. AI agent 写代码怎么管？

详见 `references/04_safety/AI编码治理.md`。三件必做：
1. AI 输出也有 reviewer（不放过不刁难）
2. AI 输出必须有测试
3. AI 不可逆操作要二次确认

## 9. 怎么配合 鲁班-automation？

当你说了**可执行的活儿**（合并 Excel、写脚本、抓公开网页…），
- 本包给"为什么做 + 风险 + 鲁班去做什么"
- 鲁班给具体可跑 Python 代码

两者描述都在 SKILL.md 引导你交叉触发。

## 10. 怎样打补丁 / 贡献？

- 误判样本 → 把反例给我（关键词列表里没有的那句），加词典
- 新场景 → 加 references/<分类>/<场景>.md，并在 mega_kb.json 加场景条目
- 新防线 → 新加 scripts/guard_<name>.py 即可

(此 FAQ 会随升级更新)
