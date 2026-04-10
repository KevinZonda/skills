# API Notes

This skill prefers `NCBI PubMed/PMC` for medical or biomedical literature, `OpenAlex` for general academic search and reference expansion, and `Crossref` as a fallback for work resolution.

## NCBI PubMed / PMC

- Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- Best for:
  - medical and biomedical paper search
  - PubMed ID based resolution
  - PubMed / PMC reference and citation links
- Useful patterns:
  - search PubMed: `/esearch.fcgi?db=pubmed&term=<query>&retmode=json`
  - fetch summaries: `/esummary.fcgi?db=pubmed&id=<pmid-list>&retmode=json`
  - get PubMed references for PMC-backed articles: `/elink.fcgi?dbfrom=pubmed&db=pubmed&id=<pmid>&linkname=pubmed_pubmed_refs&retmode=json`
  - get PubMed citing articles: `/elink.fcgi?dbfrom=pubmed&db=pubmed&id=<pmid>&linkname=pubmed_pubmed_citedin&retmode=json`
- Recommended env vars:
  - `ACADEMIC_API_EMAIL`: contact email included in requests
  - `NCBI_API_KEY`: optional; useful when running above the default anonymous rate
- Notes:
  - `pubmed_pubmed_refs` depends on PMC-linked full text, so some PubMed records will not expose references through this route.
  - PMID is the most stable explicit identifier for PubMed search and follow-up fetches.

## OpenAlex

- Base URL: `https://api.openalex.org`
- Best for:
  - searching authors and works
  - resolving a work by OpenAlex ID
  - expanding a work's reference list
- Useful patterns:
  - search works: `/works?search=<query>`
  - search authors: `/authors?search=<name>`
  - get a single work: `/works/W...`
  - expand references of work `W...`: `/works?filter=cited_by:W...`
  - expand citations of work `W...`: `/works?filter=cites:W...`
- Recommended env vars:
  - `ACADEMIC_API_EMAIL`: contact email for polite-pool requests
  - `OPENALEX_API_KEY`: optional; use when available to avoid stricter limits

## Crossref

- Base URL: `https://api.crossref.org`
- Best for:
  - DOI-oriented metadata
  - work search fallback when OpenAlex returns no candidates
  - raw reference strings when deposited by the publisher
- Useful query params:
  - `query.bibliographic`
  - `query.title`
  - `query.author`
  - `filter=from-pub-date:YYYY,until-pub-date:YYYY`

## Matching Guidance

- Prefer explicit IDs when available:
  - DOI
  - OpenAlex work ID
- If only title/keywords are available:
  - search works
  - inspect top candidates
  - check authors and year before trusting the selected work
- Treat low-confidence matches as ambiguous; confirm before citing them in a final answer.

## Known Limits

- OpenAlex does not preserve the paper's original in-text reference order through the API; the script returns a normalized list of referenced works.
- OpenAlex and Crossref can both contain duplicate or republished records under the same title. Use author/year checks or explicit identifiers when precision matters.
- PubMed reference expansion is asymmetric: some records have good `citedin` links and no `pubmed_refs`, depending on PMC coverage.
