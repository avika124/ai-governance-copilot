"""
Global AI Governance Copilot — Streamlit UI.

Premium dark-mode dashboard with card-based output, source-grounded
evidence, and professional governance language.

Run: streamlit run app/ui/app.py
"""

import json
import os
import sys
from pathlib import Path

# Project root on path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
import streamlit as st

DEFAULT_API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Governance Copilot",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS Design System
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ---------- Google Font ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ---------- Root Variables ---------- */
    :root {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-card: rgba(30, 41, 59, 0.85);
        --bg-card-hover: rgba(30, 41, 59, 0.95);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-blue: #3b82f6;
        --accent-indigo: #6366f1;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-rose: #f43f5e;
        --border-subtle: rgba(148, 163, 184, 0.12);
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.25);
        --radius: 12px;
    }

    /* ---------- Global Overrides ---------- */
    .stApp {
        background: linear-gradient(160deg, var(--bg-primary) 0%, #1e1b4b 100%) !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }

    /* Make sidebar blend */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    section[data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* ---------- Header ---------- */
    .gov-header {
        text-align: center;
        padding: 1.5rem 0 0.75rem;
    }
    .gov-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2rem;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .gov-subtitle {
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin-top: 0.35rem;
        font-weight: 400;
    }

    /* ---------- Card System ---------- */
    .gov-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border-radius: var(--radius);
        border: 1px solid var(--border-subtle);
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-card);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .gov-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
        background: var(--bg-card-hover);
    }
    .gov-card-title {
        font-weight: 600;
        font-size: 1rem;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .gov-card-body {
        color: var(--text-secondary);
        font-size: 0.875rem;
        line-height: 1.6;
    }

    /* ---------- Hero Metric Cards ---------- */
    .hero-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.25rem;
    }
    .hero-metric {
        flex: 1;
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border-radius: var(--radius);
        border: 1px solid var(--border-subtle);
        padding: 1.25rem;
        text-align: center;
        box-shadow: var(--shadow-card);
    }
    .hero-metric .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.25rem 0;
    }
    .hero-metric .metric-label {
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    .metric-blue   .metric-value { color: var(--accent-blue); }
    .metric-green  .metric-value { color: var(--accent-emerald); }
    .metric-amber  .metric-value { color: var(--accent-amber); }
    .metric-rose   .metric-value { color: var(--accent-rose); }

    /* ---------- Coverage Grid ---------- */
    .cov-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 0.75rem;
    }
    .cov-cell {
        background: var(--bg-card);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid var(--border-subtle);
    }
    .cov-cell.covered {
        border-left: 3px solid var(--accent-emerald);
    }
    .cov-cell.gap {
        border-left: 3px solid var(--accent-rose);
    }
    .cov-risk {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .cov-area {
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-primary);
        margin-bottom: 0.35rem;
    }
    .cov-evidence {
        font-size: 0.8rem;
        color: var(--text-secondary);
        font-style: italic;
    }
    .cov-badge-covered {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-emerald);
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .cov-badge-gap {
        display: inline-block;
        background: rgba(244, 63, 94, 0.15);
        color: var(--accent-rose);
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
    }

    /* ---------- Conflict Cards ---------- */
    .conflict-card {
        background: var(--bg-card);
        border-radius: var(--radius);
        border: 1px solid var(--border-subtle);
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        box-shadow: var(--shadow-card);
    }
    .conflict-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    .severity-badge {
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .severity-high   { background: rgba(244, 63, 94, 0.18); color: #fb7185; }
    .severity-medium { background: rgba(245, 158, 11, 0.18); color: #fbbf24; }
    .severity-low    { background: rgba(16, 185, 129, 0.18); color: #34d399; }

    .conflict-ref {
        font-size: 0.8rem;
        color: var(--text-muted);
    }
    .conflict-ref strong {
        color: var(--text-secondary);
    }
    .conflict-desc {
        font-size: 0.875rem;
        color: var(--text-secondary);
        line-height: 1.55;
        margin-bottom: 0.5rem;
    }
    .sim-bar-bg {
        height: 6px;
        background: rgba(148, 163, 184, 0.15);
        border-radius: 3px;
        overflow: hidden;
        margin-top: 0.4rem;
    }
    .sim-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.4s ease;
    }

    /* ---------- Policy Option Cards ---------- */
    .policy-card {
        background: var(--bg-card);
        border-radius: var(--radius);
        border: 1px solid var(--border-subtle);
        padding: 1.5rem;
        height: 100%;
        box-shadow: var(--shadow-card);
        transition: transform 0.2s ease;
    }
    .policy-card:hover {
        transform: translateY(-3px);
    }
    .policy-card.tier-minimal  { border-top: 3px solid var(--accent-emerald); }
    .policy-card.tier-moderate { border-top: 3px solid var(--accent-blue); }
    .policy-card.tier-strict   { border-top: 3px solid var(--accent-indigo); }
    .policy-title {
        font-weight: 700;
        font-size: 1rem;
        color: var(--text-primary);
        margin-bottom: 0.65rem;
    }
    .policy-summary {
        font-size: 0.85rem;
        color: var(--text-secondary);
        line-height: 1.55;
        margin-bottom: 0.75rem;
    }
    .policy-sample {
        font-size: 0.8rem;
        color: var(--text-muted);
        font-style: italic;
        border-left: 2px solid var(--border-subtle);
        padding-left: 0.75rem;
        line-height: 1.5;
    }

    /* ---------- Pill Badges ---------- */
    .pill {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-bottom: 0.25rem;
    }
    .pill-risk       { background: rgba(244, 63, 94, 0.12); color: #fb7185; }
    .pill-actor      { background: rgba(59, 130, 246, 0.12); color: #60a5fa; }
    .pill-obligation { background: rgba(168, 85, 247, 0.12); color: #c084fc; }

    /* ---------- Section Headers ---------- */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.15rem;
        color: var(--text-primary);
        margin: 1.75rem 0 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-divider {
        height: 1px;
        background: var(--border-subtle);
        margin: 0.25rem 0 1rem;
    }

    /* ---------- Status Indicators ---------- */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-ok   { background: var(--accent-emerald); box-shadow: 0 0 6px rgba(16, 185, 129, 0.4); }
    .status-err  { background: var(--accent-rose); box-shadow: 0 0 6px rgba(244, 63, 94, 0.4); }

    /* ---------- Connection Error ---------- */
    .error-card {
        background: rgba(244, 63, 94, 0.08);
        border: 1px solid rgba(244, 63, 94, 0.25);
        border-radius: var(--radius);
        padding: 1.5rem;
        text-align: center;
    }
    .error-card h3 {
        color: #fb7185;
        margin-bottom: 0.5rem;
    }
    .error-card p {
        color: var(--text-secondary);
        font-size: 0.875rem;
    }

    /* ---------- Misc Overrides ---------- */
    .stTextArea textarea {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
    }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-indigo) 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.6rem 1.5rem !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .stButton>button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4) !important;
    }
    .stDownloadButton>button {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius) !important;
    }

    /* ---------- Empty State ---------- */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: var(--text-muted);
    }
    .empty-state .icon {
        font-size: 3rem;
        margin-bottom: 0.75rem;
    }
    .empty-state p {
        font-size: 0.9rem;
        line-height: 1.5;
        max-width: 480px;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="gov-header">
        <h1>⚖️  Global AI Governance Copilot</h1>
        <p class="gov-subtitle">
            Analyse draft AI policy text against EU &amp; India legal corpora —
            coverage gaps, cross-border conflict signals, and policy option cards
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_base = st.text_input("API base URL", value=DEFAULT_API)

    # Health check
    api_ok = False
    db_ok = False
    faiss_count = 0
    try:
        h = requests.get(f"{api_base.rstrip('/')}/health", timeout=3).json()
        api_ok = h.get("api") == "ok"
        db_ok = h.get("database") == "ok"
        faiss_count = h.get("faiss_vectors", 0)
    except Exception:
        pass

    dot_api = "status-ok" if api_ok else "status-err"
    dot_db = "status-ok" if db_ok else "status-err"
    st.markdown(
        f'<span class="status-dot {dot_api}"></span> API: **{"Connected" if api_ok else "Unreachable"}**',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="status-dot {dot_db}"></span> Database: **{"Connected" if db_ok else "Unreachable"}**',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"📊 FAISS Index: **{faiss_count:,}** vectors",
    )

    st.divider()
    st.markdown("**Reference Corpora**")
    st.markdown("- [EUR-Lex (EU AI Act)](https://eur-lex.europa.eu)")
    st.markdown("- [India Code](https://www.indiacode.nic.in)")
    st.markdown("- [legislative.gov.in](https://legislative.gov.in)")
    st.divider()
    st.caption("Start the API: `uvicorn app.api.main:app --reload`")

# ---------------------------------------------------------------------------
# Input Area
# ---------------------------------------------------------------------------
draft = st.text_area(
    "Paste draft AI policy text",
    height=200,
    placeholder=(
        "Enter clauses describing obligations, incident reporting, data handling, "
        "testing, risk management, transparency, etc."
    ),
)

# Character counter
char_count = len(draft)
if char_count > 0:
    color = "#10b981" if char_count < 80_000 else ("#f59e0b" if char_count < 100_000 else "#f43f5e")
    st.markdown(
        f'<p style="text-align:right; font-size:0.75rem; color:{color}; margin-top:-0.5rem;">'
        f'{char_count:,} / 100,000 characters</p>',
        unsafe_allow_html=True,
    )

col_a, col_b = st.columns([1, 5])
with col_a:
    analyze_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _pretty_area(area_key: str) -> str:
    """Convert snake_case area key to human-readable label."""
    return area_key.replace("_", " ").title()

def _severity_class(sev: str) -> str:
    return f"severity-{sev}" if sev in ("high", "medium", "low") else "severity-low"

def _sim_color(sim: float) -> str:
    if sim >= 0.9:
        return "var(--accent-rose)"
    if sim >= 0.8:
        return "var(--accent-amber)"
    return "var(--accent-emerald)"


# ---------------------------------------------------------------------------
# Analysis Flow
# ---------------------------------------------------------------------------
if analyze_btn and draft.strip():
    # Validate locally before hitting API
    import re as _re
    cleaned = _re.sub(r"[\s\W]+", "", draft)
    if len(cleaned) < 5:
        st.markdown(
            '<div class="error-card">'
            "<h3>⚠️ Insufficient Input</h3>"
            "<p>Please paste substantive AI policy text containing clauses about obligations, "
            "risk management, reporting requirements, or similar governance language.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    if not api_ok:
        st.markdown(
            '<div class="error-card">'
            "<h3>🔌 API Unavailable</h3>"
            "<p>Cannot reach the API server. Please ensure the FastAPI backend is running:<br/>"
            "<code>uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000</code></p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    with st.spinner("Running analysis pipeline — parsing, classifying, checking coverage, detecting conflicts…"):
        try:
            r = requests.post(
                f"{api_base.rstrip('/')}/analyze",
                json={"text": draft},
                timeout=300,
            )
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.ConnectionError:
            st.markdown(
                '<div class="error-card">'
                "<h3>🔌 Connection Lost</h3>"
                "<p>Lost connection to the API during analysis. Please check the server and retry.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()
        except requests.exceptions.Timeout:
            st.markdown(
                '<div class="error-card">'
                "<h3>⏱️ Request Timed Out</h3>"
                "<p>The analysis took longer than expected. This may happen on first run while "
                "embedding models are loading. Please retry.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()
        except Exception as e:
            st.markdown(
                '<div class="error-card">'
                f"<h3>❌ Analysis Error</h3>"
                f"<p>{e}</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()

    # -----------------------------------------------------------------------
    # Executive Summary — hero metric cards
    # -----------------------------------------------------------------------
    clause_count = data.get("clause_count", 0)
    cov = data.get("coverage", {})
    summ = cov.get("summary", {})
    cov_frac = summ.get("fraction", 0)
    conf = data.get("conflicts", {})
    conf_count = conf.get("count", 0)
    conf_items = conf.get("items", [])
    rec = data.get("recommendations", {})

    st.markdown('<div class="section-header">📋 Executive Summary</div><div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="hero-row">
            <div class="hero-metric metric-blue">
                <div class="metric-label">Clauses Parsed</div>
                <div class="metric-value">{clause_count}</div>
            </div>
            <div class="hero-metric metric-green">
                <div class="metric-label">Coverage Score</div>
                <div class="metric-value">{cov_frac*100:.0f}%</div>
                <div style="font-size:0.75rem;color:var(--text-muted);">{summ.get('covered',0)} / {summ.get('total',0)} sub-areas</div>
            </div>
            <div class="hero-metric {'metric-rose' if conf_count > 0 else 'metric-green'}">
                <div class="metric-label">Conflict Signals</div>
                <div class="metric-value">{conf_count}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Coverage Matrix
    # -----------------------------------------------------------------------
    grid = cov.get("grid", {})
    if grid:
        st.markdown('<div class="section-header">🗺️ Regulatory Coverage Matrix</div><div class="section-divider"></div>', unsafe_allow_html=True)

        cells_html = ""
        for risk, areas in grid.items():
            for area, info in areas.items():
                is_covered = info.get("covered", False)
                cell_class = "covered" if is_covered else "gap"
                badge_class = "cov-badge-covered" if is_covered else "cov-badge-gap"
                badge_text = "✓ Covered" if is_covered else "✗ Gap"
                evidence = info.get("evidence", "—")
                cells_html += f"""
                <div class="cov-cell {cell_class}">
                    <div class="cov-risk">{risk}</div>
                    <div class="cov-area">{_pretty_area(area)}</div>
                    <span class="{badge_class}">{badge_text}</span>
                    <div class="cov-evidence">{evidence}</div>
                </div>
                """

        st.markdown(f'<div class="cov-grid">{cells_html}</div>', unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Conflict Signals
    # -----------------------------------------------------------------------
    st.markdown('<div class="section-header">⚡ Cross-Jurisdictional Conflict Signals</div><div class="section-divider"></div>', unsafe_allow_html=True)

    if conf_items:
        for item in conf_items:
            sev = item.get("severity", "low")
            sim = item.get("similarity", 0)
            ref_law = item.get("reference_law", "Unknown")
            ref_country = item.get("reference_country", "—")
            ref_excerpt = item.get("reference_excerpt", "")[:300]
            input_excerpt = item.get("input_excerpt", "")[:300]
            desc = item.get("description", "")
            obl = item.get("obligation_type", "")
            conflict_type = item.get("conflict_type", "").replace("_", " ").title()
            sim_pct = sim * 100
            sim_clr = _sim_color(sim)

            st.markdown(
                f"""
                <div class="conflict-card">
                    <div class="conflict-header">
                        <div>
                            <span class="severity-badge {_severity_class(sev)}">{sev}</span>
                            &nbsp;
                            <span style="font-size:0.8rem;color:var(--text-muted);">{conflict_type}</span>
                        </div>
                        <div class="conflict-ref">
                            <strong>{ref_law}</strong> · {ref_country}
                        </div>
                    </div>
                    <div class="conflict-desc">{desc}</div>
                    <div style="display:flex;gap:1rem;margin-top:0.5rem;">
                        <div style="flex:1;">
                            <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;font-weight:600;margin-bottom:0.25rem;">Draft Excerpt</div>
                            <div style="font-size:0.8rem;color:var(--text-secondary);line-height:1.45;">{input_excerpt}</div>
                        </div>
                        <div style="flex:1;">
                            <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;font-weight:600;margin-bottom:0.25rem;">Reference ({ref_country})</div>
                            <div style="font-size:0.8rem;color:var(--text-secondary);line-height:1.45;">{ref_excerpt}</div>
                        </div>
                    </div>
                    <div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.65rem;">
                        <span style="font-size:0.75rem;color:var(--text-muted);">Similarity</span>
                        <div class="sim-bar-bg" style="flex:1;">
                            <div class="sim-bar-fill" style="width:{sim_pct:.0f}%;background:{sim_clr};"></div>
                        </div>
                        <span style="font-size:0.75rem;color:var(--text-secondary);font-weight:600;">{sim:.2f}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="gov-card" style="text-align:center;">
                <div class="gov-card-title" style="justify-content:center;">✅ No Cross-Border Tensions Detected</div>
                <div class="gov-card-body">
                    The draft text does not exhibit high-similarity semantic overlaps with conflicting
                    provisions across EU and India corpora at the current threshold.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # Policy Option Cards
    # -----------------------------------------------------------------------
    st.markdown('<div class="section-header">📜 Policy Alignment Options</div><div class="section-divider"></div>', unsafe_allow_html=True)

    is_compliant = rec.get("full_compliance", False)

    if is_compliant:
        st.markdown(
            """
            <div class="gov-card" style="border-top:3px solid var(--accent-emerald);text-align:center;">
                <div class="gov-card-title" style="justify-content:center;">✅ Full Compliance Indicated</div>
                <div class="gov-card-body">
                    The draft text addresses all required coverage sub-areas and no cross-border
                    tensions were identified against the reference corpus. Consider periodic
                    re-evaluation as regulations evolve.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        gaps = rec.get("gaps_addressed_next", [])
        cols = st.columns(3)
        tier_data = [
            ("minimal", "🟢", "tier-minimal"),
            ("moderate", "🔵", "tier-moderate"),
            ("strict", "🟣", "tier-strict"),
        ]
        for col, (key, icon, tier_class) in zip(cols, tier_data):
            block = rec.get(key, {})
            title = block.get("title", key.title())
            summary = block.get("summary", "")
            sample = block.get("sample_language", "")
            with col:
                sample_html = f'<div class="policy-sample">{sample}</div>' if sample else ""
                st.markdown(
                    f"""
                    <div class="policy-card {tier_class}">
                        <div class="policy-title">{icon} {title}</div>
                        <div class="policy-summary">{summary}</div>
                        {sample_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if gaps:
            st.markdown(
                '<div style="margin-top:0.75rem;font-size:0.8rem;color:var(--text-muted);">'
                '<strong>Priority gaps to address:</strong> '
                + ", ".join(f"<code>{g}</code>" for g in gaps[:8])
                + "</div>",
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------------------------
    # Classified Clauses (expandable)
    # -----------------------------------------------------------------------
    sample_clauses = data.get("classified_clauses_sample", [])
    if sample_clauses:
        st.markdown('<div class="section-header">🏷️ Classified Clauses</div><div class="section-divider"></div>', unsafe_allow_html=True)

        with st.expander(f"View parsed clauses ({len(sample_clauses)} shown)", expanded=False):
            for i, cl in enumerate(sample_clauses[:30]):
                text = cl.get("clause_text", cl.get("text", ""))
                risk = cl.get("risk_type", "—")
                actor = cl.get("actor_type", "—")
                obl = cl.get("obligation_type", "—")
                st.markdown(
                    f"""
                    <div class="gov-card" style="padding:0.85rem 1.1rem;">
                        <div style="margin-bottom:0.4rem;">
                            <span class="pill pill-risk">{risk}</span>
                            <span class="pill pill-actor">{actor}</span>
                            <span class="pill pill-obligation">{obl}</span>
                        </div>
                        <div class="gov-card-body">{text[:500]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -----------------------------------------------------------------------
    # PDF Download
    # -----------------------------------------------------------------------
    st.markdown('<div class="section-divider" style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
    try:
        from app.utils.pdf_report import build_pdf
        pdf_bytes = build_pdf(data)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name="governance_analysis_report.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.caption(f"PDF export unavailable: {e}")

elif analyze_btn:
    st.markdown(
        '<div class="error-card">'
        "<h3>⚠️ No Input Provided</h3>"
        "<p>Please paste draft AI policy text into the input field above.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

else:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">📄</div>
            <p>
                Paste your draft AI policy text above and click <strong>Analyse</strong> to compare it against
                EU and India legal corpora. The system will identify coverage gaps, flag potential
                cross-jurisdictional conflicts, and generate tiered policy alignment options.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
