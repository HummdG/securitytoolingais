"""
Security Tooling AIS Dashboard — Overview
Run: streamlit run 00_Overview.py
Theme: .streamlit/config.toml handles all Streamlit component colours.
All custom HTML uses inline styles — no <style> blocks (stripped by Streamlit 1.36+).
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from data.parser import parse_excel, get_excel_path
from data.models import MATURITY_LABELS, STATUS_ORDER

# ── Design tokens (used in inline styles & Plotly) ──────────────────────────
BG      = "#06090f"
SURFACE = "#0b1220"
CARD    = "#0f1a2e"
BORDER  = "#1b2a42"
BORDER2 = "#253a56"
TEXT_HI = "#daeaf7"
TEXT_MD = "#6b8faa"
TEXT_LO = "#334d66"
ACCENT  = "#00aaff"

# Vivid maturity colours for dark backgrounds
MAT = {
    0: "#ff4757",   # red      – not started
    1: "#ff8c42",   # orange   – L1
    2: "#ffcc02",   # amber    – L2
    3: "#2de0a5",   # emerald  – L3
    4: "#3b9eff",   # blue     – L4
    5: "#57f287",   # mint     – L5
}
STATUS = {
    "Complete":    "#2de0a5",
    "In Progress": "#ffcc02",
    "Pending":     "#ff4757",
    "TBC":         "#b08cff",
    "N/A":         "#253a56",
}

# ── Plotly chart defaults (dark transparent theme) ──────────────────────────
def chart(**kw) -> dict:
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,14,28,0.75)",
        font=dict(color=TEXT_MD, family="'Trebuchet MS', sans-serif", size=12),
        hoverlabel=dict(bgcolor=BORDER, bordercolor=ACCENT,
                        font_color=TEXT_HI, font_size=13),
        legend=dict(font=dict(color=TEXT_MD, size=11), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=10, b=36, l=0, r=10),
    )
    base.update(kw)
    return base

AX = dict(
    gridcolor="rgba(255,255,255,0.04)",
    linecolor="rgba(255,255,255,0.07)",
    tickcolor="rgba(0,0,0,0)",
    tickfont=dict(color=TEXT_MD, size=11),
    zeroline=False, showgrid=True,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Security Tooling AIS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Loading workbook…")
def load_data():
    return parse_excel(get_excel_path())


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='padding:4px 0 6px;font-size:.65rem;font-weight:700;"
        f"letter-spacing:.18em;text-transform:uppercase;color:{ACCENT};'>"
        f"UK SOC</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:1.35rem;font-weight:700;color:{TEXT_HI};"
        f"line-height:1.2;margin-bottom:12px;'>Security Tooling<br>AIS Tracker</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    if st.button("⟳  Refresh from Excel", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        f"<div style='font-size:.68rem;font-weight:700;letter-spacing:.12em;"
        f"text-transform:uppercase;color:{TEXT_LO};margin:16px 0 6px;'>"
        f"Filter by Maturity</div>",
        unsafe_allow_html=True,
    )
    selected_levels = st.multiselect(
        "Levels",
        options=list(MATURITY_LABELS.keys()),
        default=list(MATURITY_LABELS.keys()),
        format_func=lambda k: f"L{k} — {MATURITY_LABELS[k]}",
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown(
        f"<div style='font-size:.73rem;color:{TEXT_LO};line-height:1.7;'>"
        f"14 tools in scope · 5 maturity levels<br>"
        f"All tools → Level 5 target<br><br>"
        f"<span style='color:{TEXT_LO};'>Source: AIS Checklist .xlsm</span></div>",
        unsafe_allow_html=True,
    )


# ── Load & filter ─────────────────────────────────────────────────────────────
summaries_all = load_data()
summaries = (
    [s for s in summaries_all if s.current_maturity in selected_levels]
    if selected_levels else summaries_all
)


# ── Page header ───────────────────────────────────────────────────────────────
today = date.today().strftime("%d %b %Y")
st.markdown(
    f"<div style='padding:16px 0 14px;border-bottom:1px solid {BORDER};margin-bottom:20px;'>"
    f"<div style='font-size:.68rem;font-weight:700;letter-spacing:.2em;"
    f"text-transform:uppercase;color:{ACCENT};margin-bottom:6px;'>"
    f"UK SOC · Acceptance Into Support · {today}</div>"
    f"<div style='font-size:2rem;font-weight:700;color:{TEXT_HI};"
    f"letter-spacing:.05em;line-height:1;'>"
    f"SECURITY TOOLING <span style='color:{ACCENT};'>MATURITY</span></div>"
    f"<div style='font-size:.8rem;color:{TEXT_LO};margin-top:6px;'>"
    f"Tracking {len(summaries_all)} tools through 5 implementation phases"
    f" · All tools targeting Level 5 — Fully Operational</div>"
    f"</div>",
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def filtered_pct(s, lf: list) -> float:
    """% complete for a tool considering only tasks at levels in lf."""
    app  = [t for t in s.tasks if t.applicable == "Y" and t.item.maturity_level in lf]
    done = [t for t in app if t.status == "Complete"]
    return round(len(done) / len(app) * 100, 1) if app else 0.0


def weighted_pct(s, lf: list) -> float:
    """Weighted % complete — sums item weights instead of counting tasks equally."""
    tasks = [t for t in s.tasks if t.applicable == "Y" and t.item.maturity_level in lf]
    total_w = sum(t.item.weight for t in tasks)
    done_w  = sum(t.item.weight for t in tasks if t.status == "Complete")
    return round(done_w / total_w * 100, 1) if total_w else 0.0


def render_view(all_s: list, view_s: list, lf: list) -> None:
    """Render KPI cards + all three charts for the given level filter."""

    # ── KPI computation ───────────────────────────────────────────────────────
    not_started = sum(1 for s in all_s if s.current_maturity == 0)
    in_prog     = sum(1 for s in all_s if 0 < s.current_maturity < 5)
    lvl5        = sum(1 for s in all_s if s.current_maturity == 5)
    avg_pct     = round(sum(filtered_pct(s, lf) for s in all_s) / len(all_s), 1) if all_s else 0.0
    pending_ct  = sum(
        1 for s in all_s for t in s.tasks
        if t.applicable == "Y" and t.item.maturity_level in lf
        and t.status in ("Pending", "TBC")
    )
    lvl_label = f"L{min(lf)}–L{max(lf)}"

    # ── KPI cards ─────────────────────────────────────────────────────────────
    kpis = [
        ("Not Started",    str(not_started),  MAT[0],            "Maturity Level 0"),
        ("In Progress",    str(in_prog),       MAT[1],            "Levels 1 – 4"),
        ("Level 5 ✓",      str(lvl5),          MAT[5],            "Fully operational"),
        ("Avg Completion", f"{avg_pct}%",      ACCENT,            f"Across all tools · {lvl_label}"),
        ("Blocked Tasks",  str(pending_ct),    STATUS["Pending"], f"Pending or TBC · {lvl_label}"),
    ]

    card_divs = ""
    for label, value, color, sub in kpis:
        card_divs += (
            f"<div style='background:{CARD};border:1px solid {BORDER};"
            f"border-top:3px solid {color};border-radius:10px;"
            f"padding:18px 20px;overflow:hidden;'>"
            f"<div style='font-size:.67rem;font-weight:700;letter-spacing:.12em;"
            f"text-transform:uppercase;color:{TEXT_LO};margin-bottom:5px;'>{label}</div>"
            f"<div style='font-size:2.4rem;font-weight:700;line-height:1;color:{color};'>{value}</div>"
            f"<div style='font-size:.76rem;color:{TEXT_LO};margin-top:4px;'>{sub}</div>"
            f"</div>"
        )

    st.markdown(
        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:14px;"
        f"margin-top:4px;margin-bottom:22px;'>{card_divs}</div>",
        unsafe_allow_html=True,
    )

    # ── Chart 1 — Maturity Progress Bar ───────────────────────────────────────
    toggle_key = f"wt_{'_'.join(str(l) for l in lf)}"
    hdr_col, tog_col = st.columns([7, 3])
    with hdr_col:
        st.markdown(
            f"<div style='font-size:1rem;font-weight:700;letter-spacing:.07em;"
            f"text-transform:uppercase;color:{TEXT_HI};margin-bottom:2px;'>MATURITY PROGRESS</div>"
            f"<div style='font-size:.78rem;color:{TEXT_LO};margin-bottom:8px;'>"
            f"Coloured by current maturity level · toggle to apply item weightings</div>",
            unsafe_allow_html=True,
        )
    with tog_col:
        st.markdown(
            f"<div style='font-size:.68rem;font-weight:700;letter-spacing:.1em;"
            f"text-transform:uppercase;color:{TEXT_LO};margin-bottom:4px;margin-top:4px;'>"
            f"View</div>",
            unsafe_allow_html=True,
        )
        use_weights = st.toggle("Weighted completion", key=toggle_key, value=False)

    pct_func  = weighted_pct if use_weights else filtered_pct
    axis_label = "Weighted % Complete" if use_weights else "% Complete"

    sorted_s = sorted(view_s, key=lambda x: pct_func(x, lf))
    fig_prog = go.Figure()
    for lvl in sorted(set(s.current_maturity for s in sorted_s)):
        subset = [s for s in sorted_s if s.current_maturity == lvl]
        pcts   = [pct_func(s, lf) for s in subset]
        fig_prog.add_trace(go.Bar(
            y=[s.tool for s in subset],
            x=pcts,
            orientation="h",
            name=f"L{lvl} — {MATURITY_LABELS[lvl]}",
            marker=dict(color=MAT[lvl], opacity=0.9),
            text=[f"  L{s.current_maturity} · {p:.1f}%" for s, p in zip(subset, pcts)],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#ffffff", size=12),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<br>Level " + str(lvl) + "<extra></extra>",
        ))

    fig_prog.add_vline(x=100, line_dash="dot",
                       line_color="rgba(45,224,165,0.25)", line_width=1.5)
    fig_prog.update_layout(
        **chart(
            height=max(400, len(sorted_s) * 36),
            margin=dict(t=10, b=40, l=210, r=20),
            barmode="overlay",
            xaxis={**AX,
                "title": dict(text=axis_label, font=dict(color=TEXT_MD, size=11)),
                "range": [0, 110], "ticksuffix": "%",
                "tickvals": [0, 25, 50, 75, 100],
            },
            yaxis={**AX,
                "gridcolor": "rgba(0,0,0,0)",
                "tickfont": dict(color=TEXT_HI, size=12),
                "automargin": True,
            },
            legend=dict(orientation="h", y=-0.1, x=0,
                        font=dict(color=TEXT_MD, size=11), bgcolor="rgba(0,0,0,0)"),
        ),
    )
    st.plotly_chart(fig_prog, use_container_width=True, config={"displayModeBar": False})

    st.markdown(f"<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Charts 2 & 3 — side by side ───────────────────────────────────────────
    col_l, col_r = st.columns([5, 4])

    with col_l:
        st.markdown(
            f"<div style='font-size:1rem;font-weight:700;letter-spacing:.07em;"
            f"text-transform:uppercase;color:{TEXT_HI};margin-bottom:2px;'>COMPLETION HEATMAP</div>"
            f"<div style='font-size:.78rem;color:{TEXT_LO};margin-bottom:8px;'>"
            f"Fraction of applicable tasks done per tool × maturity level</div>",
            unsafe_allow_html=True,
        )

        tools_ord = [s.tool for s in sorted(view_s, key=lambda x: -filtered_pct(x, lf))]
        z_mat, ann_mat = [], []
        for tool in tools_ord:
            s = next(x for x in view_s if x.tool == tool)
            row_z, row_a = [], []
            for lvl in lf:
                app  = [t for t in s.tasks if t.item.maturity_level == lvl and t.applicable == "Y"]
                done = [t for t in app if t.status == "Complete"]
                tot  = len(app)
                row_z.append(len(done) / tot if tot else 0.0)
                row_a.append(f"{len(done)}/{tot}" if tot else "–")
            z_mat.append(row_z)
            ann_mat.append(row_a)

        fig_heat = go.Figure(go.Heatmap(
            z=z_mat,
            x=[f"L{i} · {MATURITY_LABELS[i][:13]}" for i in lf],
            y=tools_ord,
            colorscale=[
                [0.00, "#2d0a0a"], [0.20, "#7c1f1f"],
                [0.45, "#7c4e00"], [0.70, "#0e4a25"], [1.00, "#2de0a5"],
            ],
            zmin=0, zmax=1,
            text=ann_mat,
            texttemplate="%{text}",
            textfont=dict(color="rgba(255,255,255,0.9)", size=12),
            showscale=True,
            colorbar=dict(
                title=dict(text="Done", font=dict(color=TEXT_MD, size=11)),
                tickformat=".0%",
                tickfont=dict(color=TEXT_MD, size=10),
                thickness=12, len=0.9,
                bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, borderwidth=1,
            ),
            xgap=2, ygap=2,
            hovertemplate="<b>%{y}</b><br>%{x}<br>%{text} complete<extra></extra>",
        ))
        fig_heat.update_layout(
            **chart(
                height=420,
                margin=dict(t=10, b=30, l=175, r=60),
                xaxis={**AX, "side": "bottom", "tickangle": -20,
                       "tickfont": dict(color=TEXT_MD, size=10),
                       "gridcolor": "rgba(0,0,0,0)"},
                yaxis={**AX, "autorange": "reversed",
                       "tickfont": dict(color=TEXT_HI, size=11),
                       "automargin": True, "gridcolor": "rgba(0,0,0,0)"},
            ),
        )
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.markdown(
            f"<div style='font-size:1rem;font-weight:700;letter-spacing:.07em;"
            f"text-transform:uppercase;color:{TEXT_HI};margin-bottom:2px;'>STATUS BREAKDOWN</div>"
            f"<div style='font-size:.78rem;color:{TEXT_LO};margin-bottom:8px;'>"
            f"Applicable tasks per tool, segmented by current status</div>",
            unsafe_allow_html=True,
        )

        tools_for_status = [s.tool for s in sorted(view_s, key=lambda x: -filtered_pct(x, lf))]
        fig_st = go.Figure()
        for status in STATUS_ORDER:
            counts = [
                sum(1 for t in next(x for x in view_s if x.tool == tl).tasks
                    if t.applicable == "Y" and t.status == status
                    and t.item.maturity_level in lf)
                for tl in tools_for_status
            ]
            if sum(counts) == 0:
                continue
            fig_st.add_trace(go.Bar(
                y=tools_for_status, x=counts, name=status, orientation="h",
                marker=dict(color=STATUS[status], opacity=0.9),
                hovertemplate="<b>%{y}</b><br>" + status + ": %{x}<extra></extra>",
            ))

        fig_st.update_layout(
            **chart(
                height=420,
                margin=dict(t=10, b=70, l=175, r=10),
                barmode="stack",
                xaxis={**AX,
                       "title": dict(text="Task count",
                                     font=dict(color=TEXT_MD, size=11),
                                     standoff=12),
                       "side": "bottom"},
                yaxis={**AX,
                       "tickfont": dict(color=TEXT_HI, size=11),
                       "automargin": True,
                       "gridcolor": "rgba(0,0,0,0)",
                       "autorange": "reversed"},
                legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center",
                            font=dict(color=TEXT_MD, size=11), bgcolor="rgba(0,0,0,0)"),
            ),
        )
        st.plotly_chart(fig_st, use_container_width=True, config={"displayModeBar": False})


# ── View tabs ─────────────────────────────────────────────────────────────────
tab_combined, tab_build, tab_ops = st.tabs([
    "🔀  Combined",
    "🔨  Build  ·  L1 – L3",
    "⚙️  Operational  ·  L4 – L5",
])

with tab_combined:
    render_view(summaries_all, summaries, list(range(1, 6)))

with tab_build:
    render_view(summaries_all, summaries, [1, 2, 3])

with tab_ops:
    render_view(summaries_all, summaries, [4, 5])


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f"<div style='font-size:.72rem;color:{TEXT_LO};text-align:right;'>"
    f"Live from Acceptance Into Support Checklist .xlsm · auto-refresh every 5 min · {today}"
    f"</div>",
    unsafe_allow_html=True,
)
