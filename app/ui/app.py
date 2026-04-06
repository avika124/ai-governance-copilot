"""
Global AI Governance Copilot — Streamlit UI.

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

# --- Page config & professional styling ---
st.set_page_config(
    page_title="AI Governance Copilot",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --gov-navy: #0f172a;
        --gov-accent: #2563eb;
        --gov-muted: #64748b;
    }
    .main-header {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-weight: 700;
        font-size: 1.75rem;
        color: var(--gov-navy);
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        color: var(--gov-muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">Global AI Governance Copilot</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Draft policy analysis · EU & India corpus · Coverage & conflict signals</p>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Settings")
    api_base = st.text_input("API base URL", value=DEFAULT_API)
    st.caption("Start the API: `uvicorn app.api.main:app --reload`")
    st.divider()
    st.markdown("**Resources**")
    st.markdown("- [EUR-Lex](https://eur-lex.europa.eu)")
    st.markdown("- [India Code](https://www.indiacode.nic.in)")

draft = st.text_area(
    "Paste draft AI policy text",
    height=220,
    placeholder="Enter clauses describing obligations, incident reporting, data handling, testing, etc.",
)

col_a, col_b = st.columns([1, 4])
with col_a:
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

if analyze_btn and draft.strip():
    with st.spinner("Running analysis pipeline (embeddings + FAISS may take a moment on first run)…"):
        try:
            r = requests.post(
                f"{api_base.rstrip('/')}/analyze",
                json={"text": draft},
                timeout=300,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    st.success("Analysis complete")

    # Coverage heatmap-style grid
    st.subheader("Coverage matrix")
    cov = data.get("coverage", {})
    grid = cov.get("grid", {})
    rows = []
    for risk, areas in grid.items():
        for area, info in areas.items():
            rows.append({
                "Risk": risk,
                "Area": area,
                "Covered": "✓" if info.get("covered") else "✗",
                "Evidence": info.get("evidence", "—"),
            })
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    summ = cov.get("summary", {})
    st.metric("Coverage score", f"{summ.get('fraction', 0)*100:.0f}%", f"{summ.get('covered')}/{summ.get('total')} sub-areas")

    st.subheader("Conflict signals")
    conf = data.get("conflicts", {})
    items = conf.get("items", [])
    if items:
        import pandas as pd
        cdf = pd.DataFrame([
            {
                "Severity": x.get("severity"),
                "Reference": x.get("reference_law", ""),
                "Country": x.get("reference_country", ""),
                "Similarity": x.get("similarity"),
                "Description": x.get("description", "")[:200],
            }
            for x in items
        ])
        st.dataframe(cdf, use_container_width=True, hide_index=True)
    else:
        st.info("No high-similarity cross-border tensions flagged for this draft.")

    st.subheader("Policy options")
    rec = data.get("recommendations", {})
    c1, c2, c3 = st.columns(3)
    for col, key, color in zip(
        (c1, c2, c3),
        ("minimal", "moderate", "strict"),
        ("#f1f5f9", "#dbeafe", "#e0e7ff"),
    ):
        block = rec.get(key, {})
        with col:
            st.markdown(
                f'<div style="background:{color};padding:1rem;border-radius:8px;border:1px solid #e2e8f0;height:100%;">'
                f'<strong>{block.get("title", key)}</strong><br/><br/>{block.get("summary", "")}<br/><br/>'
                f'<small>{block.get("sample_language", "")}</small></div>',
                unsafe_allow_html=True,
            )

    # PDF download
    try:
        from app.utils.pdf_report import build_pdf
        pdf_bytes = build_pdf(data)
        st.download_button(
            label="Download PDF report",
            data=pdf_bytes,
            file_name="governance_analysis_report.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.caption(f"PDF export unavailable: {e}")

    with st.expander("Sample classified clauses (first 20)"):
        st.json(data.get("classified_clauses_sample", [])[:20])

elif analyze_btn:
    st.warning("Please enter draft text.")

else:
    st.caption("Enter policy text and click **Analyze** to compare against the legal corpus.")
