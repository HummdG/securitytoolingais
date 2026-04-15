"""
Tool Detail — per-tool drill-down
No <style> blocks. All custom HTML uses inline styles.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from data.parser import parse_excel, get_excel_path
from data.models import MATURITY_LABELS, STATUS_ORDER

st.set_page_config(page_title="Tool Detail | AIS", page_icon="🔍", layout="wide")

BG      = "#06090f"; SURFACE = "#0b1220"; CARD = "#0f1a2e"
BORDER  = "#1b2a42"; BORDER2 = "#253a56"
TEXT_HI = "#daeaf7"; TEXT_MD = "#6b8faa"; TEXT_LO = "#334d66"; ACCENT = "#00aaff"

MAT = {0:"#ff4757",1:"#ff8c42",2:"#ffcc02",3:"#2de0a5",4:"#3b9eff",5:"#57f287"}
STATUS = {"Complete":"#2de0a5","In Progress":"#ffcc02","Pending":"#ff4757","TBC":"#b08cff","N/A":"#253a56"}


@st.cache_data(ttl=300, show_spinner="Loading…")
def load_data(): return parse_excel(get_excel_path())


summaries = load_data()
tool_map  = {s.tool: s for s in summaries}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='font-size:.65rem;font-weight:700;letter-spacing:.18em;"
        f"text-transform:uppercase;color:{ACCENT};padding:4px 0 6px;'>Tool Detail</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    selected_tool = st.selectbox("Tool", options=list(tool_map.keys()),
                                  label_visibility="collapsed")
    if st.button("⟳  Refresh", use_container_width=True):
        st.cache_data.clear(); st.rerun()

s = tool_map[selected_tool]
applicable = [t for t in s.tasks if t.applicable == "Y"]
done       = [t for t in applicable if t.status == "Complete"]
remaining  = [t for t in applicable if t.status != "Complete"]
blocked    = [t for t in applicable if t.status in ("Pending", "TBC")]

# ── Tool header ───────────────────────────────────────────────────────────────
mc = MAT[s.current_maturity]
ml = MATURITY_LABELS[s.current_maturity]
st.markdown(
    f"<div style='padding:16px 0 14px;border-bottom:1px solid {BORDER};margin-bottom:18px;'>"
    f"<div style='font-size:.68rem;font-weight:700;letter-spacing:.18em;"
    f"text-transform:uppercase;color:{ACCENT};margin-bottom:4px;'>Security Tool · Maturity Review</div>"
    f"<div style='font-size:2rem;font-weight:700;color:{TEXT_HI};letter-spacing:.04em;"
    f"line-height:1;margin-bottom:8px;'>{s.tool}</div>"
    f"<span style='display:inline-block;padding:4px 14px;border-radius:6px;background:{mc};"
    f"font-size:.82rem;font-weight:700;color:#000;'>Level {s.current_maturity} — {ml}</span>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── KPI mini row ──────────────────────────────────────────────────────────────
kpi_items = [
    ("% Complete",     f"{s.pct_complete:.1f}%", ACCENT),
    ("Tasks Done",     str(len(done)),            STATUS["Complete"]),
    ("Remaining",      str(len(remaining)),       TEXT_MD),
    ("Blocked",        str(len(blocked)),         STATUS["Pending"]),
]
row_html = ""
for lbl, val, col in kpi_items:
    row_html += (
        f"<div style='background:{CARD};border:1px solid {BORDER};"
        f"border-top:2px solid {col};border-radius:8px;padding:14px 16px;'>"
        f"<div style='font-size:.65rem;font-weight:700;letter-spacing:.1em;"
        f"text-transform:uppercase;color:{TEXT_LO};margin-bottom:4px;'>{lbl}</div>"
        f"<div style='font-size:1.9rem;font-weight:700;line-height:1;color:{col};'>{val}</div>"
        f"</div>"
    )
st.markdown(
    f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;'>"
    f"{row_html}</div>",
    unsafe_allow_html=True,
)

# ── Donut + Blockers ──────────────────────────────────────────────────────────
c_donut, c_next = st.columns([4, 5])

with c_donut:
    fig_d = go.Figure(go.Pie(
        labels=["Complete", "Remaining"],
        values=[len(done), max(len(remaining), 0)],
        hole=0.65,
        marker_colors=[STATUS["Complete"], BORDER2],
        textinfo="none", sort=False,
    ))
    fig_d.update_layout(
        annotations=[dict(
            text=f"<b>{s.pct_complete:.0f}%</b>",
            x=0.5, y=0.5,
            font=dict(size=28, color=TEXT_HI),
            showarrow=False,
        )],
        showlegend=True,
        legend=dict(font=dict(color=TEXT_MD, size=11), bgcolor="rgba(0,0,0,0)",
                    orientation="h", y=-0.12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=250, margin=dict(t=10, b=30, l=20, r=20),
    )
    st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

with c_next:
    next_lvl = s.current_maturity + 1
    if next_lvl <= 5:
        blocking_next = [
            t for t in s.tasks
            if t.item.maturity_level == next_lvl
            and t.applicable == "Y"
            and t.status not in ("Complete", "N/A")
        ]
        if blocking_next:
            header_html = (
                f"<div style='font-size:1rem;font-weight:700;color:{TEXT_HI};"
                f"margin-bottom:12px;padding-top:16px;'>"
                f"🚧 {len(blocking_next)} items blocking Level {next_lvl}"
                f"<span style='font-weight:400;font-size:.82rem;color:{TEXT_MD};'>"
                f" — {MATURITY_LABELS[next_lvl]}</span></div>"
            )
            items_html = ""
            for t in blocking_next:
                sc = STATUS.get(t.status, "#94a3b8")
                items_html += (
                    f"<div style='display:flex;align-items:center;gap:10px;"
                    f"padding:8px 12px;background:rgba(255,71,87,.07);"
                    f"border:1px solid rgba(255,71,87,.2);border-radius:6px;"
                    f"margin-bottom:6px;'>"
                    f"<div style='flex:1;font-size:.86rem;color:{TEXT_HI};'>{t.item.item_name}</div>"
                    f"<span style='background:{sc};color:white;font-size:.72rem;font-weight:600;"
                    f"padding:2px 8px;border-radius:999px;white-space:nowrap;'>{t.status}</span>"
                    f"</div>"
                )
            st.markdown(header_html + items_html, unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='padding:24px 16px;background:{CARD};"
                f"border:1px solid {STATUS['Complete']}44;border-radius:10px;"
                f"margin-top:16px;text-align:center;'>"
                f"<div style='font-size:1.4rem;margin-bottom:6px;'>✅</div>"
                f"<div style='font-size:1rem;font-weight:700;color:{STATUS['Complete']};'>"
                f"Level {next_lvl} items complete</div>"
                f"<div style='font-size:.82rem;color:{TEXT_MD};margin-top:4px;'>"
                f"Ready to advance to next level</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f"<div style='padding:24px 16px;background:{CARD};"
            f"border:1px solid {STATUS['Complete']}44;border-radius:10px;"
            f"margin-top:16px;text-align:center;'>"
            f"<div style='font-size:1.4rem;margin-bottom:6px;'>🎉</div>"
            f"<div style='font-size:1rem;font-weight:700;color:{STATUS['Complete']};'>"
            f"Level 5 — Fully Operational</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown(f"<div style='height:10px'></div>", unsafe_allow_html=True)

# ── Level tabs ────────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='font-size:.95rem;font-weight:700;letter-spacing:.07em;"
    f"text-transform:uppercase;color:{TEXT_HI};margin-bottom:4px;'>CHECKLIST DETAIL</div>"
    f"<div style='font-size:.78rem;color:{TEXT_LO};margin-bottom:12px;'>"
    f"All 25 checklist items organised by maturity level</div>",
    unsafe_allow_html=True,
)

tabs = st.tabs([f"L{i} — {MATURITY_LABELS[i]}" for i in range(1, 6)])

for tab, lvl in zip(tabs, range(1, 6)):
    with tab:
        level_tasks = [t for t in s.tasks if t.item.maturity_level == lvl]
        app_tasks   = [t for t in level_tasks if t.applicable == "Y"]
        done_tasks  = [t for t in app_tasks if t.status == "Complete"]
        pct_lvl     = round(len(done_tasks) / len(app_tasks) * 100) if app_tasks else 0

        if app_tasks and len(done_tasks) == len(app_tasks):
            st.success(f"✅  Level {lvl} fully complete — {len(done_tasks)}/{len(app_tasks)} done")
        elif lvl <= s.current_maturity:
            st.info(f"Level {lvl} reached · {len(done_tasks)}/{len(app_tasks)} applicable complete")
        else:
            st.warning(f"Level {lvl} in progress — {len(done_tasks)}/{len(app_tasks)} done ({pct_lvl}%)")

        rows = []
        for t in level_tasks:
            sc = STATUS.get(t.status, "#94a3b8")
            pill = (
                f'<span style="background:{sc};color:white;font-size:.72rem;font-weight:600;'
                f'padding:2px 9px;border-radius:999px;">'
                f'{t.status}</span>'
            )
            rows.append({
                "Checklist Item": t.item.item_name,
                "Applicable": t.applicable,
                "Status": pill,
                "Comment": t.comment or "",
            })

        df = pd.DataFrame(rows)
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

        comments = [(t.item.item_name, t.comment) for t in level_tasks if t.comment]
        if comments:
            with st.expander("💬 Notes"):
                for nm, cm in comments:
                    st.markdown(f"**{nm}:** {cm}")
