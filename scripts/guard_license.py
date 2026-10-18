#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""墨子·工程指挥官 · Guard #3: License/合规扫描

用法：
  python3 scripts/guard_license.py "<待检测文本>"
  echo "..." | python3 scripts/guard_license.py

行为：
  检测文本里的版权/许可信号，给出风险等级提示：
    - GPL/AGPL 出现在闭源 → 高风险（强制开源传染）
    - "直接复制 MIT 改个名" / "把 Apache 项目换个壳" → 中风险（注意署名/许可声明义务）
    - 拿商业素材（图片/字体/歌曲/视频）训练或二次分发 → 高风险
    - 抓取公开网页内容二次发表当原创 → 中风险（看 robots.txt 与版权声明）
"""
import re
import sys
import json

# 信号 → (类别, 风险等级 high/medium/low, 说明)
SIGNALS = [
    (r"\bGPL[- ]?(v?2|v?3)?\b", "license_gpl", "high", "GPL 系家族强制开源传染；并入闭源产品会触发开源义务。"),
    (r"\bAGPL\b", "license_agpl", "high", "AGPL 在网络服务场景也强制开源，最严苛的 GPL 变种。"),
    (r"\bLGPL\b", "license_lgpl", "medium", "LGPL 一般可链接，但若修改库本身需开源改动部分。"),
    (r"\bSSPL\b", "license_sspl", "high", "SSPL：网络服务也强制开源，MongoDB 等采用。"),
    (r"\bBUSL\b", "license_busl", "medium", "BUSL 非真开源；商业用途需额外授权。"),
    (r"\bRPL\b", "license_rpl", "medium", "RPL：分发时同样受限制；商用前读授权说明。"),
    (r"(直接|原样)复制.{0,15}(改个名|换壳|换品牌)", "copypasta_rewrite", "medium", "原样复制并改名仍构成衍生作品；需保留原作者署名与许可声明。"),
    (r"(把|将|拿).{0,15}(GPL|LGPL|AGPL|SSPL).{0,15}(塞进|并入|用到|嵌入)", "gpl_into_closed", "high", "把强传染许可库塞进闭源产品 → 高风险，可能触发开源义务。"),
    (r"(商业|付费|商用|版权).{0,15}(素材|图片|字体|音乐|视频|音频|歌曲)", "commercial_asset", "medium", "商业素材二次使用/再分发需先确认是否买断、是否含肖像权/版权水印。"),
    (r"(抓(取|了)|爬(取|了)|采集).{0,20}(网页|网站|文章|新闻|公众号|知乎|微博).{0,15}(当原创|二次发表|再发|洗稿)", "scrape_republish", "medium", "抓取公开网页 ≠ 无版权；robots.txt 与原文授权声明优先。"),
    (r"(训练|微调|精调).{0,15}(商业|付费|有版权|素材|歌曲)", "train_on_commercial", "high", "训练数据如包含受版权保护素材而无授权，模型对外输出可能引发争议；先做筛选与去重。"),
]


def scan(text: str) -> dict:
    hits = []
    for pat, kind, level, note in SIGNALS:
        if re.search(pat, text, re.IGNORECASE):
            hits.append({"type": kind, "level": level, "note": note})
    high = sum(1 for h in hits if h["level"] == "high")
    medium = sum(1 for h in hits if h["level"] == "medium")
    return {
        "input_length": len(text),
        "hits": hits,
        "high_count": high,
        "medium_count": medium,
        "verdict": "BLOCK" if high >= 1 else ("WARN" if medium >= 1 else "OK"),
        "suggestion": (
            "需先确认：①许可证义务（署名/传染）；②二次创作的合理使用边界；"
            "③商业素材授权范围；④抓取范围是否尊重 robots.txt。"
        ) if high + medium else "OK",
    }


def main():
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    result = scan(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if result["verdict"] == "BLOCK" else (2 if result["verdict"] == "WARN" else 0))


if __name__ == "__main__":
    main()
