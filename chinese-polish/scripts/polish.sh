#!/usr/bin/env bash
# chinese-polish/scripts/polish.sh
# 调用 DeepSeek API 对中文文本进行润色（核心脚本）
#
# 用法:
#   polish.sh <mode> --file <filepath>
#   polish.sh <mode> <text>          # 短文本直接传参
#
# mode: default | academic | business | casual
#
# 输出: JSON {"polished": "...", "changes": ["...", ...]}
# 错误: JSON {"error": "..."} 写入 stderr，exit 1

set -euo pipefail

API_URL="https://api.deepseek.com/chat/completions"
MODEL="deepseek-chat"
TEMPERATURE="1.3"

# ---------- 参数解析 ----------
MODE="${1:-default}"
shift || true

if [[ "${1:-}" == "--file" ]]; then
    INPUT_FILE="${2:?'--file 需要指定文件路径'}"
    if [[ ! -r "$INPUT_FILE" ]]; then
        echo "{\"error\": \"文件不可读: $INPUT_FILE\"}" >&2
        exit 1
    fi
    TEXT="$(cat "$INPUT_FILE")"
else
    TEXT="${1:-}"
fi

if [[ -z "$TEXT" ]]; then
    echo '{"error": "未提供待润色文本"}' >&2
    exit 1
fi

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
    echo '{"error": "未设置 DEEPSEEK_API_KEY 环境变量"}' >&2
    exit 1
fi

# ---------- System Prompt ----------
BASE_SUFFIX='请返回 JSON 格式：{"polished": "润色后的文本", "changes": ["修改要点1", "修改要点2", ...]}
修改要点简洁说明改了什么、为什么改（3-5条）。只返回 JSON，不要添加其他内容。'

case "$MODE" in
    academic)
        SYSTEM_PROMPT="你是一位中文学术写作专家。请对用户提供的中文文本进行学术风格润色，要求：
1. 使用严谨、客观、正式的学术语言
2. 确保逻辑清晰、论述准确
3. 使用规范的学术用语和句式
4. 避免口语化表达和主观臆断
5. 保持原文的论点和论据不变
${BASE_SUFFIX}"
        ;;
    business)
        SYSTEM_PROMPT="你是一位商务写作专家。请对用户提供的中文文本进行商务风格润色，要求：
1. 语言专业、简洁、有力
2. 适合商务报告、邮件、方案等场景
3. 突出重点，逻辑层次分明
4. 使用恰当的商务用语
5. 保持原文的核心信息不变
${BASE_SUFFIX}"
        ;;
    casual)
        SYSTEM_PROMPT="你是一位中文写作达人。请对用户提供的中文文本进行口语化润色，要求：
1. 语言自然、亲切、接地气
2. 保持原意但让表达更生动活泼
3. 适当使用口语化表达和修辞
4. 避免生硬的书面语
5. 保持原文的核心信息不变
${BASE_SUFFIX}"
        ;;
    *)
        SYSTEM_PROMPT="你是一位中文写作专家。请对用户提供的中文文本进行润色，要求：
1. 保持原文的核心含义不变
2. 提升语言的流畅度和可读性
3. 修正语法错误和用词不当
4. 优化句式结构，消除冗余表达
${BASE_SUFFIX}"
        ;;
esac

USER_PROMPT="请润色以下文本：

${TEXT}"

# ---------- 构造 payload（jq 安全转义中文和特殊字符）----------
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
RESPONSE=$(curl -s --noproxy "api.deepseek.com" -w "\n%{http_code}" \
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

# ---------- 提取 content ----------
CONTENT=$(printf '%s' "$BODY" | jq -r '.choices[0].message.content // empty')

if [[ -z "$CONTENT" ]]; then
    echo '{"error": "API 返回内容为空"}' >&2
    exit 1
fi

# content 本身是 JSON object，直接输出
printf '%s\n' "$CONTENT"
