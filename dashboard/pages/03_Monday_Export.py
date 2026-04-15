"""
Monday.com Export — no <style> blocks, all inline styles.
"""

import sys, os, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd

from data.parser import parse_excel, get_excel_path
from data.models import MATURITY_LABELS, STATUS_ORDER

st.set_page_config(page_title="Monday Export | AIS", page_icon="📤", layout="wide")

CARD = "#0f1a2e"; BORDER = "#1b2a42"; BORDER2 = "#253a56"
TEXT_HI = "#daeaf7"; TEXT_MD = "#6b8faa"; TEXT_LO = "#334d66"; ACCENT = "#00aaff"

STATUS_MAP = {
    "Complete":"Done","In Progress":"Working on it",
    "Pending":"Stuck","TBC":"Need more info","N/A":"Not relevant",
}
STATUS_MONDAY_COLORS = {
    "Done":"#2de0a5","Working on it":"#ffcc02",
    "Stuck":"#ff4757","Need more info":"#b08cff","Not relevant":"#253a56",
}


@st.cache_data(ttl=300, show_spinner="Loading…")
def load_data(): return parse_excel(get_excel_path())


summaries = load_data()

with st.sidebar:
    st.markdown(
        f"<div style='font-size:.65rem;font-weight:700;letter-spacing:.18em;"
        f"text-transform:uppercase;color:{ACCENT};padding:4px 0 2px;'>Export</div>"
        f"<div style='font-size:1.3rem;font-weight:700;color:{TEXT_HI};margin-bottom:12px;'>"
        f"Monday.com</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button("⟳  Refresh", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='padding:16px 0 14px;border-bottom:1px solid {BORDER};margin-bottom:22px;'>"
    f"<div style='font-size:.68rem;font-weight:700;letter-spacing:.2em;"
    f"text-transform:uppercase;color:{ACCENT};margin-bottom:4px;'>"
    f"Security Tooling AIS · Migration</div>"
    f"<div style='font-size:2rem;font-weight:700;color:{TEXT_HI};letter-spacing:.05em;'>"
    f"MONDAY.COM EXPORT</div>"
    f"<div style='font-size:.8rem;color:{TEXT_LO};margin-top:6px;'>"
    f"Download a ready-to-import CSV and follow the setup guide below</div>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Build export data ──────────────────────────────────────────────────────────
export_rows = []
for s in summaries:
    for t in s.tasks:
        export_rows.append({
            "Name":           f"{t.tool} — {t.item.item_name}",
            "Group":          f"Maturity Level {t.item.maturity_level} — {MATURITY_LABELS[t.item.maturity_level]}",
            "Tool":           t.tool,
            "Maturity Level": t.item.maturity_level,
            "Checklist Item": t.item.item_name,
            "Status":         STATUS_MAP.get(t.status, t.status),
            "Applicable":     t.applicable,
            "Notes":          t.comment or "",
        })
df_export = pd.DataFrame(export_rows)

# ── Two columns ───────────────────────────────────────────────────────────────
col_l, col_r = st.columns([3, 2])

with col_l:
    st.markdown(
        f"<div style='font-size:.95rem;font-weight:700;letter-spacing:.07em;"
        f"text-transform:uppercase;color:{TEXT_HI};margin-bottom:3px;'>DATA PREVIEW</div>"
        f"<div style='font-size:.78rem;color:{TEXT_LO};margin-bottom:10px;'>"
        f"{len(df_export)} rows · ready for Monday.com CSV import</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(df_export.head(30), use_container_width=True, height=340, hide_index=True)
    if len(df_export) > 30:
        st.caption(f"Showing 30 of {len(df_export)} rows — download to see all")

with col_r:
    st.markdown(
        f"<div style='font-size:.95rem;font-weight:700;letter-spacing:.07em;"
        f"text-transform:uppercase;color:{TEXT_HI};margin-bottom:3px;'>DOWNLOAD</div>"
        f"<div style='font-size:.78rem;color:{TEXT_LO};margin-bottom:10px;'>"
        f"Monday.com import-ready CSV</div>",
        unsafe_allow_html=True,
    )
    csv_buf = io.StringIO()
    df_export.to_csv(csv_buf, index=False)
    st.download_button(
        label="⬇  Download  ais_monday_import.csv",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="ais_monday_import.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown(
        f"<div style='font-size:.85rem;font-weight:700;letter-spacing:.07em;"
        f"text-transform:uppercase;color:{TEXT_HI};margin:18px 0 8px;'>"
        f"Status Mapping</div>",
        unsafe_allow_html=True,
    )
    for orig, mapped in STATUS_MAP.items():
        mc = STATUS_MONDAY_COLORS.get(mapped, "#555")
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;padding:6px 0;"
            f"border-bottom:1px solid {BORDER};font-size:.8rem;'>"
            f"<span style='color:{TEXT_MD};flex:1;'>{orig}</span>"
            f"<span style='font-size:.65rem;color:{TEXT_LO};'>→</span>"
            f"<span style='background:{mc}22;border:1px solid {mc}55;color:{mc};"
            f"padding:2px 8px;border-radius:999px;font-size:.72rem;font-weight:600;'>{mapped}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Setup guide ───────────────────────────────────────────────────────────────
st.markdown(f"<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown(
    f"<div style='font-size:.95rem;font-weight:700;letter-spacing:.07em;"
    f"text-transform:uppercase;color:{TEXT_HI};margin-bottom:3px;'>MONDAY.COM SETUP GUIDE</div>"
    f"<div style='font-size:.78rem;color:{TEXT_LO};margin-bottom:14px;'>"
    f"10 steps to replicate this dashboard in Monday.com</div>",
    unsafe_allow_html=True,
)

STEPS = [
    ("Step 01", "Create a new Board",
     'Click <b>+ Add</b> → <b>Board</b>. Name it <code style="background:rgba(255,255,255,.08);padding:1px 5px;border-radius:3px;">Security Tooling AIS — Maturity Tracker</code>. Choose <b>Main Table</b> view.'),
    ("Step 02", "Create 5 Groups (one per Maturity Level)",
     "Click <b>+ Add Group</b> five times, named Level 1 — Service Implemented through Level 5 — Fully Operational."),
    ("Step 03", "Add column types",
     "Add: <b>Status</b> (status), <b>Tool</b> (text), <b>Maturity Level</b> (number), <b>Applicable</b> (text), <b>Notes</b> (long text), <b>Owner</b> (people), <b>Due Date</b> (date)."),
    ("Step 04", "Import the CSV",
     "Board menu (⋯) → Import / Export → Import from CSV. Upload the file above and map columns in the wizard."),
    ("Step 05", "Match Status label colours",
     "Done=green, Working on it=orange, Stuck=red, Need more info=purple, Not relevant=grey."),
    ("Step 06", "Assign Owners",
     "Use the Owner (People) column. Filter the board by Person=Me to see your own outstanding items."),
    ("Step 07", "Automation — completion notify",
     '"When Status changes to Done, notify Owner." Keeps people updated without manual chasing.'),
    ("Step 08", "Automation — due date reminder",
     '"When Due Date arrives and Status is not Done, notify Owner and me." Your automated chase trigger.'),
    ("Step 09", "Create a Dashboard",
     "Add a Battery widget (% done per group), Chart widget (status breakdown), and a Table widget filtered to Status=Stuck for daily chase view."),
    ("Step 10", "Add a Gantt view",
     "Add View → Gantt. Set date column to Due Date, group by Tool. Pin the board to sidebar for daily access."),
]

for num, title, body in STEPS:
    st.markdown(
        f"<div style='border-left:3px solid {ACCENT};padding:11px 16px;"
        f"background:rgba(0,170,255,.04);border-radius:0 8px 8px 0;margin-bottom:10px;'>"
        f"<div style='font-size:.65rem;font-weight:700;letter-spacing:.12em;"
        f"text-transform:uppercase;color:{ACCENT};margin-bottom:3px;'>{num}</div>"
        f"<div style='font-size:.95rem;font-weight:700;color:{TEXT_HI};"
        f"margin-bottom:4px;letter-spacing:.02em;'>{title}</div>"
        f"<div style='font-size:.83rem;color:{TEXT_MD};line-height:1.6;'>{body}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
