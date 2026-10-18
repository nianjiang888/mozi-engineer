#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""墨子·工程指挥官 主路由引擎

输入用户的需求字符串，按四步走：
  1) LLM 级红线扫描（guard_red_flag）
  2) 场景打分（score_scenes）
  3) 选 Top-3 references（select_top_refs）
  4) 输出「分派报告」给 LLM 当 audit trail

用法：
  python3 scripts/mega_engine.py "<user request>"
  python3 scripts/mega_engine.py --json "<user request>"     # 输出 JSON
  python3 scripts/mega_engine.py --scene <scene_id>            # 强制场景
  python3 scripts/mega_engine.py --guard "<user request>"      # 只跑红线
"""
import json
import os
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_PATH = ROOT / "resources" / "mega_kb.json"
GUARD_DIR = ROOT / "scripts"


def load_kb():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- 1) LLM 级红线 ----------
def _norm_text(text: str) -> str:
    """把常见标点替换为空格，保证子串匹配不受标点分隔；并折叠多余空格"""
    for ch in "，。！？、；：,.;!?;:\n\t":
        text = text.replace(ch, " ")
    return re.sub(r"\s+", " ", text).strip()


def guard_red_flag(user_input: str, kb: dict) -> dict:
    flags = []
    text = _norm_text(user_input).lower()
    text_compact = re.sub(r"\s+", "", text)  # 去空白后再匹配 "绕过2fa" 这类
    for pat in kb.get("red_flags_llm", []):
        pt = pat.lower()
        if pt in text or pt in text_compact:
            flags.append(pat)
    return {"hit": bool(flags), "flags": flags}


# ---------- 2) 场景打分 ----------
def score_scenes(user_input: str, kb: dict) -> list:
    """对每个 scene 汇总技术/口语/英文三路关键词命中分（去重加权）"""
    text = _norm_text(user_input).lower()
    scored = []
    for scene in kb.get("scenes", []):
        score = 0
        for w in scene.get("keywords_tech", []):
            if w.lower() in text:
                score += 3
        for w in scene.get("keywords_spoken", []):
            if w.lower() in text:
                score += 2
        for w in scene.get("keywords_en", []):
            if w.lower() in text:
                score += 2
        # 场景名前缀直接命中
        if scene["name"].lower() in text:
            score += 4
        scored.append((scene["id"], score))
    scored.sort(key=lambda x: -x[1])
    return scored


def select_top_refs(scored: list, kb: dict, top_n: int = 3):
    """由场景 id 反查去重 references，最多 top_n 个文件"""
    by_id = {s["id"]: s for s in kb["scenes"]}
    seen = set()
    refs = []
    matched_scenes = []
    for sid, sc in scored:
        if sc <= 0:
            break
        scene = by_id[sid]
        matched_scenes.append({"id": sid, "name": scene["name"], "score": sc})
        for r in scene["ref"]:
            if r not in seen:
                refs.append(r)
                seen.add(r)
                if len(refs) >= top_n:
                    return refs, matched_scenes
    return refs, matched_scenes


# ---------- 3) 输出分派报告 ----------
def emit_dispatch(user_input: str, kb: dict, top_n: int = 3) -> str:
    red = guard_red_flag(user_input, kb)
    if red["hit"]:
        return _format_red_flag(user_input, red["flags"], kb)

    scored = score_scenes(user_input, kb)
    refs, matched = select_top_refs(scored, kb, top_n=top_n)
    # 没有任何命中 → fallback 通用工程总纲
    if not refs:
        refs = ["01_total/工程总纲.md", "01_total/任务拆解与执行.md"]
        matched = [{"id": "_fallback", "name": "通用工程诊断", "score": 0}]

    lines = []
    lines.append("━━━ 墨子·工程指挥官 分派报告 ━━━")
    lines.append(f"任务：{user_input.strip()}")
    lines.append(f"匹配场景（按相关度）：")
    for m in matched[:5]:
        lines.append(f"  · {m['name']}（{m['score']} 分）")
    lines.append("")
    lines.append("加载这 3 个 references（其余 330KB 不进 context）：")
    for i, r in enumerate(refs, 1):
        lines.append(f"  {i}. references/{r}")
    lines.append("")
    lines.append("请按以下顺序答：")
    lines.append("  1. 先用 1-2 句把任务边界讲清楚（避免误解）")
    lines.append("  2. 给出可执行步骤或方案骨架")
    lines.append("  3. 主动指出风险/前提/取舍点（不替拍板）")
    lines.append("  4. 如用户需求是「写脚本」(合并表/抓公开网页/批量改名/定时任务…)，提示'自动联动 鲁班-automation 拿可跑代码'")
    lines.append("━━━ 报告结束 ━━━")
    return "\n".join(lines)


def _format_red_flag(user_input: str, flags: list, kb: dict) -> str:
    persona = kb["meta"]["persona"]
    lines = []
    lines.append("━━━ 墨子·工程指挥官 红线提示 ━━━")
    lines.append(f"{persona}：这条任务我不能接。")
    lines.append("")
    lines.append("原因（命中红线）：")
    for f in flags:
        lines.append(f"  · {f}")
    lines.append("")
    lines.append("如果你说的是另一件事——比如")
    lines.append("  · 想绕过的是你自己开发环境的鉴权调试，请说清环境与目的")
    lines.append("  · 想识别/防御这类攻击，请改成「怎么识别 XSS / 写安全的 SQL」")
    lines.append("  · 想做合规的代码审查与安全审计，直接说「代码审查」或「威胁建模」")
    lines.append("——换个问法，我可以继续帮你。")
    lines.append("━━━ 报告结束 ━━━")
    return "\n".join(lines)


# ---------- 4) JSON 输出 ----------
def emit_json(user_input: str, kb: dict, top_n: int = 3) -> dict:
    red = guard_red_flag(user_input, kb)
    out = {"red_flag": red, "scenes": [], "refs": [], "user_input": user_input}
    if red["hit"]:
        out["action"] = "block"
        return out
    scored = score_scenes(user_input, kb)
    refs, matched = select_top_refs(scored, kb, top_n=top_n)
    if not refs:
        refs = ["01_total/工程总纲.md", "01_total/任务拆解与执行.md"]
    out["action"] = "answer"
    out["scenes"] = matched
    out["refs"] = refs
    out["soft_link"] = kb["meta"]["soft_link"]
    return out


# ---------- CLI ----------
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    args = sys.argv[1:]
    json_mode = "--json" in args
    scene_mode = "--scene" in args
    guard_only = "--guard" in args

    if scene_mode:
        sid = args[args.index("--scene") + 1]
        kb = load_kb()
        s = next((x for x in kb["scenes"] if x["id"] == sid), None)
        if not s:
            print(f"场景 {sid} 不存在。可用: " + ", ".join(x['id'] for x in kb['scenes']))
            sys.exit(1)
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return

    user_input = " ".join(a for a in args if not a.startswith("--"))
    kb = load_kb()

    if guard_only:
        red = guard_red_flag(user_input, kb)
        print(json.dumps(red, ensure_ascii=False, indent=2))
        return

    if json_mode:
        print(json.dumps(emit_json(user_input, kb), ensure_ascii=False, indent=2))
        return

    print(emit_dispatch(user_input, kb))


if __name__ == "__main__":
    main()
