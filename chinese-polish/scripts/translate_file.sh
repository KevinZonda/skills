#!/usr/bin/env bash
# chinese-polish/scripts/translate_file.sh
# 文件翻译完整工作流：读文件 → 分段 → 逐段调用 translate.sh → 合并 → 写输出文件
#
# 用法:
#   translate_file.sh --target <目标语言> [--source <源语言>] --input <file> [--output <file>]
#
# --target : 目标语言（必须）
# --source : 源语言（可选，不填则自动识别）
# --input  : 输入文件路径（必须）
# --output : 输出文件路径（可选，默认 <basename>.<目标语言>.ext）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TRANSLATE_SH="$SCRIPT_DIR/translate.sh"
SEGMENT_MAX_CHARS=1800

# ---------- 解析参数 ----------
TARGET_LANG=""
SOURCE_LANG=""
INPUT_FILE=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) TARGET_LANG="$2"; shift 2 ;;
        --source) SOURCE_LANG="$2"; shift 2 ;;
        --input)  INPUT_FILE="$2";  shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        *) echo "未知参数: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$TARGET_LANG" ]]; then
    echo "错误: 必须指定 --target <目标语言>" >&2; exit 1
fi
if [[ -z "$INPUT_FILE" ]]; then
    echo "错误: 必须指定 --input <file>" >&2; exit 1
fi
if [[ ! -r "$INPUT_FILE" ]]; then
    echo "错误: 文件不可读: $INPUT_FILE" >&2; exit 1
fi

# ---------- 生成输出文件路径 ----------
if [[ -z "$OUTPUT_FILE" ]]; then
    BASE="${INPUT_FILE%.*}"
    EXT="${INPUT_FILE##*.}"
    # 目标语言名称中可能含空格，替换为下划线
    LANG_SLUG="${TARGET_LANG// /_}"
    if [[ "$EXT" == "$INPUT_FILE" ]]; then
        OUTPUT_FILE="${INPUT_FILE}.${LANG_SLUG}"
    else
        OUTPUT_FILE="${BASE}.${LANG_SLUG}.${EXT}"
    fi
fi

# ---------- 文件类型路由：.tex → translate_latex.py，.md → translate_markdown.py ----------
FILE_EXT="${INPUT_FILE##*.}"
FILE_EXT_LOWER=$(echo "$FILE_EXT" | tr '[:upper:]' '[:lower:]')

if [[ "$FILE_EXT_LOWER" == "tex" || "$FILE_EXT_LOWER" == "latex" ]]; then
    echo "=== LaTeX 专用翻译 ===" >&2
    [[ -z "$OUTPUT_FILE" ]] && OUTPUT_FILE="${INPUT_FILE%.*}.${TARGET_LANG// /_}.tex"
    SOURCE_ARG=""
    [[ -n "$SOURCE_LANG" ]] && SOURCE_ARG="--source $SOURCE_LANG"
    RESULT=$(python3 "$SCRIPT_DIR/translate_latex.py" \
        --target "$TARGET_LANG" $SOURCE_ARG \
        --input  "$INPUT_FILE" \
        --output "$OUTPUT_FILE")
    echo "$RESULT"
    exit 0
fi

if [[ "$FILE_EXT_LOWER" == "md" || "$FILE_EXT_LOWER" == "markdown" ]]; then
    echo "=== Markdown 专用翻译 ===" >&2
    [[ -z "$OUTPUT_FILE" ]] && OUTPUT_FILE="${INPUT_FILE%.*}.${TARGET_LANG// /_}.md"
    SOURCE_ARG=""
    [[ -n "$SOURCE_LANG" ]] && SOURCE_ARG="--source $SOURCE_LANG"
    RESULT=$(python3 "$SCRIPT_DIR/translate_markdown.py" \
        --target "$TARGET_LANG" $SOURCE_ARG \
        --input  "$INPUT_FILE" \
        --output "$OUTPUT_FILE")
    echo "$RESULT"
    exit 0
fi

# ---------- 其他文件类型：通用分段翻译 ----------
CONTENT="$(cat "$INPUT_FILE")"
TOTAL_CHARS="${#CONTENT}"

echo "=== 翻译开始 ===" >&2
echo "输入文件   : $INPUT_FILE ($TOTAL_CHARS 字符)" >&2
echo "输出文件   : $OUTPUT_FILE" >&2
echo "目标语言   : $TARGET_LANG" >&2
[[ -n "$SOURCE_LANG" ]] && echo "源语言     : $SOURCE_LANG" >&2

# ---------- 分段函数（与 polish_file.sh 相同逻辑）----------
split_into_segments() {
    local text="$1"
    local -a segments=()
    local current=""

    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ -z "$line" ]]; then
            if [[ -n "$current" ]]; then
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
            if [[ "${#current}" -gt "$SEGMENT_MAX_CHARS" ]]; then
                printf '%s\0' "$current"
                current=""
            fi
        fi
    done <<< "$text"

    if [[ -n "$current" ]]; then
        segments+=("$current")
    fi

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
TMPDIR_WORK=$(mktemp -d /tmp/translate_work.XXXXXX)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

SEG_IDX=0
TRANSLATED_PARTS=()
DETECTED_SOURCE=""

while IFS= read -r -d '' segment; do
    SEG_IDX=$(( SEG_IDX + 1 ))
    echo "  翻译段落 $SEG_IDX (${#segment} 字符)..." >&2

    SEG_FILE="$TMPDIR_WORK/seg_${SEG_IDX}.txt"
    printf '%s' "$segment" > "$SEG_FILE"
    RESULT_FILE="$TMPDIR_WORK/result_${SEG_IDX}.json"

    TRANSLATE_ARGS=(--target "$TARGET_LANG" --file "$SEG_FILE")
    [[ -n "$SOURCE_LANG" ]] && TRANSLATE_ARGS+=(--source "$SOURCE_LANG")

    if bash "$TRANSLATE_SH" "${TRANSLATE_ARGS[@]}" > "$RESULT_FILE" 2>"$TMPDIR_WORK/err_${SEG_IDX}.txt"; then
        TRANSLATED_TEXT=$(jq -r '.translated // empty' "$RESULT_FILE" 2>/dev/null || true)
        if [[ -z "$TRANSLATED_TEXT" ]]; then
            echo "    警告: 第 $SEG_IDX 段返回无 translated 字段，保留原文" >&2
            TRANSLATED_PARTS+=("$segment")
        else
            TRANSLATED_PARTS+=("$TRANSLATED_TEXT")
            # 记录首段识别到的源语言
            if [[ -z "$DETECTED_SOURCE" ]]; then
                DETECTED_SOURCE=$(jq -r '.source_lang // empty' "$RESULT_FILE" 2>/dev/null || true)
            fi
        fi
    else
        ERR=$(cat "$TMPDIR_WORK/err_${SEG_IDX}.txt" 2>/dev/null || true)
        echo "    警告: 第 $SEG_IDX 段翻译失败，保留原文。错误: $ERR" >&2
        TRANSLATED_PARTS+=("$segment")
    fi

done < <(split_into_segments "$CONTENT")

TOTAL_SEGS="$SEG_IDX"

if [[ "$TOTAL_SEGS" -eq 0 ]]; then
    echo "错误: 未读取到任何段落内容" >&2; exit 1
fi

# ---------- 合并输出 ----------
{
    first=true
    for part in "${TRANSLATED_PARTS[@]+"${TRANSLATED_PARTS[@]}"}"; do
        if [[ "$first" == true ]]; then
            printf '%s' "$part"
            first=false
        else
            printf '\n\n%s' "$part"
        fi
    done
    printf '\n'
} > "$OUTPUT_FILE"

echo "" >&2
echo "=== 翻译完成 ===" >&2
echo "输出文件   : $OUTPUT_FILE" >&2
echo "处理段落数 : $TOTAL_SEGS" >&2

# 输出 JSON 摘要供 Claude 解析
jq -n \
    --arg output       "$OUTPUT_FILE" \
    --arg input        "$INPUT_FILE" \
    --arg target       "$TARGET_LANG" \
    --arg source       "${DETECTED_SOURCE:-${SOURCE_LANG:-自动识别}}" \
    --argjson segs     "$TOTAL_SEGS" \
    '{
        output_file:  $output,
        input_file:   $input,
        source_lang:  $source,
        target_lang:  $target,
        segments:     $segs
    }'
