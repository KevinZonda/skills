#!/usr/bin/env python3
"""
Markdown-aware translator using DeepSeek API.

Preserves: fenced code blocks, inline code, LaTeX math, link URLs, image URLs,
HTML tags, YAML front matter.

Usage:
    translate_markdown.py --target <lang> [--source <lang>] --input <file> --output <file>

Stdout: JSON {"output_file": "...", "segments": N, ...}
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
SEGMENT_MAX_CHARS = 2500

SYSTEM_PROMPT = """\
You are a Markdown-aware translator. Translate the English text in the provided
Markdown fragment into {target}.

STRICT RULES:
1. Preserve ALL Markdown syntax verbatim: # headings markers, **bold**, *italic*,
   -, *, 1., > blockquotes, | table pipes, --- dividers.
2. Preserve ALL fenced code blocks (``` ... ```) verbatim — do NOT translate code.
3. Preserve ALL inline code (`...`) verbatim.
4. Preserve ALL LaTeX math verbatim: $...$, $$...$$, \\(...\\), \\[...\\].
5. Links [text](URL): translate ONLY the link text, keep the URL unchanged.
6. Images ![alt](URL): translate ONLY the alt text, keep the URL unchanged.
7. Preserve ALL HTML tags verbatim.
8. Preserve YAML front matter (--- ... ---) verbatim.
9. Output ONLY the translated Markdown fragment — no extra commentary.
"""


def call_api(text: str, target: str, source: str = "") -> str:
    if not API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    system = SYSTEM_PROMPT.format(target=target)
    system += ("\nTranslate from " + source + " to " + target + "." if source
               else "\nAuto-detect source language and translate to " + target + ".")
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
                return body["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            print(f"  [API attempt {attempt+1}] {exc}", file=sys.stderr)
            if attempt < MAX_RETRIES - 1:
                time.sleep(4 * (attempt + 1))
            else:
                raise


def split_markdown(text: str):
    """Split at top-level (# or ##) headings."""
    pattern = re.compile(r"(?=^#{1,2} )", re.MULTILINE)
    parts = pattern.split(text)
    chunks = []
    if parts[0].strip():
        chunks.append(("__preamble__", parts[0]))
    for part in parts[1:]:
        m = re.match(r"#{1,2} (.+)", part)
        label = m.group(1)[:40] if m else "section"
        chunks.append((label, part))
    return chunks


def translate_chunk(label: str, chunk: str, target: str, source: str) -> str:
    if len(chunk) <= SEGMENT_MAX_CHARS:
        print(f"  [{label}] {len(chunk)} chars", file=sys.stderr)
        return call_api(chunk, target, source)
    paras = re.split(r"\n{2,}", chunk)
    results, current = [], ""
    for i, para in enumerate(paras):
        if len(current) + len(para) + 2 <= SEGMENT_MAX_CHARS:
            current = (current + "\n\n" + para) if current else para
        else:
            if current:
                results.append(call_api(current, target, source)); time.sleep(1)
            current = para
    if current:
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
        text = f.read()

    chunks = split_markdown(text)
    n = len(chunks)
    print(f"Split into {n} chunks.", file=sys.stderr)
    results = [None] * n

    def _translate(i):
        label, chunk = chunks[i]
        print(f"[{i+1}/{n}] {label}", file=sys.stderr)
        return i, translate_chunk(label, chunk, args.target, args.source)

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_translate, i): i for i in range(n)}
        for fut in as_completed(futures):
            i, res = fut.result()
            results[i] = res
            print(f"  ✓ [{i+1}/{n}] done", file=sys.stderr)

    translated = results

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(translated))

    print(json.dumps({"output_file": args.output, "input_file": args.input,
                      "source_lang": args.source or "auto",
                      "target_lang": args.target, "segments": len(chunks)}))


if __name__ == "__main__":
    main()
