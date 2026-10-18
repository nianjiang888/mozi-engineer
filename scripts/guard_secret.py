#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""墨子·工程指挥官 · Guard #1: Secret 脱敏检测

用法：
  python3 scripts/guard_secret.py "<待检测文本>"
  echo "AKIA..." | python3 scripts/guard_secret.py   # 也支持管道

行为：
  扫描文本里是否含疑似 AWS AK / 阿里云 AK / GitHub PAT / 通用 JWT / 数据库连接串 /
  私钥 PEM。如命中，输出命中条目 + 建议的脱敏替换规则。
  只告警不修改原文。命中越多越应该拒绝写入日志/截图/外发。
"""
import re
import sys
import json

PATTERNS = [
    ("aws_access_key", r"AKIA[0-9A-Z]{16}"),
    ("aws_secret", r"(?i)aws(.{0,20})?(secret|sk)[^A-Za-z0-9]?([0-9A-Za-z/+=]{40})"),
    ("aliyun_ak",     r"LTAI[A-Za-z0-9]{12,20}"),
    ("github_pat",    r"ghp_[A-Za-z0-9]{36}"),
    ("github_oauth",  r"gho_[A-Za-z0-9]{36}"),
    ("slack_token",   r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    ("jwt",           r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("private_pem",   r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ("postgres_url",  r"postgres(?:ql)?://[^:\s]+:[^@\s]+@[^/\s]+"),
    ("mysql_url",     r"mysql://[^:\s]+:[^@\s]+@[^/\s]+"),
    ("mongo_url",     r"mongodb(?:\+srv)?://[^:\s]+:[^@\s]+@[^/\s]+"),
    ("redis_url",     r"redis://[^:\s]*:[^@\s]+@[^/\s]+"),
    ("bearer_auth",   r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._-]{20,}"),
]

# 用 \b 防止误伤代码中正规单词
GENERIC_SECRET_HINTS = [
    ("url_with_userpass", re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^:\s]+:[^@\s]+@")),
]


def scan(text: str) -> dict:
    hits = []
    for label, pat in PATTERNS:
        for m in re.finditer(pat, text):
            hits.append({
                "type": label,
                "match": m.group(0)[:24] + "..." if len(m.group(0)) > 24 else m.group(0),
                "start": m.start(),
            })
    for label, rx in GENERIC_SECRET_HINTS:
        for m in rx.finditer(text):
            hits.append({
                "type": label,
                "match": m.group(0)[:30] + "..." if len(m.group(0)) > 30 else m.group(0),
                "start": m.start(),
            })
    return {
        "input_length": len(text),
        "hits": hits,
        "hit_count": len(hits),
        "verdict": "BLOCK" if hits else "OK",
        "suggestion": (
            "请把含密钥/连接串的内容打码为「{REDACTED_AWS_AK} / {REDACTED_DB_URL}」之类占位再贴入对话；"
            "或在本地 .env / 密钥管理服务 (KMS / Vault / SOPS) 里读取，永远不要把凭据写进对话。"
        ) if hits else "OK",
    }


def main():
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = sys.stdin.read()
    result = scan(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if result["verdict"] == "BLOCK" else 0)


if __name__ == "__main__":
    main()
