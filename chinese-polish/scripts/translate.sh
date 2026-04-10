#!/usr/bin/env bash
# chinese-polish/scripts/translate.sh
# 调用 DeepSeek API 进行多语言翻译（核心脚本）
#
# 用法:
#   translate.sh --target <目标语言> [--source <源语言>] --file <filepath>
#   translate.sh --target <目标语言> [--source <源语言>] <text>
#
# --target : 目标语言，如 "中文"、"English"、"日语"、"韩语"、"French" 等
# --source : 源语言（可选，不填则模型自动识别）
#
# 输出: JSON {"translated": "...", "source_lang": "...", "target_lang": "..."}
# 错误: JSON {"error": "..."} 写入 stderr，exit 1

set -euo pipefail

API_URL="https://api.deepseek.com/chat/completions"
MODEL="deepseek-chat"
TEMPERATURE="1.3"

# ---------- 参数解析 ----------
TARGET_LANG=""
SOURCE_LANG=""
INPUT_FILE=""
TEXT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) TARGET_LANG="$2"; shift 2 ;;
        --source) SOURCE_LANG="$2"; shift 2 ;;
        --file)   INPUT_FILE="$2";  shift 2 ;;
        *) TEXT="${TEXT:+$TEXT }$1"; shift ;;
    esac
done

if [[ -z "$TARGET_LANG" ]]; then
    echo '{"error": "必须指定 --target <目标语言>"}' >&2
    exit 1
fi

if [[ -n "$INPUT_FILE" ]]; then
    if [[ ! -r "$INPUT_FILE" ]]; then
        echo "{\"error\": \"文件不可读: $INPUT_FILE\"}" >&2
        exit 1
    fi
    TEXT="$(cat "$INPUT_FILE")"
fi

if [[ -z "$TEXT" ]]; then
    echo '{"error": "未提供待翻译文本"}' >&2
    exit 1
fi

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
    echo '{"error": "未设置 DEEPSEEK_API_KEY 环境变量"}' >&2
    exit 1
fi

# ---------- 构造 System Prompt ----------
if [[ -n "$SOURCE_LANG" ]]; then
    LANG_INSTRUCTION="请将以下${SOURCE_LANG}文本翻译成${TARGET_LANG}。"
else
    LANG_INSTRUCTION="请自动识别以下文本的语言，并将其翻译成${TARGET_LANG}。"
fi

SYSTEM_PROMPT="${LANG_INSTRUCTION}
要求：
1. 翻译准确，忠实原文含义
2. 译文自然流畅，符合目标语言的表达习惯
3. 保留原文的段落结构和格式
4. 专有名词、人名、地名等保持原文或使用通用译法
请返回 JSON 格式：{\"translated\": \"译文内容\", \"source_lang\": \"识别到的源语言\", \"target_lang\": \"${TARGET_LANG}\"}
只返回 JSON，不要添加其他内容。"

USER_PROMPT="$TEXT"

# ---------- 构造 payload ----------
PAYLOAD=$(jq -n \
    --arg model "$MODEL" \
    --argjson temperature "$TEMPERATURE" \
    --arg sys "$SYSTEM_PROMPT" \
    --arg user "$USER_PROMPT" \
    '{
        model: $model,
        temperature: $temperature,
        response_format: { type: "json_object" },
        messages: [
            { role: "system", content: $sys },
            { role: "user",   content: $user }
        ]
    }')

# ---------- 调用 API ----------
RESPONSE=$(curl -s -w "\n%{http_code}" \
    --max-time 60 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
    -d "$PAYLOAD" \
    "$API_URL")

HTTP_CODE=$(printf '%s' "$RESPONSE" | tail -1)
BODY=$(printf '%s' "$RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" -ne 200 ]]; then
    ERR_DETAIL=$(printf '%s' "$BODY" | jq -c '.' 2>/dev/null || printf '"%s"' "$BODY")
    echo "{\"error\": \"API 返回 HTTP ${HTTP_CODE}\", \"detail\": ${ERR_DETAIL}}" >&2
    exit 1
fi

CONTENT=$(printf '%s' "$BODY" | jq -r '.choices[0].message.content // empty')

if [[ -z "$CONTENT" ]]; then
    echo '{"error": "API 返回内容为空"}' >&2
    exit 1
fi

printf '%s\n' "$CONTENT"
