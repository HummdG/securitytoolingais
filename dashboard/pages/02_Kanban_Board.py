"""
Kanban Board — no <style> blocks, all inline styles.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from data.parser import parse_excel, get_excel_path
from data.models import MATURITY_LABELS, STATUS_ORDER

st.set_page_config(page_title="Kanban Board | AIS", page_icon="📋", layout="wide")

BG = "#06090f"; SURFACE = "#0b1220"; CARD = "#0f1a2e"
BORDER = "#1b2a42"; BORDER2 = "#253a56"
TEXT_HI = "#daeaf7"; TEXT_MD = "#6b8faa"; TEXT_LO = "#334d66"; ACCENT = "#00aaff"
MAT = {0:"#ff4757",1:"#ff8c42",2:"#ffcc02",3:"#2de0a5",4:"#3b9eff",5:"#57f287"}
STATUS = {"Complete":"#2de0a5","In Progress":"#ffcc02","Pending":"#ff4757","TBC":"#b08cff","N/A":"#253a56"}


@st.cache_data(ttl=300, show_spinner="Loading…")
def load_data(): return parse_excel(get_excel_path())


summaries = load_data()
all_tools = [s.tool for s in summaries]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='font-size:.65rem;font-weight:700;letter-spacing:.18em;"
        f"text-transform:uppercase;color:{ACCENT};padding:4px 0 2px;'>Kanban</div>"
        f"<div style='font-size:1.3rem;font-weight:700;color:{TEXT_HI};margin-bottom:12px;'>"
        f"Task Board</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    sel_tools  = st.multiselect("Tools",  all_tools, default=all_tools, label_visibility="collapsed")
    sel_levels = st.multiselect("Levels", list(range(1, 6)), default=list(range(1, 6)),
                                format_func=lambda x: f"L{x} – {MATURITY_LABELS[x]}",
                                label_visibility="collapsed")
    hide_na  = st.toggle("Hide N/A items", value=True)
    group_by = st.radio("Group by", ["Tool", "Maturity Level"], horizontal=True)
    st.divider()
    if st.button("⟳  Refresh", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='padding:16px 0 14px;border-bottom:1px solid {BORDER};margin-bottom:16px;'>"
    f"<div style='font-size:.68rem;font-weight:700;letter-spacing:.2em;"
    f"text-transform:uppercase;color:{ACCENT};margin-bottom:4px;'>"
    f"Security Tooling AIS · Task Board</div>"
    f"<div style='font-size:2rem;font-weight:700;color:{TEXT_HI};letter-spacing:.05em;'>KANBAN VIEW</div>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Build flat task list ───────────────────────────────────────────────────────
flat = []
for s in summaries:
    if s.tool not in sel_tools: continue
    for t in s.tasks:
        if t.item.maturity_level not in sel_levels: continue
        if hide_na and t.status == "N/A": continue
        flat.append({"tool": s.tool, "item": t.item.item_name,
                     "level": t.item.maturity_level, "status": t.status,
                     "applicable": t.applicable})

# Summary bar
counts = {st_: sum(1 for r in flat if r["status"] == st_) for st_ in STATUS_ORDER}
sum_parts = ""
for st_, cnt in counts.items():
    if cnt == 0: continue
    sc = STATUS[st_]
    sum_parts += (
        f"<span style='display:inline-flex;align-items:center;gap:6px;"
        f"margin-right:18px;font-size:.82rem;color:{TEXT_MD};'>"
        f"<span style='width:10px;height:10px;border-radius:50%;background:{sc};"
        f"box-shadow:0 0 6px {sc}66;flex-shrink:0;'></span>"
        f"<strong style='color:{TEXT_HI};font-size:1rem;'>{cnt}</strong> {st_}</span>"
    )
st.markdown(
    f"<div style='display:flex;flex-wrap:wrap;padding:10px 0;border-bottom:1px solid {BORDER};"
    f"margin-bottom:16px;'>{sum_parts}</div>",
    unsafe_allow_html=True,
)

if not flat:
    st.markdown(
        f"<div style='text-align:center;padding:60px;color:{TEXT_LO};font-size:.9rem;'>"
        f"No tasks match the current filters.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── Kanban columns ────────────────────────────────────────────────────────────
kanban_cols = st.columns(len(STATUS_ORDER))

for col, status in zip(kanban_cols, STATUS_ORDER):
    sc = STATUS[status]
    tasks_here = [r for r in flat if r["status"] == status]
    with col:
        # Column header
        st.markdown(
            f"<div style='text-align:center;padding:10px 8px;"
            f"background:linear-gradient(135deg,{sc}22,{sc}11);"
            f"border:1px solid {sc}44;border-bottom:2px solid {sc};"
            f"border-radius:8px 8px 0 0;font-weight:700;font-size:.9rem;"
            f"letter-spacing:.05em;text-transform:uppercase;color:{TEXT_HI};"
            f"margin-bottom:10px;'>"
            f"{status}"
            f"<br><span style='font-size:.72rem;font-weight:500;opacity:.65;'>"
            f"{len(tasks_here)} task{'s' if len(tasks_here) != 1 else ''}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if not tasks_here:
            st.markdown(
                f"<div style='text-align:center;padding:20px 0;color:{TEXT_LO};"
                f"font-size:.8rem;'>—</div>",
                unsafe_allow_html=True,
            )
            continue

        # Group tasks within column
        groups: dict[str, list] = {}
        for r in tasks_here:
            key = r["tool"] if group_by == "Tool" else f"L{r['level']} · {MATURITY_LABELS[r['level']]}"
            groups.setdefault(key, []).append(r)

        for grp_tasks in groups.values():
            for r in grp_tasks:
                mc = MAT[r["level"]]
                st.markdown(
                    f"<div style='border-left:3px solid {mc};border-radius:0 7px 7px 0;"
                    f"padding:10px 11px;margin-bottom:7px;background:{CARD};"
                    f"border-top:1px solid {BORDER};border-right:1px solid {BORDER};"
                    f"border-bottom:1px solid {BORDER};'>"
                    f"<div style='font-weight:700;font-size:.88rem;color:{TEXT_HI};"
                    f"margin-bottom:3px;'>{r['tool']}</div>"
                    f"<div style='font-size:.78rem;color:{TEXT_MD};margin-bottom:7px;"
                    f"line-height:1.3;'>{r['item']}</div>"
                    f"<div style='display:flex;gap:5px;'>"
                    f"<span style='background:{mc};color:#000;font-size:.68rem;font-weight:700;"
                    f"padding:1px 7px;border-radius:999px;'>L{r['level']}</span>"
                    f"<span style='background:{BORDER2};color:{TEXT_MD};font-size:.68rem;"
                    f"font-weight:600;padding:1px 7px;border-radius:999px;'>"
                    f"App:{r['applicable']}</span>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
