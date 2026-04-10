#!/usr/bin/env python3
"""
LaTeX-aware translator using DeepSeek API.

Usage:
    translate_latex.py --target <lang> [--source <lang>] --input <file> --output <file>

Stdout: JSON {"output_file": "...", "input_file": "...", "source_lang": "...",
              "target_lang": "...", "segments": N}
"""
import os, sys, re, json, time, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

API_KEY  = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL  = "https://api.deepseek.com/chat/completions"
# Bypass any local HTTPS proxy that breaks TLS to external APIs
import os as _os
_os.environ.pop("HTTPS_PROXY", None)
_os.environ.pop("HTTP_PROXY", None)
MAX_RETRIES      = 3
REQUEST_TIMEOUT  = 120
SEGMENT_MAX_CHARS = 3000

SYSTEM_PROMPT = """\
You are a LaTeX-aware scientific translator specializing in high-energy physics papers.
Translate the English text in the provided LaTeX fragment into {target}.

STRICT RULES (any violation will break LaTeX compilation):
1. Preserve ALL LaTeX commands verbatim: \\section, \\cite{{}}, \\ref{{}}, \\label{{}}, \\texttt{{}}, \\emph{{}}, \\begin{{}}, \\end{{}}, etc.
2. Preserve ALL math mode verbatim: $...$, $$...$$, \\begin{{equation}}...\\end{{equation}}, \\begin{{align}}...\\end{{align}}, etc.
3. Preserve tabular / tikzpicture / thebibliography environment bodies verbatim.
4. Preserve ALL \\texttt{{}} / \\verb arguments verbatim (code, paths, identifiers).
5. Translate ONLY human-readable prose: paragraph text, headings inside \\section{{}}/\\subsection{{}}, captions, abstract text, acknowledgment text.
6. Do NOT translate these identifiers: CDCalib, detsim, elec, rec, uproot, iminuit, SNiPER, LS_FULL, ACU_DCR_FIX, codearmy, metrics.json, jheppub, pdflatex, EOS.
7. Standard physics translations:
   photoelectron(s)→光电子; dark count rate→暗计数率; liquid scintillator→液体闪烁体;
   calibration→刻度; simulation→模拟; detector→探测器; PMT→光电倍增管(PMT);
   neutrino→中微子; scintillation→闪烁; readout window→读出窗口;
   transit-time spread→渡越时间弥散; resolution→分辨率; baseline→基准线; campaign→调优活动.
8. Output ONLY the translated LaTeX fragment — no markdown fences, no explanations.
"""


def call_api(text: str, target: str, source: str = "") -> str:
    if not API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    lang_note = (f"Translate from {source} to {target}." if source
                 else f"Auto-detect source language and translate to {target}.")
    system = SYSTEM_PROMPT.format(target=target) + "\n" + lang_note
    payload = json.dumps({
        "model": "deepseek-chat", "temperature": 1.3,
        "messages": [{"role": "system", "content": system},
                     {"role": "user",   "content": text}]
    }).encode()
    req = urllib.request.Request(API_URL, data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                body = json.loads(resp.read())
                content = body["choices"][0]["message"]["content"].strip()
                content = re.sub(r"^```(?:latex)?\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
                return content
        except Exception as exc:
            print(f"  [API attempt {attempt+1}] {exc}", file=sys.stderr)
            if attempt < MAX_RETRIES - 1:
                time.sleep(4 * (attempt + 1))
            else:
                raise


def split_at_sections(tex: str):
    pattern = re.compile(r"(?=^\\(?:sub){0,2}section[\*\{])", re.MULTILINE)
    raw = pattern.split(tex)
    chunks = [("__preamble__", raw[0])]
    for part in raw[1:]:
        m = re.match(r"\\(?:sub){0,2}section\*?\{([^}]*)\}", part)
        label = m.group(1)[:40] if m else "section"
        chunks.append((label, part))
    return chunks


def translate_preamble(chunk: str, target: str, source: str) -> str:
    def xlat(text, desc):
        print(f"    → {desc} ({len(text)} chars)", file=sys.stderr)
        return call_api(text, target, source)

    def repl_title(m):
        return f"\\title{{{xlat(m.group(1), 'title')}}}"
    chunk = re.sub(r"\\title\{((?:[^{}]|\n)*?)\}", repl_title, chunk, flags=re.DOTALL)

    def repl_abstract_jhep(m):
        return f"\\abstract{{%\n{xlat(m.group(1), 'abstract')}}}"
    chunk = re.sub(r"\\abstract\{%\n((?:[^{}]|\n)*?)\}", repl_abstract_jhep, chunk, flags=re.DOTALL)

    def repl_abstract_plain(m):
        return f"\\abstract{{{xlat(m.group(1), 'abstract')}}}"
    chunk = re.sub(r"\\abstract\{((?:[^{}]|\n)*?)\}", repl_abstract_plain, chunk, flags=re.DOTALL)

    def repl_keywords(m):
        return f"\\keywords{{{xlat(m.group(1), 'keywords')}}}"
    chunk = re.sub(r"\\keywords\{((?:[^{}]|\n)*?)\}", repl_keywords, chunk, flags=re.DOTALL)

    return chunk


def translate_section(label: str, chunk: str, target: str, source: str) -> str:
    if len(chunk) <= SEGMENT_MAX_CHARS:
        print(f"  [{label}] {len(chunk)} chars", file=sys.stderr)
        return call_api(chunk, target, source)
    paragraphs = re.split(r"\n{2,}", chunk)
    results, current = [], ""
    seg = 0
    for para in paragraphs:
        if len(current) + len(para) + 2 <= SEGMENT_MAX_CHARS:
            current = (current + "\n\n" + para) if current else para
        else:
            if current:
                seg += 1
                print(f"  [{label}] sub-seg {seg} ({len(current)} chars)", file=sys.stderr)
                results.append(call_api(current, target, source)); time.sleep(1)
            current = para
    if current:
        seg += 1
        print(f"  [{label}] sub-seg {seg} ({len(current)} chars)", file=sys.stderr)
        results.append(call_api(current, target, source))
    return "\n\n".join(results)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True)
    p.add_argument("--source", default="")
    p.add_argument("--input",  required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    with open(args.input, encoding="utf-8") as f:
        tex = f.read()

    chunks = split_at_sections(tex)
    n = len(chunks)
    print(f"Split into {n} chunks.", file=sys.stderr)
    results = [None] * n

    # Preamble always first (sequential, has sub-calls)
    preamble_idx = next((i for i, (l, _) in enumerate(chunks) if l == "__preamble__"), None)
    if preamble_idx is not None:
        label, chunk = chunks[preamble_idx]
        print(f"[preamble] translating...", file=sys.stderr)
        results[preamble_idx] = translate_preamble(chunk, args.target, args.source)

    # All other sections concurrently (up to 10 workers)
    section_indices = [i for i, (l, _) in enumerate(chunks) if l != "__preamble__"]
    def _translate_section(i):
        label, chunk = chunks[i]
        print(f"[{i+1}/{n}] {label}", file=sys.stderr)
        return i, translate_section(label, chunk, args.target, args.source)

    failed = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_translate_section, i): i for i in section_indices}
        for fut in as_completed(futures):
            try:
                i, res = fut.result()
                results[i] = res
                print(f"  ✓ [{i+1}/{n}] done", file=sys.stderr)
            except Exception as exc:
                idx = futures[fut]
                label = chunks[idx][0]
                print(f"  ✗ [{idx+1}/{n}] {label}: {exc}", file=sys.stderr)
                failed.append(idx)
                results[idx] = chunks[idx][1]  # keep original on failure

    if failed:
        print(f"WARNING: {len(failed)} chunk(s) failed; original text kept.", file=sys.stderr)
    total = n

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(json.dumps({"output_file": args.output, "input_file": args.input,
                      "source_lang": args.source or "auto",
                      "target_lang": args.target, "segments": total}))


if __name__ == "__main__":
    main()
