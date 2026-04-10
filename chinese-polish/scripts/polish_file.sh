#!/usr/bin/env bash
# chinese-polish/scripts/polish_file.sh
# 文件润色完整工作流：读文件 → 分段 → 逐段调用 polish.sh → 合并 → 写输出文件
#
# 用法:
#   polish_file.sh --mode <mode> --input <file> [--output <file>]
#
# --mode   : default | academic | business | casual （默认 default）
# --input  : 输入文件路径（必须）
# --output : 输出文件路径（可选，默认 <basename>.polished.<ext>）
#
# 退出码:
#   0 成功
#   1 参数错误或文件不可读
#   2 API 调用失败

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POLISH_SH="$SCRIPT_DIR/polish.sh"
SEGMENT_MAX_CHARS=1800   # 每段最大字符数（留余量，避免贴近 API 上限）

# ---------- 解析参数 ----------
MODE="default"
INPUT_FILE=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)   MODE="$2";        shift 2 ;;
        --input)  INPUT_FILE="$2";  shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        *) echo "未知参数: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$INPUT_FILE" ]]; then
    echo "错误: 必须指定 --input <file>" >&2
    exit 1
fi

if [[ ! -r "$INPUT_FILE" ]]; then
    echo "错误: 文件不可读: $INPUT_FILE" >&2
    exit 1
fi

# ---------- 生成输出文件路径 ----------
if [[ -z "$OUTPUT_FILE" ]]; then
    BASE="${INPUT_FILE%.*}"
    EXT="${INPUT_FILE##*.}"
    if [[ "$EXT" == "$INPUT_FILE" ]]; then
        OUTPUT_FILE="${INPUT_FILE}.polished"
    else
        OUTPUT_FILE="${BASE}.polished.${EXT}"
    fi
fi

# ---------- 读取输入内容 ----------
CONTENT="$(cat "$INPUT_FILE")"
TOTAL_CHARS="${#CONTENT}"

echo "=== 中文润色开始 ===" >&2
echo "输入文件 : $INPUT_FILE ($TOTAL_CHARS 字符)" >&2
echo "输出文件 : $OUTPUT_FILE" >&2
echo "润色模式 : $MODE" >&2

# ---------- 分段函数 ----------
# 将文本按空行（段落分隔符）切分，再合并短段、分拆超长段
split_into_segments() {
    local text="$1"
    local -a segments=()
    local current=""

    # 逐行处理
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ -z "$line" ]]; then
            # 空行：段落边界
            if [[ -n "$current" ]]; then
                # 当前积累段超长则先输出
                if [[ "${#current}" -gt "$SEGMENT_MAX_CHARS" ]]; then
                    printf '%s\0' "$current"
                    current=""
                else
                    segments+=("$current")
                    current=""
                fi
            fi
        else
            if [[ -n "$current" ]]; then
                current="${current}
${line}"
            else
                current="$line"
            fi

            # 积累段已超长，强制切断
            if [[ "${#current}" -gt "$SEGMENT_MAX_CHARS" ]]; then
                printf '%s\0' "$current"
                current=""
            fi
        fi
    done <<< "$text"

    # 输出最后一段
    if [[ -n "$current" ]]; then
        segments+=("$current")
    fi

    # 合并 segments 数组中的短段，输出 NUL 分隔
    local merged=""
    for seg in "${segments[@]+"${segments[@]}"}"; do
        if [[ -z "$merged" ]]; then
            merged="$seg"
        elif [[ $(( ${#merged} + ${#seg} + 2 )) -le "$SEGMENT_MAX_CHARS" ]]; then
            merged="${merged}

${seg}"
        else
            printf '%s\0' "$merged"
            merged="$seg"
        fi
    done
    if [[ -n "$merged" ]]; then
        printf '%s\0' "$merged"
    fi
}

# ---------- 主流程 ----------
TMPDIR_WORK=$(mktemp -d /tmp/polish_work.XXXXXX)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

SEG_IDX=0
ALL_CHANGES=()
POLISHED_PARTS=()

# 逐段处理
while IFS= read -r -d '' segment; do
    SEG_IDX=$(( SEG_IDX + 1 ))
    echo "  处理段落 $SEG_IDX (${#segment} 字符)..." >&2

    SEG_FILE="$TMPDIR_WORK/seg_${SEG_IDX}.txt"
    printf '%s' "$segment" > "$SEG_FILE"

    RESULT_FILE="$TMPDIR_WORK/result_${SEG_IDX}.json"

    # 调用核心脚本，失败时输出错误并跳过该段（保留原文）
    if bash "$POLISH_SH" "$MODE" --file "$SEG_FILE" > "$RESULT_FILE" 2>"$TMPDIR_WORK/err_${SEG_IDX}.txt"; then
        POLISHED_TEXT=$(jq -r '.polished // empty' "$RESULT_FILE" 2>/dev/null || true)
        if [[ -z "$POLISHED_TEXT" ]]; then
            echo "    警告: 第 $SEG_IDX 段 API 返回无 polished 字段，保留原文" >&2
            POLISHED_PARTS+=("$segment")
        else
            POLISHED_PARTS+=("$POLISHED_TEXT")
            # 收集 changes
            while IFS= read -r change; do
                ALL_CHANGES+=("$change")
            done < <(jq -r '.changes[]? // empty' "$RESULT_FILE" 2>/dev/null || true)
        fi
    else
        ERR=$(cat "$TMPDIR_WORK/err_${SEG_IDX}.txt" 2>/dev/null || true)
        echo "    警告: 第 $SEG_IDX 段润色失败，保留原文。错误: $ERR" >&2
        POLISHED_PARTS+=("$segment")
    fi

done < <(split_into_segments "$CONTENT")

TOTAL_SEGS="$SEG_IDX"

if [[ "$TOTAL_SEGS" -eq 0 ]]; then
    echo "错误: 未读取到任何段落内容" >&2
    exit 1
fi

# ---------- 合并输出 ----------
{
    first=true
    for part in "${POLISHED_PARTS[@]+"${POLISHED_PARTS[@]}"}"; do
        if [[ "$first" == true ]]; then
            printf '%s' "$part"
            first=false
        else
            printf '\n\n%s' "$part"
        fi
    done
    printf '\n'
} > "$OUTPUT_FILE"

# ---------- 汇总报告 ----------
echo "" >&2
echo "=== 润色完成 ===" >&2
echo "输出文件   : $OUTPUT_FILE" >&2
echo "处理段落数 : $TOTAL_SEGS" >&2

# 输出 JSON 摘要供 Claude 解析
CHANGES_JSON=$(printf '%s\n' "${ALL_CHANGES[@]+"${ALL_CHANGES[@]}"}" | jq -R . | jq -s .)
jq -n \
    --arg output  "$OUTPUT_FILE" \
    --arg input   "$INPUT_FILE" \
    --arg mode    "$MODE" \
    --argjson segs "$TOTAL_SEGS" \
    --argjson changes "$CHANGES_JSON" \
    '{
        output_file: $output,
        input_file:  $input,
        mode:        $mode,
        segments:    $segs,
        changes:     $changes
    }'
