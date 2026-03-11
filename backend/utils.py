import re
import io
from typing import Optional
import openpyxl
import pandas as pd


def normalize_company_name(name: str) -> str:
    """Normalize Swedish company names for matching."""
    if not name:
        return ""
    name = str(name).strip().lower()
    for suffix in [
        " ab", " hb", " kb", " ek. för.", " ek.för.",
        " ekonomisk förening", " handelsbolag",
        " kommanditbolag", " aktiebolag", " i likvidation",
        " i konkurs", " filial", " ideell förening",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_org_nr(org_nr: str) -> str:
    """Strip to digits only."""
    if not org_nr:
        return ""
    return re.sub(r"\D", "", str(org_nr).strip())


def read_file_to_df(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Read xlsx, xls, or csv into a DataFrame."""
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    df.columns = [str(c).strip() for c in df.columns]
    return df.fillna("")


SALESFORCE_REQUIRED_COLS = [
    "Organisation Number",
    "Account Name",
    "Primary City",
    "Status",
]


def validate_salesforce_df(df: pd.DataFrame) -> list[str]:
    """Return list of missing required columns."""
    missing = [c for c in SALESFORCE_REQUIRED_COLS if c not in df.columns]
    return missing


def export_results_to_excel(results: list[dict]) -> bytes:
    """Convert results list to Excel bytes."""
    rows = []
    for item in results:
        input_data = item.get("input", {})
        candidates = item.get("candidates", [])
        if not candidates:
            row = {**input_data, "Match Rank": "", "Match Score": "", "Match Method": "",
                   "SF Organisation Number": "", "SF Account Name": "",
                   "SF Primary City": "", "SF Status": "", "Note": "No match found"}
            rows.append(row)
        else:
            for rank, cand in enumerate(candidates, 1):
                row = {
                    **input_data,
                    "Match Rank": rank,
                    "Match Score": f"{cand['score']}%",
                    "Match Method": cand["method"],
                    "SF Organisation Number": cand["org_nr"],
                    "SF Account Name": cand["account_name"],
                    "SF Primary City": cand["city"],
                    "SF Status": cand["status"],
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Match Results", index=False)
        ws = writer.sheets["Match Results"]
        for col in ws.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=8)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)
    buf.seek(0)
    return buf.read()
