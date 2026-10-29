#!/bin/bash
# 新词快打：盯官方 SDK / 发布页的更新，出现新模型或新能力就报出来。
# 用法：./watch-new-words.sh        首次运行只建基线，第二次起只打印新增。
#
# 为什么盯 SDK release：新模型上线时，官方 SDK 的 release / changelog 通常当天就会提到它，
# 比谷歌趋势早，也不需要翻墙。HuggingFace 的 trending 接口在本机网络下超时，已排除。
set -u
cd "$(dirname "$0")" || exit 1
mkdir -p state
STATE=state/new-words.tsv
TMP=$(mktemp)

SRCS=(
  "openai/openai-python"
  "openai/openai-node"
  "anthropics/anthropic-sdk-python"
  "anthropics/anthropic-sdk-typescript"
  "google-gemini/generative-ai-python"
  "google-gemini/generative-ai-js"
  "deepseek-ai/DeepSeek-V3"
  "moonshotai/kimi-cli"
)

for repo in "${SRCS[@]}"; do
  curl -sS -m 20 "https://api.github.com/repos/$repo/releases?per_page=5" 2>/dev/null \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for r in data:
    if not isinstance(r, dict):
        continue
    print('$repo\t%s\t%s' % (r.get('tag_name',''), (r.get('name') or '')[:120]))
" >> "$TMP"
done

sort -u "$TMP" -o "$TMP"

if [ ! -f "$STATE" ]; then
  cp "$TMP" "$STATE"
  echo "已建立基线（$(wc -l < "$STATE" | tr -d ' ') 条）。下次运行只报新增。"
  rm -f "$TMP"
  exit 0
fi

NEW=$(comm -13 <(sort -u "$STATE") <(sort -u "$TMP"))
if [ -z "$NEW" ]; then
  echo "无新增。"
else
  echo "=== 新增 $(printf '%s\n' "$NEW" | wc -l | tr -d ' ') 条 ==="
  printf '%s\n' "$NEW"
  # 增量合并进基线，避免下次重复报
  sort -u "$STATE" "$TMP" -o "$STATE"
fi
rm -f "$TMP"
