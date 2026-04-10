---
name: academic-reference-search
description: Search academic papers, authors, and reference lists through open scholarly APIs. Use when Codex needs to find literature by keyword, title, DOI, PMID, or author; disambiguate candidate papers; expand a paper's references; or return concise citation metadata without relying on Google Scholar. For medical or biomedical searches, prefer NCBI PubMed/PMC through this skill.
---

# Academic Reference Search

## Overview

Use this skill to resolve papers from partial metadata and fetch their reference lists through open APIs. Prefer the bundled script so the search, ranking, and fallback logic stay deterministic. For medical or biomedical literature, prefer NCBI PubMed/PMC before general scholarly indexes.

## Workflow

1. Resolve the user's intent:
   - If they want author lookup, run `authors`.
   - If they want candidate papers from keywords/title/author, run `works`.
   - If they want the bibliography or references behind a paper, run `references`.
2. Prefer explicit identifiers:
   - Use `--openalex-id` when you already know the OpenAlex work ID.
   - Use `--doi` when the DOI is known.
   - Use `--pmid` when the user already has a PubMed ID.
3. Choose the source deliberately:
   - For medical, clinical, biomedical, drug, gene, protein, or PubMed-style searches, use `--source ncbi` or leave `--source auto`.
   - For general academic searches, use `--source auto` or `--source openalex`.
4. If only partial metadata exists, search with `--title` or `--query`, then add `--author` and `--year` when available to reduce ambiguity.
5. Inspect the returned candidates before citing them in a final answer. If `confidence` is `low`, say so and ask the user to confirm or choose a candidate.
6. Summarize the selected work and the returned references in human-readable citation form.

## Quick Start

Search authors:
```bash
python3 scripts/academic_reference_search.py authors \
  --query "Yoshua Bengio" \
  --format text
```

Search candidate papers:
```bash
python3 scripts/academic_reference_search.py works \
  --title "Attention Is All You Need" \
  --author "Ashish Vaswani" \
  --limit 5 \
  --format text
```

Expand a paper's references:
```bash
python3 scripts/academic_reference_search.py references \
  --title "Attention Is All You Need" \
  --author "Ashish Vaswani" \
  --pick 1 \
  --reference-limit 20 \
  --format text
```

Resolve directly from DOI:
```bash
python3 scripts/academic_reference_search.py references \
  --doi "10.1145/3292500.3330749" \
  --reference-limit 15
```

Medical search through NCBI:
```bash
python3 scripts/academic_reference_search.py references \
  --query "covid-19 vaccine myocarditis" \
  --source ncbi \
  --reference-limit 15 \
  --format text
```

## Commands

### `authors`

- Purpose: Find author candidates and their OpenAlex IDs.
- Required: `--query`
- Returns: author display name, OpenAlex ID, ORCID, works count, cited-by count

### `works`

- Purpose: Find likely papers from keyword/title/author metadata.
- Typical flags:
  - `--title` for title-heavy lookups
  - `--query` for free-text keyword searches
  - `--author` to bias/filter by author
  - `--year`, `--year-from`, `--year-to` to constrain publication date
  - `--source auto|openalex|ncbi|crossref` to steer the primary index
- Returns:
  - `author_candidates`
  - ranked `work_candidates`
  - per-candidate `score` and `score_reasons`

### `references`

- Purpose: Resolve one work, then fetch its references.
- Input priority:
  - `--openalex-id`
  - `--doi`
  - `--pmid`
  - `--title` / `--query` plus optional `--author` and `--year`
- Typical flags:
  - `--source ncbi` for medical/biomedical literature
  - `--pick N` chooses the candidate to expand after ranking
  - `--reference-limit N` caps the returned references
- Returns:
  - `selected` work
  - candidate list used for selection
  - `confidence`
  - `reference_source`
  - normalized `references`

## Environment

- Optional but recommended:
  - `ACADEMIC_API_EMAIL`: contact email for OpenAlex/Crossref polite pools
  - `OPENALEX_API_KEY`: OpenAlex API key when available
  - `NCBI_API_KEY`: NCBI E-utilities API key when available
- Without these, the script still attempts anonymous access, but rate limits may be tighter.

## Selection Rules

- Treat explicit IDs as authoritative.
- Treat PMID as the preferred explicit identifier for PubMed records.
- If a title has multiple near-identical matches, check author/year before citing the references as final.
- If `confidence` is `low`, do not silently present the result as certain.
- Prefer JSON output when another tool or script will consume the result; use text output when you want a readable shortlist in the chat.

## Fallback Behavior

- Use NCBI PubMed/PMC first for medical and biomedical searches.
- Use OpenAlex as the default primary source for general academic search and for non-medical reference expansion.
- Use Crossref as a fallback when OpenAlex or NCBI returns no usable work candidates or when a Crossref record exposes raw deposited references.
- If neither source yields a reliable match, say that clearly and return the closest candidates instead of inventing certainty.

## Resources

- Script:
  - `scripts/academic_reference_search.py`
- Reference notes:
  - `references/api-notes.md`
