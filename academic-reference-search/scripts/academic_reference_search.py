#!/usr/bin/env python3
"""Search academic works, authors, and reference lists via open APIs.

Default flow:
- Search works/authors with OpenAlex
- Fall back to Crossref for work resolution when OpenAlex is empty
- Expand a work's references with OpenAlex's `cited_by` filter
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

OPENALEX_BASE = "https://api.openalex.org"
CROSSREF_BASE = "https://api.crossref.org"
NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_LIMIT = 5
DEFAULT_REFERENCE_LIMIT = 20
BIOMEDICAL_HINTS = (
    "pubmed",
    "pmid",
    "pmcid",
    "pmc",
    "biomedical",
    "medical",
    "medicine",
    "clinical",
    "patient",
    "therapy",
    "treatment",
    "disease",
    "syndrome",
    "drug",
    "vaccine",
    "gene",
    "genetic",
    "genome",
    "protein",
    "rna",
    "dna",
    "cell",
    "cancer",
    "tumor",
    "oncology",
    "epidemiology",
    "cohort",
    "trial",
    "meta-analysis",
    "systematic review",
    "covid",
    "sars-cov-2",
    "医学",
    "医药",
    "生物医学",
    "临床",
    "患者",
    "治疗",
    "药物",
    "疫苗",
    "疾病",
    "综合征",
    "病例",
    "基因",
    "蛋白",
    "肿瘤",
    "癌",
    "流行病",
)


class ApiError(RuntimeError):
    """Raised when an upstream API call fails."""


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def tokenize(value: Optional[str]) -> List[str]:
    return [token for token in normalize_text(value).split() if len(token) > 1]


def overlap_ratio(left: Optional[str], right: Optional[str]) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), 1)


def clean_doi(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    value = doi.strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    return value or None


def doi_url(doi: Optional[str]) -> Optional[str]:
    cleaned = clean_doi(doi)
    if not cleaned:
        return None
    return f"https://doi.org/{cleaned}"


def short_openalex_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.rstrip("/")
    if value.startswith("https://openalex.org/"):
        value = value.rsplit("/", 1)[-1]
    return value


def compact_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    if value.startswith("https://doi.org/"):
        return clean_doi(value)
    return value


def get_year(parts: Optional[Sequence[Sequence[int]]]) -> Optional[int]:
    if not parts or not parts[0]:
        return None
    return parts[0][0]


def first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value:
            return value
    return None


def build_query(params: Dict[str, Any]) -> str:
    clean = {key: value for key, value in params.items() if value is not None and value != ""}
    return urllib.parse.urlencode(clean, doseq=True)


def extract_year(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", value)
    if not match:
        return None
    return int(match.group(0))


def parse_pubmed_ids(articleids: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    ids: Dict[str, str] = {}
    for item in articleids:
        idtype = item.get("idtype")
        value = item.get("value")
        if idtype and value:
            ids[idtype] = value.strip()
    return ids


def looks_biomedical(*values: Optional[str]) -> bool:
    haystack = " ".join(value for value in values if value)
    lowered = haystack.lower()
    return any(hint in lowered for hint in BIOMEDICAL_HINTS)


def http_get_json(url: str, *, headers: Optional[Dict[str, str]] = None) -> Any:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = body.strip() or exc.reason
        raise ApiError(f"{exc.code} from {url}: {message}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"Network error for {url}: {exc.reason}") from exc


class OpenAlexClient:
    def __init__(self, mailto: Optional[str], api_key: Optional[str]) -> None:
        self.mailto = mailto
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        contact = self.mailto or "anonymous@example.com"
        return {
            "Accept": "application/json",
            "User-Agent": f"academic-reference-search/1.0 (mailto:{contact})",
        }

    def _url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        merged = dict(params or {})
        if self.mailto and "mailto" not in merged:
            merged["mailto"] = self.mailto
        if self.api_key and "api_key" not in merged:
            merged["api_key"] = self.api_key
        query = build_query(merged)
        if query:
            return f"{OPENALEX_BASE}{path}?{query}"
        return f"{OPENALEX_BASE}{path}"

    def get_single_work(self, work_id: str) -> Dict[str, Any]:
        oid = short_openalex_id(work_id)
        return http_get_json(self._url(f"/works/{oid}"), headers=self._headers())

    def get_work_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        params = {"filter": f"doi:{doi_url(doi) or doi}", "per-page": 1}
        payload = http_get_json(self._url("/works", params), headers=self._headers())
        results = payload.get("results", [])
        return results[0] if results else None

    def search_authors(self, query: str, limit: int) -> List[Dict[str, Any]]:
        params = {
            "search": query,
            "per-page": limit,
            "sort": "relevance_score:desc",
        }
        payload = http_get_json(self._url("/authors", params), headers=self._headers())
        return payload.get("results", [])

    def search_works(
        self,
        *,
        search: Optional[str],
        author_id: Optional[str],
        year: Optional[int],
        year_from: Optional[int],
        year_to: Optional[int],
        limit: int,
    ) -> List[Dict[str, Any]]:
        filters: List[str] = []
        if author_id:
            filters.append(f"author.id:{author_id}")
        if year is not None:
            filters.append(f"publication_year:{year}")
        else:
            if year_from is not None:
                filters.append(f"from_publication_date:{year_from}-01-01")
            if year_to is not None:
                filters.append(f"to_publication_date:{year_to}-12-31")
        params: Dict[str, Any] = {"per-page": limit}
        if search:
            params["search"] = search
            params["sort"] = "relevance_score:desc"
        else:
            params["sort"] = "cited_by_count:desc"
        if filters:
            params["filter"] = ",".join(filters)
        payload = http_get_json(self._url("/works", params), headers=self._headers())
        return payload.get("results", [])

    def get_references(self, work_id: str, limit: int) -> List[Dict[str, Any]]:
        short_id = short_openalex_id(work_id)
        params = {
            "filter": f"cited_by:{short_id}",
            "per-page": limit,
            "sort": "publication_year:asc",
        }
        payload = http_get_json(self._url("/works", params), headers=self._headers())
        return payload.get("results", [])


class CrossrefClient:
    def __init__(self, mailto: Optional[str]) -> None:
        self.mailto = mailto

    def _headers(self) -> Dict[str, str]:
        contact = self.mailto or "anonymous@example.com"
        return {
            "Accept": "application/json",
            "User-Agent": f"academic-reference-search/1.0 (mailto:{contact})",
        }

    def _url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        query = build_query(params or {})
        if query:
            return f"{CROSSREF_BASE}{path}?{query}"
        return f"{CROSSREF_BASE}{path}"

    def search_works(
        self,
        *,
        query: Optional[str],
        title: Optional[str],
        author: Optional[str],
        year: Optional[int],
        limit: int,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"rows": limit}
        if title:
            params["query.title"] = title
        elif query:
            params["query.bibliographic"] = query
        if author:
            params["query.author"] = author
        if year is not None:
            params["filter"] = f"from-pub-date:{year},until-pub-date:{year}"
        payload = http_get_json(self._url("/works", params), headers=self._headers())
        return payload.get("message", {}).get("items", [])

    def get_work_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        cleaned = clean_doi(doi)
        if not cleaned:
            return None
        try:
            payload = http_get_json(self._url(f"/works/{urllib.parse.quote(cleaned, safe='')}"), headers=self._headers())
        except ApiError:
            return None
        return payload.get("message")


class NCBIClient:
    def __init__(self, email: Optional[str], api_key: Optional[str], tool: str = "academic-reference-search") -> None:
        self.email = email
        self.api_key = api_key
        self.tool = tool

    def _headers(self) -> Dict[str, str]:
        contact = self.email or "anonymous@example.com"
        return {
            "Accept": "application/json",
            "User-Agent": f"academic-reference-search/1.0 (mailto:{contact})",
        }

    def _url(self, utility: str, params: Dict[str, Any]) -> str:
        merged = dict(params)
        merged.setdefault("tool", self.tool)
        if self.email:
            merged.setdefault("email", self.email)
        if self.api_key:
            merged.setdefault("api_key", self.api_key)
        query = build_query(merged)
        return f"{NCBI_EUTILS_BASE}/{utility}.fcgi?{query}"

    def _term(self, *, title: Optional[str], query: Optional[str], author: Optional[str]) -> str:
        parts = []
        if title:
            parts.append(f"\"{title}\"[Title]")
        elif query:
            parts.append(query)
        if author:
            parts.append(f"\"{author}\"[Author]")
        return " AND ".join(parts)

    def search_pubmed(
        self,
        *,
        title: Optional[str],
        query: Optional[str],
        author: Optional[str],
        year: Optional[int],
        year_from: Optional[int],
        year_to: Optional[int],
        limit: int,
    ) -> List[str]:
        term = self._term(title=title, query=query, author=author)
        if not term:
            return []
        params: Dict[str, Any] = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": limit,
            "sort": "relevance",
        }
        if year is not None:
            params["datetype"] = "pdat"
            params["mindate"] = str(year)
            params["maxdate"] = str(year)
        elif year_from is not None or year_to is not None:
            params["datetype"] = "pdat"
            params["mindate"] = str(year_from or 1800)
            params["maxdate"] = str(year_to or 3000)
        payload = http_get_json(self._url("esearch", params), headers=self._headers())
        return payload.get("esearchresult", {}).get("idlist", [])

    def get_summaries(self, pmids: Sequence[str]) -> List[Dict[str, Any]]:
        if not pmids:
            return []
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }
        payload = http_get_json(self._url("esummary", params), headers=self._headers())
        result = payload.get("result", {})
        uids = result.get("uids", [])
        return [result[uid] for uid in uids if uid in result]

    def get_summary(self, pmid: str) -> Optional[Dict[str, Any]]:
        summaries = self.get_summaries([pmid])
        return summaries[0] if summaries else None

    def get_references(self, pmid: str, limit: int) -> List[Dict[str, Any]]:
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_refs",
            "retmode": "json",
        }
        payload = http_get_json(self._url("elink", params), headers=self._headers())
        linksets = payload.get("linksets", [])
        if not linksets:
            return []
        linksetdbs = linksets[0].get("linksetdbs", [])
        if not linksetdbs:
            return []
        ref_ids = linksetdbs[0].get("links", [])[:limit]
        return self.get_summaries(ref_ids)


def format_openalex_author(author: Dict[str, Any]) -> Dict[str, Any]:
    institutions = author.get("last_known_institutions") or []
    return {
        "source": "openalex",
        "id": author.get("id"),
        "display_name": author.get("display_name"),
        "orcid": author.get("orcid"),
        "works_count": author.get("works_count"),
        "cited_by_count": author.get("cited_by_count"),
        "last_known_institution": institutions[0].get("display_name") if institutions else None,
        "raw": author,
    }


def summarize_authors(authorships: Optional[Sequence[Dict[str, Any]]]) -> List[str]:
    authors: List[str] = []
    for authorship in authorships or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)
    return authors


def format_openalex_work(work: Dict[str, Any]) -> Dict[str, Any]:
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    return {
        "source": "openalex",
        "id": work.get("id"),
        "openalex_id": short_openalex_id(work.get("id")),
        "title": work.get("display_name"),
        "year": work.get("publication_year"),
        "doi": compact_url(work.get("doi")),
        "doi_url": work.get("doi"),
        "type": work.get("type"),
        "authors": summarize_authors(work.get("authorships")),
        "venue": source.get("display_name"),
        "landing_page_url": first_non_empty(primary_location.get("landing_page_url"), source.get("homepage_url")),
        "pdf_url": primary_location.get("pdf_url"),
        "cited_by_count": work.get("cited_by_count"),
        "reference_count": work.get("referenced_works_count"),
        "references_available": bool(work.get("referenced_works_count")),
        "raw": work,
    }


def format_crossref_work(item: Dict[str, Any]) -> Dict[str, Any]:
    title = ""
    if item.get("title"):
        title = item["title"][0]
    authors = []
    for author in item.get("author", []):
        name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
        if name:
            authors.append(name)
    venue = None
    container = item.get("container-title") or []
    if container:
        venue = container[0]
    raw_references = item.get("reference") or []
    doi = clean_doi(item.get("DOI"))
    return {
        "source": "crossref",
        "id": doi or item.get("URL"),
        "openalex_id": None,
        "title": title,
        "year": get_year((item.get("issued") or {}).get("date-parts")),
        "doi": doi,
        "doi_url": doi_url(doi),
        "type": item.get("type"),
        "authors": authors,
        "venue": venue,
        "landing_page_url": item.get("URL"),
        "pdf_url": None,
        "cited_by_count": item.get("is-referenced-by-count"),
        "reference_count": len(raw_references) if raw_references else None,
        "references_available": bool(raw_references),
        "raw": item,
    }


def format_ncbi_pubmed_work(item: Dict[str, Any]) -> Dict[str, Any]:
    ids = parse_pubmed_ids(item.get("articleids") or [])
    authors = [author.get("name") for author in item.get("authors", []) if author.get("name")]
    pmid = item.get("uid")
    pmcid = ids.get("pmc")
    doi = clean_doi(ids.get("doi"))
    return {
        "source": "ncbi-pubmed",
        "id": f"PMID:{pmid}" if pmid else None,
        "openalex_id": None,
        "pmid": pmid,
        "pmcid": pmcid,
        "title": item.get("title"),
        "year": extract_year(first_non_empty(item.get("pubdate"), item.get("epubdate"), item.get("sortpubdate"))),
        "doi": doi,
        "doi_url": doi_url(doi),
        "type": item.get("pubtype") or item.get("doctype"),
        "authors": authors,
        "venue": item.get("fulljournalname"),
        "landing_page_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
        "pdf_url": None,
        "cited_by_count": None,
        "reference_count": None,
        "references_available": bool(pmcid),
        "raw": item,
    }


def author_match_score(work_authors: Sequence[str], target_author: Optional[str]) -> int:
    if not target_author:
        return 0
    target = normalize_text(target_author)
    if not target:
        return 0
    best = 0.0
    for author in work_authors:
        author_norm = normalize_text(author)
        if author_norm == target:
            return 35
        if target in author_norm or author_norm in target:
            best = max(best, 0.8)
        else:
            best = max(best, overlap_ratio(author_norm, target))
    return int(best * 25)


def score_work(
    work: Dict[str, Any],
    *,
    title: Optional[str],
    query: Optional[str],
    author: Optional[str],
    year: Optional[int],
    preferred_source: Optional[str],
) -> Tuple[int, List[str]]:
    reasons: List[str] = []
    score = 0
    target_text = title or query
    target_norm = normalize_text(target_text)
    title_norm = normalize_text(work.get("title"))
    if target_norm and title_norm:
        if target_norm == title_norm:
            score += 80
            reasons.append("exact-title")
        overlap = overlap_ratio(target_norm, title_norm)
        if overlap:
            score += int(overlap * 40)
            reasons.append(f"title-overlap={overlap:.2f}")
        if target_norm and target_norm in title_norm and target_norm != title_norm:
            score += 8
            reasons.append("title-contains-query")
    author_score = author_match_score(work.get("authors", []), author)
    if author_score:
        score += author_score
        reasons.append("author-match")
    work_year = work.get("year")
    if year is not None and work_year is not None:
        distance = abs(year - work_year)
        if distance == 0:
            score += 20
            reasons.append("exact-year")
        elif distance == 1:
            score += 8
            reasons.append("near-year")
        elif distance > 4:
            score -= 6
            reasons.append("year-far")
    if work.get("references_available"):
        score += 5
    if work.get("doi"):
        score += 2
    if work.get("source") == "openalex":
        score += 3
    if preferred_source and work.get("source") == preferred_source:
        score += 8
        reasons.append("preferred-source")
    return score, reasons


def selection_confidence(candidates: Sequence[Dict[str, Any]]) -> str:
    if not candidates:
        return "none"
    top = candidates[0]["score"]
    second = candidates[1]["score"] if len(candidates) > 1 else None
    if top >= 95 and (second is None or top - second >= 15):
        return "high"
    if top >= 70 and (second is None or top - second >= 8):
        return "medium"
    return "low"


def render_citation(work: Dict[str, Any]) -> str:
    authors = work.get("authors") or []
    if not authors:
        author_text = "Unknown author"
    elif len(authors) <= 3:
        author_text = ", ".join(authors)
    else:
        author_text = ", ".join(authors[:3]) + ", et al."
    pieces = [author_text]
    if work.get("year"):
        pieces.append(f"({work['year']})")
    if work.get("title"):
        pieces.append(work["title"])
    if work.get("venue"):
        pieces.append(work["venue"])
    if work.get("doi"):
        pieces.append(f"DOI:{work['doi']}")
    return ". ".join(piece for piece in pieces if piece).strip()


def rank_works(
    works: Sequence[Dict[str, Any]],
    *,
    title: Optional[str],
    query: Optional[str],
    author: Optional[str],
    year: Optional[int],
    preferred_source: Optional[str],
) -> List[Dict[str, Any]]:
    ranked = []
    for work in works:
        score, reasons = score_work(
            work,
            title=title,
            query=query,
            author=author,
            year=year,
            preferred_source=preferred_source,
        )
        ranked.append({**work, "score": score, "score_reasons": reasons})
    ranked.sort(key=lambda item: (item["score"], item.get("reference_count") or 0, item.get("cited_by_count") or 0), reverse=True)
    return ranked


def resolve_author_id(openalex: OpenAlexClient, author: Optional[str], limit: int) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    if not author:
        return None, []
    candidates = [format_openalex_author(item) for item in openalex.search_authors(author, limit)]
    if not candidates:
        return None, []
    normalized = normalize_text(author)
    for candidate in candidates:
        if normalize_text(candidate.get("display_name")) == normalized:
            return candidate["id"], candidates
    return candidates[0]["id"], candidates


def search_work_candidates(
    openalex: OpenAlexClient,
    crossref: CrossrefClient,
    ncbi: NCBIClient,
    *,
    title: Optional[str],
    query: Optional[str],
    author: Optional[str],
    year: Optional[int],
    year_from: Optional[int],
    year_to: Optional[int],
    limit: int,
    source: str,
) -> Dict[str, Any]:
    search_text = title or query

    author_id, author_candidates = resolve_author_id(openalex, author, limit=min(limit, 5))
    if not search_text and not author:
        raise ApiError("Provide --title, --query, --author, --doi, or --openalex-id.")
    prefer_ncbi = source == "ncbi" or (source == "auto" and looks_biomedical(title, query))
    preferred_source = "ncbi-pubmed" if prefer_ncbi else "openalex"
    openalex_results: List[Dict[str, Any]] = []
    crossref_results: List[Dict[str, Any]] = []
    ncbi_results: List[Dict[str, Any]] = []

    if source in {"auto", "openalex", "ncbi"}:
        openalex_results = [
            format_openalex_work(item)
            for item in openalex.search_works(
                search=search_text,
                author_id=author_id,
                year=year,
                year_from=year_from,
                year_to=year_to,
                limit=max(limit, 5),
            )
        ]

    if source in {"auto", "crossref", "openalex", "ncbi"}:
        crossref_results = [
            format_crossref_work(item)
            for item in crossref.search_works(
                query=query or title or author,
                title=title,
                author=author,
                year=year,
                limit=max(limit, 5),
            )
        ]

    if source in {"auto", "ncbi"} and (prefer_ncbi or source == "ncbi"):
        ncbi_results = [
            format_ncbi_pubmed_work(item)
            for item in ncbi.get_summaries(
                ncbi.search_pubmed(
                    title=title,
                    query=query,
                    author=author,
                    year=year,
                    year_from=year_from,
                    year_to=year_to,
                    limit=max(limit, 5),
                )
            )
        ]

    ranked = rank_works(
        ncbi_results + openalex_results + crossref_results,
        title=title,
        query=query,
        author=author,
        year=year,
        preferred_source=preferred_source,
    )
    return {
        "preferred_source": preferred_source,
        "author_filter_id": author_id,
        "author_candidates": author_candidates,
        "work_candidates": ranked[:limit],
    }


def crossref_references_as_works(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    output = []
    for reference in item.get("reference", []):
        title = first_non_empty(reference.get("article-title"), reference.get("series-title"), reference.get("volume-title"), reference.get("journal-title"), reference.get("unstructured"))
        authors = []
        if reference.get("author"):
            authors.append(reference["author"])
        doi = clean_doi(reference.get("DOI"))
        output.append(
            {
                "source": "crossref-reference",
                "id": doi or reference.get("key"),
                "openalex_id": None,
                "title": title,
                "year": reference.get("year"),
                "doi": doi,
                "doi_url": doi_url(doi),
                "type": None,
                "authors": authors,
                "venue": reference.get("journal-title"),
                "landing_page_url": doi_url(doi),
                "pdf_url": None,
                "cited_by_count": None,
                "reference_count": None,
                "references_available": False,
                "raw": reference,
            }
        )
    return output


def resolve_work(
    openalex: OpenAlexClient,
    crossref: CrossrefClient,
    ncbi: NCBIClient,
    *,
    openalex_id: Optional[str],
    doi: Optional[str],
    pmid: Optional[str],
    title: Optional[str],
    query: Optional[str],
    author: Optional[str],
    year: Optional[int],
    year_from: Optional[int],
    year_to: Optional[int],
    limit: int,
    pick: int,
    source: str,
) -> Dict[str, Any]:
    if openalex_id:
        work = format_openalex_work(openalex.get_single_work(openalex_id))
        return {
            "selected": {**work, "score": 999, "score_reasons": ["explicit-openalex-id"]},
            "confidence": "explicit",
            "work_candidates": [{**work, "score": 999, "score_reasons": ["explicit-openalex-id"]}],
            "author_candidates": [],
        }
    if doi:
        openalex_hit = openalex.get_work_by_doi(doi)
        if openalex_hit:
            work = format_openalex_work(openalex_hit)
            return {
                "selected": {**work, "score": 999, "score_reasons": ["explicit-doi-openalex"]},
                "confidence": "explicit",
                "work_candidates": [{**work, "score": 999, "score_reasons": ["explicit-doi-openalex"]}],
                "author_candidates": [],
            }
        crossref_hit = crossref.get_work_by_doi(doi)
        if crossref_hit:
            work = format_crossref_work(crossref_hit)
            return {
                "selected": {**work, "score": 999, "score_reasons": ["explicit-doi-crossref"]},
                "confidence": "explicit",
            "work_candidates": [{**work, "score": 999, "score_reasons": ["explicit-doi-crossref"]}],
            "author_candidates": [],
        }
        raise ApiError(f"No work found for DOI {doi}.")
    if pmid:
        summary = ncbi.get_summary(pmid)
        if not summary:
            raise ApiError(f"No PubMed record found for PMID {pmid}.")
        work = format_ncbi_pubmed_work(summary)
        return {
            "selected": {**work, "score": 999, "score_reasons": ["explicit-pmid"]},
            "confidence": "explicit",
            "work_candidates": [{**work, "score": 999, "score_reasons": ["explicit-pmid"]}],
            "author_candidates": [],
        }

    search_result = search_work_candidates(
        openalex,
        crossref,
        ncbi,
        title=title,
        query=query,
        author=author,
        year=year,
        year_from=year_from,
        year_to=year_to,
        limit=limit,
        source=source,
    )
    candidates = search_result["work_candidates"]
    if not candidates:
        raise ApiError("No candidate works found.")
    if pick < 1 or pick > len(candidates):
        raise ApiError(f"--pick must be between 1 and {len(candidates)}.")
    selected = candidates[pick - 1]
    return {
        "selected": selected,
        "confidence": selection_confidence(candidates),
        "work_candidates": candidates,
        "author_candidates": search_result["author_candidates"],
    }


def references_for_selected(
    openalex: OpenAlexClient,
    ncbi: NCBIClient,
    selected: Dict[str, Any],
    limit: int,
) -> Tuple[List[Dict[str, Any]], str]:
    if selected.get("source") == "openalex" and selected.get("openalex_id"):
        refs = [format_openalex_work(item) for item in openalex.get_references(selected["openalex_id"], limit)]
        return refs, "openalex-cited_by"
    if selected.get("source") == "ncbi-pubmed" and selected.get("pmid"):
        refs = [format_ncbi_pubmed_work(item) for item in ncbi.get_references(selected["pmid"], limit)]
        if refs:
            return refs, "ncbi-pubmed_pubmed_refs"
    raw = selected.get("raw") or {}
    if selected.get("source") == "crossref" and raw.get("reference"):
        return crossref_references_as_works(raw)[:limit], "crossref-reference-list"
    doi = selected.get("doi")
    if doi:
        openalex_work = openalex.get_work_by_doi(doi)
        if openalex_work:
            refs = [format_openalex_work(item) for item in openalex.get_references(openalex_work["id"], limit)]
            return refs, "openalex-cited_by-via-doi"
    return [], "unavailable"


def prune_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(payload)
    if "raw" in cleaned:
        del cleaned["raw"]
    return cleaned


def render_text_lines(title: str, items: Iterable[str]) -> str:
    lines = [title]
    lines.extend(items)
    return "\n".join(lines)


def format_text_result(result: Dict[str, Any], command: str) -> str:
    if command == "authors":
        lines = []
        for idx, author in enumerate(result["authors"], 1):
            line = f"{idx}. {author['display_name']}"
            extras = []
            if author.get("orcid"):
                extras.append(f"ORCID {author['orcid']}")
            if author.get("works_count") is not None:
                extras.append(f"works={author['works_count']}")
            if author.get("cited_by_count") is not None:
                extras.append(f"cited_by={author['cited_by_count']}")
            if author.get("id"):
                extras.append(author["id"])
            if extras:
                line += " | " + " | ".join(str(extra) for extra in extras)
            lines.append(line)
        return render_text_lines("Authors", lines)

    if command == "works":
        lines = []
        for idx, work in enumerate(result["work_candidates"], 1):
            line = f"{idx}. [{work['source']}] score={work['score']} | {render_citation(work)}"
            if work.get("id"):
                line += f" | id={work['id']}"
            lines.append(line)
        if result.get("author_candidates"):
            lines.append("")
            lines.append("Resolved author candidates:")
            for idx, author in enumerate(result["author_candidates"], 1):
                lines.append(f"{idx}. {author['display_name']} | {author['id']}")
        return render_text_lines("Work candidates", lines)

    selected = result["selected"]
    lines = [
        f"Selected work [{result['confidence']} confidence]: {render_citation(selected)}",
        f"Selection source: {selected['source']} | score={selected.get('score')}",
    ]
    if result.get("work_candidates"):
        lines.append("Candidates:")
        for idx, work in enumerate(result["work_candidates"], 1):
            lines.append(f"{idx}. [{work['source']}] score={work['score']} | {render_citation(work)}")
    lines.append("")
    lines.append(f"References via {result['reference_source']}:")
    for idx, reference in enumerate(result["references"], 1):
        lines.append(f"{idx}. {render_citation(reference)}")
    return "\n".join(lines)


def emit_result(result: Dict[str, Any], fmt: str, command: str) -> None:
    if fmt == "json":
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    print(format_text_result(result, command))


def add_shared_work_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--query", help="Free-text query or keywords")
    parser.add_argument("--title", help="Title-focused query")
    parser.add_argument("--author", help="Author name to bias or filter results")
    parser.add_argument("--year", type=int, help="Exact publication year")
    parser.add_argument("--year-from", type=int, help="Lower year bound")
    parser.add_argument("--year-to", type=int, help="Upper year bound")
    parser.add_argument("--source", choices=["auto", "openalex", "ncbi", "crossref"], default="auto", help="Primary search source")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of candidates to return")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--mailto", help="Contact email for OpenAlex/Crossref polite pools")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    authors = subparsers.add_parser("authors", help="Search authors by name")
    authors.add_argument("--query", required=True, help="Author name query")
    authors.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of author candidates")
    authors.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    authors.add_argument("--mailto", help="Contact email for OpenAlex polite pool")

    works = subparsers.add_parser("works", help="Search works by keyword/title/author")
    add_shared_work_args(works)

    references = subparsers.add_parser("references", help="Resolve a work and expand its references")
    add_shared_work_args(references)
    references.add_argument("--doi", help="Explicit DOI")
    references.add_argument("--openalex-id", help="Explicit OpenAlex work ID or URL")
    references.add_argument("--pmid", help="Explicit PubMed ID")
    references.add_argument("--pick", type=int, default=1, help="1-based candidate index to expand")
    references.add_argument("--reference-limit", type=int, default=DEFAULT_REFERENCE_LIMIT, help="Number of references to return")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    mailto = args.mailto or os.environ.get("ACADEMIC_API_EMAIL")
    openalex = OpenAlexClient(mailto=mailto, api_key=os.environ.get("OPENALEX_API_KEY"))
    crossref = CrossrefClient(mailto=mailto)
    ncbi = NCBIClient(email=mailto, api_key=os.environ.get("NCBI_API_KEY"))

    try:
        if args.command == "authors":
            result = {
                "query": args.query,
                "authors": [prune_payload(format_openalex_author(item)) for item in openalex.search_authors(args.query, args.limit)],
            }
            emit_result(result, args.format, args.command)
            return 0

        if args.command == "works":
            result = search_work_candidates(
                openalex,
                crossref,
                ncbi,
                title=args.title,
                query=args.query,
                author=args.author,
                year=args.year,
                year_from=args.year_from,
                year_to=args.year_to,
                limit=args.limit,
                source=args.source,
            )
            result["work_candidates"] = [prune_payload(item) for item in result["work_candidates"]]
            result["author_candidates"] = [prune_payload(item) for item in result["author_candidates"]]
            emit_result(result, args.format, args.command)
            return 0

        resolved = resolve_work(
            openalex,
            crossref,
            ncbi,
            openalex_id=args.openalex_id,
            doi=args.doi,
            pmid=args.pmid,
            title=args.title,
            query=args.query,
            author=args.author,
            year=args.year,
            year_from=args.year_from,
            year_to=args.year_to,
            limit=args.limit,
            pick=args.pick,
            source=args.source,
        )
        references, reference_source = references_for_selected(openalex, ncbi, resolved["selected"], args.reference_limit)
        result = {
            "selected": prune_payload(resolved["selected"]),
            "confidence": resolved["confidence"],
            "work_candidates": [prune_payload(item) for item in resolved["work_candidates"]],
            "author_candidates": [prune_payload(item) for item in resolved["author_candidates"]],
            "reference_source": reference_source,
            "references": [prune_payload(item) for item in references],
        }
        emit_result(result, args.format, args.command)
        return 0
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
