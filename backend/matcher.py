from rapidfuzz import fuzz, process
from utils import normalize_company_name, normalize_org_nr
from typing import Generator


def _sf_records_to_lookup(sf_records: list[dict]) -> dict:
    """Precompute normalized values for SF records."""
    for rec in sf_records:
        rec["_norm_name"] = normalize_company_name(rec.get("Account Name", ""))
        rec["_norm_org"] = normalize_org_nr(rec.get("Organisation Number", ""))
        rec["_norm_city"] = str(rec.get("Primary City", "")).strip().lower()
    return sf_records


def match_tier1(
    input_rows: list[dict],
    sf_records: list[dict],
    col_org: str,
    progress_callback=None,
) -> list[dict]:
    """Tier 1: exact org number match."""
    sf_records = _sf_records_to_lookup(sf_records)
    sf_by_org: dict[str, list[dict]] = {}
    for rec in sf_records:
        key = rec["_norm_org"]
        if key:
            sf_by_org.setdefault(key, []).append(rec)

    results = []
    total = len(input_rows)
    for i, row in enumerate(input_rows):
        input_org = normalize_org_nr(row.get(col_org, ""))
        candidates = []
        if input_org and input_org in sf_by_org:
            for sf in sf_by_org[input_org][:3]:
                candidates.append({
                    "score": 100,
                    "method": "org_nr_exact",
                    "org_nr": sf.get("Organisation Number", ""),
                    "account_name": sf.get("Account Name", ""),
                    "city": sf.get("Primary City", ""),
                    "status": sf.get("Status", ""),
                })
        results.append({"input": row, "candidates": candidates})
        if progress_callback:
            progress_callback(i + 1, total)
    return results


def match_tier2(
    input_rows: list[dict],
    sf_records: list[dict],
    col_name: str,
    col_city: str,
    col_org: str | None = None,
    progress_callback=None,
) -> list[dict]:
    """Tier 2: fuzzy name + city boost."""
    sf_records = _sf_records_to_lookup(sf_records)
    sf_norm_names = [rec["_norm_name"] for rec in sf_records]

    results = []
    total = len(input_rows)
    for i, row in enumerate(input_rows):
        input_name_norm = normalize_company_name(row.get(col_name, ""))
        input_city_norm = str(row.get(col_city, "")).strip().lower()

        if not input_name_norm:
            results.append({"input": row, "candidates": []})
            if progress_callback:
                progress_callback(i + 1, total)
            continue

        # rapidfuzz extract: returns (match, score, index)
        top_matches = process.extract(
            input_name_norm,
            sf_norm_names,
            scorer=fuzz.token_sort_ratio,
            limit=50,
        )

        scored = []
        for _, name_score, idx in top_matches:
            sf = sf_records[idx]
            city_match = input_city_norm and (input_city_norm == sf["_norm_city"])
            combined = min(name_score + (10 if city_match else 0), 100)
            scored.append((combined, name_score, sf))

        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = []
        for combined, name_score, sf in scored[:3]:
            candidates.append({
                "score": name_score,  # display the raw name score
                "method": "name+city_fuzzy",
                "org_nr": sf.get("Organisation Number", ""),
                "account_name": sf.get("Account Name", ""),
                "city": sf.get("Primary City", ""),
                "status": sf.get("Status", ""),
            })

        results.append({"input": row, "candidates": candidates})
        if progress_callback:
            progress_callback(i + 1, total)
    return results


def match_tier3(
    input_rows: list[dict],
    sf_records: list[dict],
    col_name: str,
    progress_callback=None,
) -> list[dict]:
    """Tier 3: fuzzy name only."""
    sf_records = _sf_records_to_lookup(sf_records)
    sf_norm_names = [rec["_norm_name"] for rec in sf_records]

    results = []
    total = len(input_rows)
    for i, row in enumerate(input_rows):
        input_name_norm = normalize_company_name(row.get(col_name, ""))

        if not input_name_norm:
            results.append({"input": row, "candidates": []})
            if progress_callback:
                progress_callback(i + 1, total)
            continue

        top_matches = process.extract(
            input_name_norm,
            sf_norm_names,
            scorer=fuzz.token_sort_ratio,
            limit=3,
        )

        candidates = []
        for _, score, idx in top_matches:
            sf = sf_records[idx]
            candidates.append({
                "score": score,
                "method": "name_fuzzy",
                "org_nr": sf.get("Organisation Number", ""),
                "account_name": sf.get("Account Name", ""),
                "city": sf.get("Primary City", ""),
                "status": sf.get("Status", ""),
            })

        results.append({"input": row, "candidates": candidates})
        if progress_callback:
            progress_callback(i + 1, total)
    return results
