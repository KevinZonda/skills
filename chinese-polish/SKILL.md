---
name: chinese-polish
description: "调用 DeepSeek API 进行中文润色和多语言翻译。润色支持通用/学术/商务/口语四种风格；翻译支持任意语言互译，并对 .tex（LaTeX）和 .md（Markdown）文件做专项处理，保留所有命令/代码/数学公式，只翻译自然语言文本。"
---

# 中文润色 & 多语言翻译

通过 DeepSeek API（`deepseek-chat` 模型）提供两大功能：**文本润色**和**多语言翻译**。

## 触发场景

**润色：**
- 用户说"润色"、"改写"、"优化这段文字"、"polish"、"帮我改一下措辞"
- 用户提供一段文字并希望提升表达质量
- 用户要求润色某个文件

**翻译：**
- 用户说"翻译成中文"、"translate to English"、"帮我把这段译成日文"
- 用户提供文本并指定目标语言
- 用户要求翻译某个文件

- 用户要求翻译 `.tex`（LaTeX）或 `.md`（Markdown）文件

## 文件类型专项处理

`translate_file.sh` 根据文件扩展名自动路由：

| 扩展名 | 处理脚本 | 保留内容 | 翻译内容 |
|--------|----------|----------|----------|
| `.tex` / `.latex` | `translate_latex.py` | LaTeX 命令、数学公式、`\texttt{}`、`tabular`/`tikzpicture`/`thebibliography` 环境体 | 章节标题、段落文本、`\abstract{}`、`\keywords{}`、`\title{}`、图表说明 |
| `.md` / `.markdown` | `translate_markdown.py` | 代码块（`` ``` ``）、行内代码、数学公式、链接 URL、图片 URL、HTML 标签、YAML front matter | 正文、标题文字、链接文字、图片 alt 文字 |
| 其他 | 原有通用分段逻辑 | — | 全文分段翻译 |

### 调用示例

```bash
export DEEPSEEK_API_KEY="sk-..."

# 翻译 LaTeX 论文
bash ~/.claude/skills/chinese-polish/scripts/translate_file.sh \
    --target 中文 --source 英文 \
    --input paper.tex --output paper.zh.tex

# 翻译 Markdown 文档
bash ~/.claude/skills/chinese-polish/scripts/translate_file.sh \
    --target 中文 \
    --input README.md --output README.zh.md
```

### LaTeX 专项物理术语映射

| 英文 | 中文 |
|------|------|
| photoelectron(s) | 光电子 |
| dark count rate | 暗计数率 |
| liquid scintillator | 液体闪烁体 |
| calibration | 刻度 |
| simulation | 模拟 |
| PMT | 光电倍增管(PMT) |
| neutrino | 中微子 |
| readout window | 读出窗口 |
| transit-time spread | 渡越时间弥散 |
| baseline | 基准线 |
| campaign | 调优活动 |

技术标识符（**不翻译**）：CDCalib, detsim, elec, rec, uproot, iminuit, SNiPER, LS_FULL, ACU_DCR_FIX, codearmy, EOS

## 润色模式

| 模式 | 触发关键词 | 说明 |
|------|-----------|------|
| `default` | 默认/通用/不指定 | 保持原意，提升流畅度和可读性 |
| `academic` | 学术/论文/严谨/正式 | 严谨客观，符合中文学术规范 |
| `business` | 商务/商业/邮件/报告 | 专业简洁，适合商务沟通 |
| `casual` | 口语/日常/轻松/亲切 | 自然亲切，接地气 |

## 前提检查

执行前先校验 API Key：

```bash
test -n "$DEEPSEEK_API_KEY" && echo "OK" || echo "MISSING"
```

如果输出 `MISSING`，告知用户需要设置环境变量：
```bash
export DEEPSEEK_API_KEY="sk-..."  # 写入 ~/.zshrc 后 source
```
并停止执行。

## 工作流 A：润色文本片段

用户直接粘贴文字时使用此流程。

1. 从用户消息中提取待润色文本和模式（未指定则用 `default`）
2. 将文本写入临时文件（避免 shell 转义问题）：
   ```bash
   TMPFILE=$(mktemp /tmp/polish_input.XXXXXX.txt)
   cat > "$TMPFILE" << 'TEXTEOF'
   （待润色文本）
   TEXTEOF
   ```
3. 调用核心脚本：
   ```bash
   bash ~/.agents/skills/chinese-polish/scripts/polish.sh <mode> --file "$TMPFILE"
   rm -f "$TMPFILE"
   ```
4. 脚本输出 JSON：`{"polished": "...", "changes": ["...", ...]}`
5. 按以下格式呈现结果：

```
## 润色结果（<模式>风格）

### 原文
> （原文，保留段落结构）

### 润色后
（润色后的文本）

### 主要修改
- 修改要点1
- 修改要点2
- ...
```

**长文本处理**（超过 2000 字）：按自然段落拆分，每段独立调用，最后合并拼接。

## 工作流 B：润色文件

用户要求润色某个文件时使用此流程（使用 `polish_file.sh` 完整工作流脚本）。

1. 确认文件路径（要求用户提供绝对路径）
2. 确认润色模式（未指定则询问或默认 `default`）
3. 调用文件润色脚本：
   ```bash
   bash ~/.agents/skills/chinese-polish/scripts/polish_file.sh \
       --mode <mode> \
       --input <input_file> \
       [--output <output_file>]  # 不指定则自动生成 <basename>.polished.<ext>
   ```
4. 脚本完成后告知用户：
   - 润色后文件路径
   - 处理的段落数
   - 主要修改摘要（汇总各段的 changes）

## 工作流 C：翻译文本片段

用户要求翻译一段文字时使用此流程。

1. 从用户消息中提取待翻译文本、源语言（可不指定，自动识别）、目标语言
2. 将文本写入临时文件：
   ```bash
   TMPFILE=$(mktemp /tmp/translate_input.XXXXXX.txt)
   cat > "$TMPFILE" << 'TEXTEOF'
   （待翻译文本）
   TEXTEOF
   ```
3. 调用翻译脚本：
   ```bash
   bash ~/.agents/skills/chinese-polish/scripts/translate.sh \
       --target <目标语言> \
       [--source <源语言>] \
       --file "$TMPFILE"
   rm -f "$TMPFILE"
   ```
4. 脚本输出 JSON：`{"translated": "...", "source_lang": "...", "target_lang": "..."}`
5. 按以下格式呈现：

```
## 翻译结果（<源语言> → <目标语言>）

### 原文
> （原文）

### 译文
（翻译后的文本）
```

**语言参数说明**：使用自然语言名称即可，如 `中文`、`英文`、`English`、`日语`、`韩语`、`French` 等，脚本直接透传给模型。

**长文本处理**（超过 2000 字）：按自然段落拆分，每段独立调用，最后合并。

## 工作流 D：翻译文件

用户要求翻译某个文件时使用此流程（使用 `translate_file.sh`）。

1. 确认文件路径（要求绝对路径）
2. 确认目标语言（必须指定），源语言可选
3. 调用文件翻译脚本：
   ```bash
   bash ~/.agents/skills/chinese-polish/scripts/translate_file.sh \
       --target <目标语言> \
       [--source <源语言>] \
       --input <input_file> \
       [--output <output_file>]  # 不指定则自动生成 <basename>.<目标语言>.ext
   ```
4. 完成后告知用户：
   - 译文文件路径
   - 处理的段落数

## 错误处理

- API 返回非 200：展示 HTTP 状态码和错误信息，建议检查 API Key 或网络
- JSON 解析失败：直接输出原始响应，让用户判断
- 文件不可读：提示用户检查路径和权限
- 超时（> 60s）：建议缩短文本或分段提交

## 脚本说明

| 脚本 | 功能 |
|------|------|
| `scripts/polish.sh` | 核心润色，接受模式和文本（文件方式），输出 JSON |
| `scripts/polish_file.sh` | 文件润色完整工作流，分段处理，写入输出文件 |
| `scripts/translate.sh` | 核心翻译，接受目标语言和文本（文件方式），输出 JSON |
| `scripts/translate_file.sh` | 文件翻译完整工作流，分段处理，写入输出文件 |
