import sys
import io
import pandas as pd
import streamlit as st

sys.path.insert(0, "backend")
from matcher import match_tier1, match_tier2, match_tier3
from utils import export_results_to_excel, read_file_to_df, validate_salesforce_df

# ─── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="STIM Client Matcher",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    #MainMenu, footer, header { visibility: hidden; }

    .main .block-container {
        max-width: 1050px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }

    /* App header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    .app-logo {
        width: 38px; height: 38px;
        background: #2563eb;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem;
    }
    .app-title { font-size: 1.1rem; font-weight: 700; color: #111827; margin: 0; }
    .app-subtitle { font-size: 0.75rem; color: #9ca3af; margin: 0; }

    /* Stepper */
    .stepper {
        display: flex;
        align-items: center;
        margin-bottom: 1.75rem;
        overflow-x: auto;
        padding-bottom: 4px;
    }
    .step-wrap { display: flex; align-items: center; white-space: nowrap; }
    .step-circle {
        width: 30px; height: 30px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 0.78rem; font-weight: 600; flex-shrink: 0;
    }
    .step-circle.done  { background: #2563eb; color: #fff; }
    .step-circle.cur   { background: #2563eb; color: #fff;
                         box-shadow: 0 0 0 4px #dbeafe; }
    .step-circle.pend  { background: #e5e7eb; color: #9ca3af; }
    .step-label { font-size: 0.78rem; font-weight: 500;
                  margin-left: 6px; margin-right: 4px; }
    .step-label.done, .step-label.cur { color: #374151; }
    .step-label.pend  { color: #9ca3af; }
    .step-line { flex: 1; height: 2px; background: #e5e7eb;
                 min-width: 24px; margin: 0 6px; }
    .step-line.done { background: #2563eb; }

    /* Tier cards */
    .tier-card {
        border: 2px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.25rem 1.25rem 1rem;
        background: #fff;
        transition: border-color 0.15s, box-shadow 0.15s;
        height: 100%;
    }
    .tier-card.selected {
        border-color: #2563eb;
        background: #eff6ff;
        box-shadow: 0 0 0 3px #dbeafe;
    }
    .tier-badge {
        display: inline-block;
        padding: 2px 9px;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .tier-title { font-size: 0.95rem; font-weight: 700;
                  color: #111827; margin: 0 0 0.35rem; }
    .tier-desc  { font-size: 0.78rem; color: #6b7280; line-height: 1.5; margin: 0; }

    /* Section card */
    .section-card {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.25rem;
    }
    .section-title {
        font-size: 1rem; font-weight: 700; color: #111827;
        margin: 0 0 0.2rem;
    }
    .section-sub {
        font-size: 0.78rem; color: #9ca3af; margin: 0 0 1rem;
    }

    /* Nav buttons row */
    .nav-row { display: flex; justify-content: space-between;
               align-items: center; margin-top: 1.25rem; }

    /* Score badges */
    .score-high { background: #dcfce7; color: #166534;
                  border-radius: 4px; padding: 1px 7px;
                  font-size: 0.78rem; font-weight: 600; }
    .score-mid  { background: #fef9c3; color: #854d0e;
                  border-radius: 4px; padding: 1px 7px;
                  font-size: 0.78rem; font-weight: 600; }
    .score-low  { background: #fee2e2; color: #991b1b;
                  border-radius: 4px; padding: 1px 7px;
                  font-size: 0.78rem; font-weight: 600; }

    /* Dataframe row highlighting */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* Hide default expander arrow shift */
    div[data-testid="stExpander"] { border: 1px solid #e5e7eb;
                                    border-radius: 10px; overflow: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


# ─── Session state ────────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "step": 1,
        "tier": None,
        "sf_df": None,
        "sf_name": None,
        "sf_row_count": 0,
        "sf_file_id": None,
        "match_df": None,
        "match_name": None,
        "match_row_count": 0,
        "match_file_id": None,
        "results": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init()

ss = st.session_state  # shorthand


# ─── Helper: render stepper ───────────────────────────────────────────────────────
def _stepper(current: int):
    steps = [
        (1, "Choose Tier"),
        (2, "Salesforce Export"),
        (3, "Matching File"),
        (4, "Run Matching"),
        (5, "Results"),
    ]
    parts = []
    for i, (sid, label) in enumerate(steps):
        if sid < current:
            cls_c, cls_l, sym = "done", "done", "✓"
        elif sid == current:
            cls_c, cls_l, sym = "cur", "cur", str(sid)
        else:
            cls_c, cls_l, sym = "pend", "pend", str(sid)

        parts.append(
            f'<div class="step-wrap">'
            f'<span class="step-circle {cls_c}">{sym}</span>'
            f'<span class="step-label {cls_l}">{label}</span>'
            f"</div>"
        )
        if i < len(steps) - 1:
            line_cls = "done" if sid < current else ""
            parts.append(f'<div class="step-line {line_cls}"></div>')

    st.markdown(
        f'<div class="stepper">{"".join(parts)}</div>', unsafe_allow_html=True
    )


# ─── Helper: preview table ───────────────────────────────────────────────────────
def _preview(df: pd.DataFrame, n: int = 5):
    st.dataframe(df.head(n), width="stretch", hide_index=True)


# ─── Helper: build flat results df ──────────────────────────────────────────────
def _build_results_df(results: list[dict], best_only: bool = False) -> pd.DataFrame:
    rows = []
    for item in results:
        candidates = item.get("candidates", [])
        top = candidates[:1] if best_only else candidates
        if not top:
            rows.append(
                {
                    **item["input"],
                    "Score": None,
                    "Method": "",
                    "SF Organisation Number": "",
                    "SF Account Name": "— No match found —",
                    "SF Primary City": "",
                    "SF Status": "",
                }
            )
        else:
            for cand in top:
                rows.append(
                    {
                        **item["input"],
                        "Score": cand["score"],
                        "Method": cand["method"],
                        "SF Organisation Number": cand["org_nr"],
                        "SF Account Name": cand["account_name"],
                        "SF Primary City": cand["city"],
                        "SF Status": cand["status"],
                    }
                )
    return pd.DataFrame(rows)


# ─── Helper: style results df ───────────────────────────────────────────────────
def _style_results(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    import math

    # Keep raw numeric scores for row colouring before we convert to strings.
    raw_scores: pd.Series = pd.Series(dtype=object)
    if "Score" in df.columns:
        raw_scores = df["Score"].reset_index(drop=True)

    # Work on a display copy where Score is already a formatted string.
    # This completely avoids the Styler .format() path and any NaN-to-int crash.
    disp = df.copy().reset_index(drop=True)
    if "Score" in disp.columns:

        def _fmt(v):
            try:
                if v is None or v == "":
                    return ""
                fv = float(v)
                return "" if math.isnan(fv) else f"{int(fv)}%"
            except (TypeError, ValueError):
                return str(v) if v is not None else ""

        disp["Score"] = disp["Score"].apply(_fmt)

    def row_color(row):
        try:
            raw = raw_scores.iat[row.name]
            if raw is None or raw == "":
                raise ValueError
            s = float(raw)
            if math.isnan(s):
                raise ValueError
        except (TypeError, ValueError, IndexError):
            return ["background-color: #f9fafb"] * len(row)
        if s >= 90:
            bg = "#f0fdf4"
        elif s >= 70:
            bg = "#fefce8"
        else:
            bg = "#fff1f2"
        return [f"background-color: {bg}"] * len(row)

    return disp.style.apply(row_color, axis=1)


# ─── APP HEADER ──────────────────────────────────────────────────────────────────
hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.markdown(
        """
        <div class="app-header">
          <div class="app-logo">🔍</div>
          <div>
            <p class="app-title">STIM Client Matcher</p>
            <p class="app-subtitle">Salesforce record matching tool</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hcol2:
    if ss.step > 1:
        if st.button("↺ Start over", use_container_width=True):
            for k in list(ss.keys()):
                del st.session_state[k]
            st.rerun()

_stepper(ss.step)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Choose tier
# ═══════════════════════════════════════════════════════════════════════════════
if ss.step == 1:
    st.markdown(
        '<div class="section-card">'
        '<p class="section-title">Choose matching tier</p>'
        '<p class="section-sub">Select the method based on what data you have available.</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    tier_defs = [
        (
            1,
            "Tier 1",
            "Organisation Number",
            "Deterministic match on org number. Fastest and highest confidence.",
            "#dcfce7",
            "#166534",
            "Exact match",
        ),
        (
            2,
            "Tier 2",
            "Name + City",
            "Fuzzy match on company name with city as a disambiguation boost.",
            "#dbeafe",
            "#1e40af",
            "Fuzzy + boost",
        ),
        (
            3,
            "Tier 3",
            "Name Only",
            "Fuzzy match on company name only. Lowest confidence — most review needed.",
            "#fef3c7",
            "#92400e",
            "Fuzzy only",
        ),
    ]

    cols = st.columns(3, gap="medium")
    for (tid, tlabel, ttitle, tdesc, bg, fg, badge), col in zip(tier_defs, cols):
        with col:
            sel = ss.tier == tid
            card_cls = "tier-card selected" if sel else "tier-card"
            st.markdown(
                f"""
                <div class="{card_cls}">
                  <span class="tier-badge" style="background:{bg};color:{fg};">{badge}</span>
                  <div style="font-size:0.65rem;font-weight:700;letter-spacing:.06em;
                              color:#9ca3af;text-transform:uppercase;margin-bottom:4px;">
                    {tlabel}
                  </div>
                  <p class="tier-title">{ttitle}</p>
                  <p class="tier-desc">{tdesc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            btn_label = "✓ Selected" if sel else "Select"
            btn_type = "primary" if sel else "secondary"
            if st.button(
                btn_label,
                key=f"tier_btn_{tid}",
                type=btn_type,
                use_container_width=True,
            ):
                ss.tier = tid
                st.rerun()

    st.write("")
    _, rb = st.columns([4, 1])
    with rb:
        if st.button(
            "Continue →",
            type="primary",
            use_container_width=True,
            disabled=ss.tier is None,
        ):
            ss.step = 2
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Upload Salesforce export
# ═══════════════════════════════════════════════════════════════════════════════
elif ss.step == 2:
    st.markdown(
        '<div class="section-card">'
        '<p class="section-title">Upload Salesforce export</p>'
        '<p class="section-sub">Required columns: Organisation Number · Account Name · Primary City · Status</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Drag and drop or click to upload",
        type=["xlsx", "xls", "csv"],
        key="sf_uploader",
    )

    if uploaded is not None:
        file_id = getattr(uploaded, "file_id", id(uploaded))
        if ss.sf_file_id != file_id:
            try:
                df = read_file_to_df(uploaded.read(), uploaded.name)
                missing = validate_salesforce_df(df)
                if missing:
                    st.error(f"Missing required columns: **{', '.join(missing)}**")
                else:
                    ss.sf_df = df
                    ss.sf_name = uploaded.name
                    ss.sf_row_count = len(df)
                    ss.sf_file_id = file_id
            except Exception as e:
                st.error(f"Could not read file: {e}")

    if ss.sf_df is not None:
        st.success(f"✓  **{ss.sf_name}** — {ss.sf_row_count:,} rows")
        with st.expander("Preview (first 5 rows)", expanded=True):
            _preview(ss.sf_df)

    st.write("")
    lb, _, rb = st.columns([1, 3, 1])
    with lb:
        if st.button("← Back", use_container_width=True):
            ss.step = 1
            st.rerun()
    with rb:
        if st.button(
            "Continue →",
            type="primary",
            use_container_width=True,
            disabled=ss.sf_df is None,
        ):
            ss.step = 3
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Upload match file + column mapping
# ═══════════════════════════════════════════════════════════════════════════════
elif ss.step == 3:
    # ── File upload ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-card">'
        '<p class="section-title">Upload matching file</p>'
        '<p class="section-sub">The file containing records you want to match against Salesforce.</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Drag and drop or click to upload",
        type=["xlsx", "xls", "csv"],
        key="match_uploader",
    )

    if uploaded is not None:
        file_id = getattr(uploaded, "file_id", id(uploaded))
        if ss.match_file_id != file_id:
            try:
                df = read_file_to_df(uploaded.read(), uploaded.name)
                ss.match_df = df
                ss.match_name = uploaded.name
                ss.match_row_count = len(df)
                ss.match_file_id = file_id
                # reset mappings for new file
                for k in ["map_org_nr", "map_company_name", "map_city"]:
                    if k in st.session_state:
                        del st.session_state[k]
            except Exception as e:
                st.error(f"Could not read file: {e}")

    if ss.match_df is not None:
        st.success(f"✓  **{ss.match_name}** — {ss.match_row_count:,} rows")
        with st.expander("Preview (first 5 rows)", expanded=True):
            _preview(ss.match_df)

    # ── Column mapping ────────────────────────────────────────────────────────
    if ss.match_df is not None:
        st.markdown("---")
        st.markdown(
            '<div class="section-card">'
            '<p class="section-title">Map columns</p>'
            '<p class="section-sub">Tell us which columns in your file correspond to the required fields.</p>'
            "</div>",
            unsafe_allow_html=True,
        )

        FIELD_CONFIGS = {
            1: [("org_nr", "Organisation Number", True)],
            2: [
                ("company_name", "Company Name", True),
                ("city", "City", True),
                ("org_nr", "Organisation Number", False),
            ],
            3: [
                ("company_name", "Company Name", True),
                ("org_nr", "Organisation Number", False),
            ],
        }

        columns = list(ss.match_df.columns)
        blank = "— Select column —"
        options = [blank] + columns

        for key, label, required in FIELD_CONFIGS.get(ss.tier, []):
            req_txt = " *" if required else " (optional)"
            c1, c2 = st.columns([2, 3])
            with c1:
                st.markdown(
                    f"<div style='padding-top:8px;font-size:0.88rem;"
                    f"font-weight:600;color:#374151'>{label}"
                    f"<span style='color:{'#ef4444' if required else '#9ca3af'}"
                    f";font-weight:400;font-size:0.78rem'>{req_txt}</span></div>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.selectbox(
                    label,
                    options=options,
                    key=f"map_{key}",
                    label_visibility="collapsed",
                )

        # Derive mappings from widget state
        def _get_mappings() -> dict:
            m = {}
            for key in ["org_nr", "company_name", "city"]:
                val = st.session_state.get(f"map_{key}", blank)
                if val and val != blank:
                    m[key] = val
            return m

        required_keys = {1: ["org_nr"], 2: ["company_name", "city"], 3: ["company_name"]}
        req = required_keys.get(ss.tier, [])
        current_mappings = _get_mappings()
        mapping_complete = all(current_mappings.get(k) for k in req)

    else:
        mapping_complete = False
        current_mappings = {}

    st.write("")
    lb, _, rb = st.columns([1, 3, 1])
    with lb:
        if st.button("← Back", use_container_width=True):
            ss.step = 2
            st.rerun()
    with rb:
        if st.button(
            "Run matching →",
            type="primary",
            use_container_width=True,
            disabled=not (ss.match_df is not None and mapping_complete),
        ):
            ss.results = None
            # Save resolved mappings before leaving step
            ss._mappings = _get_mappings() if ss.match_df is not None else {}
            ss.step = 4
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Run matching
# ═══════════════════════════════════════════════════════════════════════════════
elif ss.step == 4:
    st.markdown(
        '<div class="section-card">'
        '<p class="section-title">Running matching…</p>'
        f'<p class="section-sub">Processing <strong>{ss.match_row_count:,}</strong> rows '
        f"against <strong>{ss.sf_row_count:,}</strong> Salesforce records</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if ss.results is None:
        progress_bar = st.progress(0)
        status_txt = st.empty()

        input_rows = ss.match_df.to_dict(orient="records")
        sf_records = ss.sf_df.to_dict(orient="records")
        tier = ss.tier
        mappings = ss._mappings
        total = len(input_rows)

        def _cb(processed: int, total: int):
            pct = processed / total if total > 0 else 0
            progress_bar.progress(pct)
            status_txt.markdown(
                f"**{processed:,} / {total:,}** rows processed &nbsp; `{int(pct * 100)}%`"
            )

        try:
            if tier == 1:
                results = match_tier1(
                    input_rows, sf_records, mappings["org_nr"], _cb
                )
            elif tier == 2:
                results = match_tier2(
                    input_rows,
                    sf_records,
                    mappings["company_name"],
                    mappings["city"],
                    mappings.get("org_nr"),
                    _cb,
                )
            else:
                results = match_tier3(
                    input_rows, sf_records, mappings["company_name"], _cb
                )

            ss.results = results
            progress_bar.progress(1.0)
            status_txt.markdown("**✓ Matching complete!**")
            ss.step = 5
            st.rerun()

        except Exception as e:
            st.error(f"Matching failed: {e}")
            if st.button("← Back"):
                ss.step = 3
                st.rerun()
    else:
        ss.step = 5
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Results
# ═══════════════════════════════════════════════════════════════════════════════
elif ss.step == 5 and ss.results is not None:
    results = ss.results
    tier = ss.tier

    tier_labels = {1: "Tier 1 — Org Number", 2: "Tier 2 — Name + City", 3: "Tier 3 — Name Only"}

    # ── Stats ─────────────────────────────────────────────────────────────────
    total_in = len(results)
    matched = sum(1 for r in results if r.get("candidates"))
    high_conf = sum(
        1
        for r in results
        if (r.get("candidates") or [{}])[0].get("score", 0) >= 90
    )
    no_match = total_in - matched

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Input rows", f"{total_in:,}")
    c2.metric("Matched", f"{matched:,}")
    c3.metric("High confidence ≥90%", f"{high_conf:,}")
    c4.metric("No match found", f"{no_match:,}")

    # ── Export ────────────────────────────────────────────────────────────────
    st.write("")
    xlsx_bytes = export_results_to_excel(results)
    st.download_button(
        label="📥  Export to Excel",
        data=xlsx_bytes,
        file_name="match_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

    st.markdown("---")

    # ── Results table ──────────────────────────────────────────────────────────
    st.markdown(
        f"<p style='font-size:0.78rem;color:#9ca3af;margin-bottom:0.5rem'>"
        f"Matching method: <strong>{tier_labels.get(tier, '')}</strong> · "
        f"Top 3 candidates per input row · "
        f"<span style='color:#166534'>■</span> ≥90%  "
        f"<span style='color:#854d0e'>■</span> 70–89%  "
        f"<span style='color:#991b1b'>■</span> &lt;70%</p>",
        unsafe_allow_html=True,
    )

    tab_all, tab_new = st.tabs(["All matches", "Potential new clients"])

    df = _build_results_df(results, best_only=True)

    with tab_all:
        styled = _style_results(df)
        st.dataframe(styled, width="stretch", height=600, hide_index=True)

    # ── Potential new clients ──────────────────────────────────────────────────
    with tab_new:
        threshold = st.slider(
            "Consider 'not in Salesforce' when best match score is below",
            min_value=50, max_value=95, value=80, step=5,
            format="%d%%",
            help="Clients whose top candidate scores below this threshold appear in the list.",
        )

        new_rows = []
        input_cols = list(results[0]["input"].keys()) if results else []
        for item in results:
            candidates = item.get("candidates", [])
            best_score = candidates[0]["score"] if candidates else None
            if best_score is None or best_score < threshold:
                best = candidates[0] if candidates else {}
                new_rows.append({
                    **item["input"],
                    "Best Match Score": f"{best_score:.1f}%" if best_score is not None else "—",
                    "Best SF Match": best.get("account_name", ""),
                    "Best SF City": best.get("city", ""),
                })

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            st.markdown(
                f"**{len(new_rows)} client(s)** with best match score below **{threshold}%** "
                f"— likely not in Salesforce."
            )
            st.dataframe(new_df, width="stretch", hide_index=True)

            # Download just the new-clients list
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                new_df.to_excel(w, index=False, sheet_name="Potential new clients")
            st.download_button(
                label="📥  Export potential new clients",
                data=buf.getvalue(),
                file_name="potential_new_clients.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.success(f"All clients have a match ≥ {threshold}% — none flagged as new.")
