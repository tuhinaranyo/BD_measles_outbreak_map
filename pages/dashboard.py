from __future__ import annotations

from datetime import date
from html import escape
import json
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from measles_dashboard.config import DB_PATH, ROOT
from measles_dashboard.db import init_db
from measles_dashboard.theme import (
    CHART_DIVISION_COLORS,
    COLORS,
    EMBED_HEIGHT,
    FONT_STACK,
    NATIONAL_LINE,
    RISK,
    iframe_shell_css,
    plotly_base_layout,
    style_axes,
)
from measles_dashboard.ui import inject_style, section_title


st.set_page_config(page_title="বাংলাদেশ হাম সতর্কতা", layout="wide", initial_sidebar_state="collapsed")
inject_style()


RISK_STYLE = RISK

MAP_PATH = ROOT / "assets" / "bd_divisions_svg.json"
STATUS_BN = {
    "High alert": "বেশি সতর্কতা",
    "Watch closely": "খেয়াল রাখুন",
    "Lower signal": "কম সংকেত",
}
TREND_LINE_BD = "সারা বাংলাদেশ"


def bn_num(value: object) -> str:
    return f"{value:,}".translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))


def bn_date(value: object) -> str:
    return str(value).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))


def bn_table_value(value: object) -> str:
    if pd.isna(value):
        return ""
    number = float(value)
    if number.is_integer():
        return bn_num(int(number))
    return bn_num(round(number, 1))


def apply_mobile_friendly_layout(fig, *, height: int = 380, chart_kind: str = "line") -> None:
    """Plotly layout aligned with the Apple-style dark dashboard."""
    layout = plotly_base_layout(height=max(height, 400 if chart_kind == "line" else 440))
    if chart_kind == "heatmap":
        layout["margin"] = dict(l=8, r=8, t=36, b=72)
        layout["coloraxis_colorbar"] = dict(
            len=0.75,
            thickness=12,
            tickfont=dict(size=10, color=COLORS["muted"]),
            outlinewidth=0,
        )
        fig.update_layout(**layout)
        fig.update_xaxes(tickangle=-90, tickfont=dict(size=9))
        style_axes(fig)
        return

    layout["margin"] = dict(l=10, r=10, t=44, b=64)
    layout["legend"] = dict(
        orientation="h",
        yanchor="top",
        y=-0.22,
        xanchor="center",
        x=0.5,
        font=dict(size=10, color=COLORS["muted"]),
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(**layout)
    fig.update_xaxes(tickformat="%d %b")
    style_axes(fig)


CHART_CONFIG: dict = {
    "responsive": True,
    "displayModeBar": False,
    "doubleClick": "reset",
    "scrollZoom": False,
}

RANGE_OPTIONS: dict[str, int | None] = {
    "৭ দিন": 6,
    "১৫ দিন": 14,
    "৩০ দিন": 29,
    "সব উপলব্ধ": None,
}


def render_public_header(latest_label: str) -> None:
    st.markdown(
        f"""
        <section class="apple-hero">
            <p class="hero-eyebrow chip chip-nowrap">DGHS দৈনিক রিপোর্ট</p>
            <h1><span class="gradient-text">বাংলাদেশ হাম</span> সতর্কতা</h1>
            <p class="hero-lead">
                স্বাস্থ্য অধিদপ্তরের দৈনিক প্রেস রিলিজ থেকে বিভাগভিত্তিক সন্দেহজনক,
                নিশ্চিত, মৃত্যু ও হাসপাতালের চাপ — এক নজরে।
                সর্বশেষ যাচাইকৃত রিপোর্ট: <b>{latest_label}</b>
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_alert_cards_html(map_data: pd.DataFrame) -> str:
    ranked = map_data.copy()
    ranked["risk_rank"] = ranked["status"].map(lambda value: RISK_STYLE[value]["rank"])
    ranked = ranked.sort_values(["risk_rank", "total_24h"], ascending=[False, False]).head(3)

    cards: list[str] = []
    for _, row in ranked.iterrows():
        style = RISK_STYLE[str(row["status"])]
        status_label = STATUS_BN[str(row["status"])]
        cards.append(
            f"""
            <article class="alert-card" style="--accent:{style['color']};--glow:{style['glow']};--soft:{style['soft']};">
                <div class="alert-head">
                    <span class="alert-dot"></span>
                    <strong>{escape(str(row['division']))}</strong>
                    <span class="chip chip-accent">{escape(status_label)}</span>
                </div>
                <div class="alert-body">
                    <div class="alert-stat">
                        <span class="alert-num">{bn_num(int(row['total_24h']))}</span>
                        <span class="alert-label">২৪ ঘণ্টায় রোগী</span>
                    </div>
                    <div class="alert-stat">
                        <span class="alert-num">{bn_num(int(row['deaths_24h']))}</span>
                        <span class="alert-label">মৃত্যু</span>
                    </div>
                </div>
            </article>
            """
        )

    return f"""
    <style>
        {iframe_shell_css()}
        .alert-panel h3 {{
            margin: 0 0 14px;
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text);
        }}
        .alert-grid {{
            display: flex;
            gap: 12px;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            -ms-overflow-style: none;
            padding-bottom: 2px;
        }}
        .alert-grid::-webkit-scrollbar {{
            display: none;
        }}
        .alert-card {{
            flex: 0 0 min(88vw, 272px);
            scroll-snap-align: start;
            border-radius: var(--radius-lg);
            padding: 16px 18px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            box-shadow: 0 0 32px var(--glow), inset 0 1px 0 rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
        }}
        .alert-head {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .alert-dot {{
            width: 8px;
            height: 8px;
            border-radius: var(--radius-pill);
            flex-shrink: 0;
            background: var(--accent);
            box-shadow: 0 0 10px var(--accent);
        }}
        .alert-head strong {{
            font-size: .98rem;
            flex: 1 1 auto;
            color: var(--text);
        }}
        .alert-head .chip {{
            flex: 0 1 auto;
            white-space: nowrap;
        }}
        .alert-body {{
            display: flex;
            gap: 20px;
        }}
        .alert-stat {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .alert-num {{
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.15;
            letter-spacing: -0.03em;
            color: var(--text);
        }}
        .alert-label {{
            font-size: .72rem;
            color: var(--muted);
            font-weight: 600;
        }}
        @media (min-width: 900px) {{
            .alert-grid {{
                overflow: visible;
            }}
            .alert-card {{
                flex: 1 1 0;
            }}
        }}
    </style>
    <section class="alert-panel">
        <h3>এখন সবচেয়ে বেশি খেয়াল রাখুন</h3>
        <div class="alert-grid">{''.join(cards)}</div>
    </section>
    """


def render_alert_chips(map_data: pd.DataFrame) -> None:
    """Styled alert cards via components.html (same approach as the map)."""
    if map_data.empty:
        return
    components.html(render_alert_cards_html(map_data), height=EMBED_HEIGHT["alert"], scrolling=False)


def build_map_data(filtered: pd.DataFrame, target_date: pd.Timestamp) -> pd.DataFrame:
    latest = filtered[filtered["report_date"] == target_date].copy()
    previous_window = filtered[filtered["report_date"] < target_date].copy()
    if latest.empty:
        return latest

    if previous_window.empty:
        latest["avg_total_7d"] = 0.0
        latest["yesterday_total"] = None
    else:
        map_baseline = (
            previous_window[previous_window["report_date"] >= target_date - pd.Timedelta(days=7)]
            .groupby("division", as_index=False)["new_total_24h"]
            .mean()
            .rename(columns={"new_total_24h": "avg_total_7d"})
        )
        yesterday_date = previous_window["report_date"].max()
        map_yesterday = (
            previous_window[previous_window["report_date"] == yesterday_date][["division", "new_total_24h"]]
            .rename(columns={"new_total_24h": "yesterday_total"})
        )
        latest = latest.merge(map_baseline, on="division", how="left")
        latest = latest.merge(map_yesterday, on="division", how="left")

    latest["avg_total_7d"] = latest["avg_total_7d"].fillna(0)
    latest["total_24h"] = latest["new_total_24h"].fillna(0).astype(int)
    latest["deaths_24h"] = latest["new_deaths_24h"].fillna(0).astype(int)
    latest["rise_vs_avg"] = latest["total_24h"] - latest["avg_total_7d"]
    latest["status"] = latest.apply(map_status, axis=1)
    return latest


def map_status(row: pd.Series) -> str:
    if row["deaths_24h"] > 0 or row["total_24h"] >= 150:
        return "High alert"
    if row["total_24h"] >= 75:
        return "Watch closely"
    if row["avg_total_7d"] > 0 and row["total_24h"] >= 20 and row["total_24h"] > row["avg_total_7d"] * 1.15:
        return "Watch closely"
    return "Lower signal"


def export_csv(stats_frame: pd.DataFrame) -> bytes:
    export = stats_frame.copy()
    export["report_date"] = export["report_date"].dt.strftime("%Y-%m-%d")
    return export.to_csv(index=False).encode("utf-8-sig")


def latest_pdf_url(reports_frame: pd.DataFrame, latest_date: date) -> str | None:
    iso = latest_date.isoformat()
    matched = reports_frame[
        reports_frame["report_date"].astype(str).str.startswith(iso)
        & (reports_frame["status"] == "extracted")
    ]
    if matched.empty:
        return None
    value = matched.iloc[0].get("pdf_url")
    return str(value) if value else None


@st.cache_data(ttl=3600)
def load_division_map() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def render_warning_map(map_data: pd.DataFrame, latest_date: pd.Timestamp) -> str:
    division_map = load_division_map()
    rows = {row["division"]: row for _, row in map_data.iterrows()}
    regions = []
    labels = []
    cards = []
    for shape in division_map["divisions"]:
        division = shape["bn"]
        row = rows.get(division)
        if row is None:
            status = "Lower signal"
            total = deaths = suspected = confirmed = 0
        else:
            status = str(row["status"])
            total = int(row["total_24h"])
            deaths = int(row["deaths_24h"])
            suspected = int(row["suspected_24h"] or 0)
            confirmed = int(row["confirmed_24h"] or 0)
        style = RISK_STYLE[status]
        status_label = STATUS_BN[status]
        label_x, label_y = shape["label"]
        alert_symbol = "!" if status == "High alert" else "•" if status == "Watch closely" else ""
        regions.append(
            f"""
            <path class="bd-region" d="{shape['path']}" fill="{style['soft']}" stroke="{style['color']}">
                <title>{escape(division)}: {escape(status_label)}, ২৪ ঘণ্টায় মোট {bn_num(total)}, মৃত্যু {bn_num(deaths)}</title>
            </path>
            """
        )
        labels.append(
            f"""
            <g class="bd-label">
                <circle cx="{label_x}" cy="{label_y - 18}" r="13" fill="{style['color']}"></circle>
                <text x="{label_x}" y="{label_y - 13}" class="bd-alert-symbol">{alert_symbol}</text>
                <text x="{label_x}" y="{label_y + 7}" class="bd-name">{escape(division)}</text>
                <text x="{label_x}" y="{label_y + 28}" class="bd-count">{bn_num(total)}</text>
            </g>
            """
        )
        cards.append(
            f"""
            <span class="chip">
                <span class="chip-dot" style="background:{style['color']};box-shadow:0 0 8px {style['color']}"></span>
                <b>{escape(division)}</b>
                <span class="chip-meta">{escape(status_label)} · {bn_num(total)} · মৃত্যু {bn_num(deaths)}</span>
            </span>
            """
        )

    return f"""
    <style>
        {iframe_shell_css()}
        :root {{
            --red: {RISK_STYLE["High alert"]["color"]};
            --gold: {RISK_STYLE["Watch closely"]["color"]};
            --green: {RISK_STYLE["Lower signal"]["color"]};
        }}
        .bd-map-panel {{
            display: grid;
            grid-template-columns: minmax(0, .86fr) minmax(300px, 1.05fr);
            gap: 18px;
            align-items: center;
            margin: 0;
            padding: 20px 20px 28px;
        }}
        .bd-map-copy h2 {{
            margin: 8px 0 10px;
            font-size: clamp(1.25rem, 3vw, 1.55rem);
            line-height: 1.12;
            letter-spacing: -0.02em;
            font-weight: 700;
            color: var(--text);
        }}
        .bd-map-copy p {{
            color: var(--muted);
            line-height: 1.55;
            margin: 0 0 14px;
            font-size: .9rem;
        }}
        .bd-map-source {{
            display: block;
            margin-top: 12px;
            color: var(--muted);
            font-size: .72rem;
            line-height: 1.35;
        }}
        .chip-dot.high {{ background: var(--red); box-shadow: 0 0 8px var(--red); }}
        .chip-dot.watch {{ background: var(--gold); box-shadow: 0 0 8px var(--gold); }}
        .chip-dot.lower {{ background: var(--green); box-shadow: 0 0 8px var(--green); }}
        .bd-map-wrap {{
            justify-self: center;
            width: min(100%, 440px);
            padding: 10px;
            border-radius: var(--radius-lg);
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--glass-border);
            overflow: hidden;
        }}
        .bd-map-svg {{
            width: 100%;
            height: auto;
            display: block;
            overflow: hidden;
        }}
        .bd-region {{
            stroke-width: 2.6;
            stroke-linejoin: round;
            filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.3));
        }}
        .bd-label text {{
            text-anchor: middle;
            pointer-events: none;
        }}
        .bd-alert-symbol {{
            fill: #ffffff;
            font-size: 15px;
            font-weight: 700;
        }}
        .bd-name {{
            fill: var(--text);
            font-size: 16px;
            font-weight: 700;
        }}
        .bd-count {{
            fill: var(--muted);
            font-size: 17px;
            font-weight: 700;
        }}
        .bd-map-cards {{
            grid-column: 1 / -1;
        }}
        @media (max-width: 760px) {{
            .bd-map-panel {{
                grid-template-columns: 1fr;
                padding: 16px;
                gap: 14px;
            }}
            .bd-map-wrap {{
                width: min(100%, 340px);
                padding: 8px;
            }}
            .bd-name {{ font-size: 14px; }}
            .bd-count {{ font-size: 15px; }}
        }}
    </style>
    <section class="bd-map-panel surface">
        <div class="bd-map-copy">
            <span class="chip">বিভাগভিত্তিক সতর্কতা</span>
            <h2>আজ কোন এলাকায় বেশি খেয়াল রাখবেন</h2>
            <p>রঙ দেখে দ্রুত বুঝুন। লাল = বেশি সতর্কতা, হলুদ = খেয়াল রাখুন, সবুজ = আজকের সংকেত কম। সংখ্যা = গত ২৪ ঘণ্টায় সন্দেহজনক + নিশ্চিত।</p>
            <div class="chip-row">
                <span class="chip"><span class="chip-dot high"></span> বেশি সতর্কতা</span>
                <span class="chip"><span class="chip-dot watch"></span> খেয়াল রাখুন</span>
                <span class="chip"><span class="chip-dot lower"></span> কম সংকেত</span>
            </div>
            <small class="bd-map-source">তথ্য: স্বাস্থ্য অধিদপ্তরের দৈনিক পিডিএফ রিপোর্ট থেকে।</small>
        </div>
        <div class="bd-map-wrap" aria-label="বাংলাদেশের বিভাগভিত্তিক সতর্কতা মানচিত্র {bn_date(latest_date.date())}">
            <svg class="bd-map-svg" viewBox="{division_map['viewBox']}" role="img">
                <rect x="0" y="0" width="{division_map['width']}" height="{division_map['height']}" rx="20" fill="#0a0a0a"></rect>
                <g>{''.join(regions)}</g>
                <g>{''.join(labels)}</g>
            </svg>
        </div>
        <div class="bd-map-cards chip-row-scroll">{''.join(cards)}</div>
    </section>
    """


@st.cache_data(ttl=60)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        stats = pd.read_sql_query("SELECT * FROM division_daily_stats", conn, parse_dates=["report_date"])
        reports = pd.read_sql_query("SELECT * FROM reports ORDER BY report_date DESC", conn)
    if not stats.empty:
        stats["report_date"] = pd.to_datetime(stats["report_date"], errors="coerce")
        stats = stats.dropna(subset=["report_date"])
    return stats, reports

stats, reports = load_data()

if stats.empty:
    st.info("এখনও দেখানোর মতো রিপোর্ট ডেটা নেই। অ্যাডমিন প্যানেল থেকে নতুন রিপোর্ট আনুন।")
    if not reports.empty:
        st.subheader("যেসব রিপোর্ট দেখতে হবে")
        st.dataframe(reports[["report_date", "title", "status", "validation_message"]], use_container_width=True)
    st.stop()

def _iso_dates(series: pd.Series) -> set[str]:
    return set(
        pd.to_datetime(series, errors="coerce")
        .dropna()
        .dt.strftime("%Y-%m-%d")
    )


valid_report_dates = _iso_dates(reports.loc[reports["status"] == "extracted", "report_date"])
review_count = int((reports["status"] != "extracted").sum()) if not reports.empty else 0

show_review_rows = False
validated_count = int((reports["status"] == "extracted").sum()) if not reports.empty else 0

if not show_review_rows:
    stats = stats[stats["report_date"].dt.strftime("%Y-%m-%d").isin(valid_report_dates)].copy()

if stats.empty:
    st.warning("এখনও যাচাই করা রিপোর্ট পাওয়া যায়নি।")
    st.stop()

all_min_date = stats["report_date"].min().date()
all_max_date = stats["report_date"].max().date()
public_divisions = sorted(stats["division"].dropna().unique())

render_public_header(bn_date(all_max_date))

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    range_label = st.selectbox("চার্ট ও টেবিলের সময়সীমা", list(RANGE_OPTIONS.keys()), index=1)
range_days = RANGE_OPTIONS[range_label]
if range_days is None:
    start_date = all_min_date
else:
    start_date = max(all_min_date, all_max_date - pd.Timedelta(days=range_days))
end_date = all_max_date

divisions = sorted(stats["division"].dropna().unique())

filtered = stats[
    (stats["report_date"].dt.date >= start_date)
    & (stats["report_date"].dt.date <= end_date)
].copy()
filtered["new_total_24h"] = filtered["suspected_24h"].fillna(0) + filtered["confirmed_24h"].fillna(0)
filtered["new_deaths_24h"] = filtered["suspected_deaths_24h"].fillna(0) + filtered["confirmed_deaths_24h"].fillna(0)
filtered["net_admitted_24h"] = filtered["admitted_24h"].fillna(0) - filtered["discharged_24h"].fillna(0)

available_map_dates = sorted(filtered["report_date"].dt.date.unique())
with filter_col2:
    map_date_value = st.selectbox(
        "মানচিত্রের তারিখ",
        options=available_map_dates,
        index=len(available_map_dates) - 1,
        format_func=lambda value: bn_date(value),
    )

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    st.download_button(
        "CSV ডাউনলোড",
        data=export_csv(filtered),
        file_name=f"measles_{start_date}_{end_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )
pdf_url = latest_pdf_url(reports, all_max_date)
with btn_col2:
    if pdf_url:
        st.link_button("সর্বশেষ DGHS PDF", pdf_url, use_container_width=True)
    else:
        st.link_button(
            "DGHS প্রেস রিলিজ",
            "https://dghs.gov.bd/pages/press-releases/",
            use_container_width=True,
        )

with st.expander("কীভাবে পড়বেন"):
    st.markdown(
        """
        - **২৪ ঘণ্টার সংখ্যা** = গত রিপোর্টিং দিনের (সকাল ৮টা–৮টা) নতুন রোগী।
        - **মোট নিশ্চিত** = outbreak শুরু থেকে জমা নিশ্চিত রোগীর সংখ্যা।
        - **লাল সতর্কতা** = বেশি রোগী বা কোনো মৃত্যু রিপোর্ট; **হলুদ** = মাঝারি চাপ বা বাড়ছে।
        - ডেটা DGHS PDF থেকে স্বয়ংক্রিয়ভাবে আসে; যাচাই ব্যর্থ হলে প্রকাশ হয় না।
        """
    )

map_date = pd.Timestamp(map_date_value)
map_data = build_map_data(filtered, map_date)
latest_date = filtered["report_date"].max()
latest = filtered[filtered["report_date"] == latest_date].copy()
previous_window = filtered[filtered["report_date"] < latest_date].copy()

_now_utc = pd.Timestamp.utcnow()
if _now_utc.tzinfo is None:
    _now_utc = _now_utc.tz_localize("UTC")
today_bd = _now_utc.tz_convert("Asia/Dhaka").normalize().date()
days_behind = (today_bd - all_max_date).days
if days_behind >= 2:
    st.markdown(
        f"""
        <div class="stale-data-banner">
            <b>সর্বশেষ যাচাই করা রিপোর্ট {bn_date(all_max_date)} এর।</b>
            এর পরের {bn_num(days_behind)} দিনের পিডিএফ এখনও যুক্ত হয়নি —
            স্বয়ংক্রিয় আপডেট চেষ্টা করছে, অথবা অ্যাডমিন প্যানেল থেকে যাচাই করে যোগ করা হবে।
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="glass-strip">
        <span class="chip chip-nowrap">সর্বশেষ: <b>{bn_date(all_max_date)}</b></span>
        <span class="chip chip-nowrap">রিপোর্ট: <b>{bn_num(validated_count)}</b></span>
        <span class="chip chip-nowrap">বিভাগ: <b>{bn_num(len(public_divisions))}</b></span>
        <span class="chip chip-nowrap">সময়: <b>{range_label}</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

today_suspected = int(latest["suspected_24h"].fillna(0).sum())
today_confirmed = int(latest["confirmed_24h"].fillna(0).sum())
today_deaths = int(latest[["suspected_deaths_24h", "confirmed_deaths_24h"]].fillna(0).sum().sum())
total_confirmed = int(latest["confirmed_total"].fillna(0).sum())

st.markdown(
    f"""
    <div class="metric-grid">
        <div class="metric-tile green"><b>২৪ ঘণ্টায় সন্দেহজনক</b><span>{bn_num(today_suspected)}</span></div>
        <div class="metric-tile blue"><b>২৪ ঘণ্টায় নিশ্চিত</b><span>{bn_num(today_confirmed)}</span></div>
        <div class="metric-tile coral"><b>২৪ ঘণ্টায় মৃত্যু</b><span>{bn_num(today_deaths)}</span></div>
        <div class="metric-tile violet"><b>মোট নিশ্চিত</b><span>{bn_num(total_confirmed)}</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_alert_chips(map_data)

if not map_data.empty:
    components.html(render_warning_map(map_data, map_date), height=EMBED_HEIGHT["map_mobile"], scrolling=False)
else:
    st.info("নির্বাচিত তারিখে মানচিত্র দেখানোর মতো ডেটা নেই।")

bar_source = map_data.sort_values("new_total_24h", ascending=True)
if not bar_source.empty:
    section_title(f"{bn_date(map_date.date())} — বিভাগভিত্তিক ২৪ ঘণ্টার চাপ", "নির্বাচিত তারিখে কোন বিভাগে চাপ বেশি")
    bar_fig = px.bar(
        bar_source,
        x="new_total_24h",
        y="division",
        orientation="h",
        color="status",
        color_discrete_map={
            "High alert": RISK_STYLE["High alert"]["color"],
            "Watch closely": RISK_STYLE["Watch closely"]["color"],
            "Lower signal": RISK_STYLE["Lower signal"]["color"],
        },
        labels={
            "new_total_24h": "২৪ ঘণ্টায় সন্দেহজনক + নিশ্চিত",
            "division": "বিভাগ",
            "status": "সতর্কতা",
        },
    )
    bar_fig.update_layout(showlegend=False, height=max(320, 42 * len(bar_source)))
    bar_fig.update_xaxes(automargin=True)
    bar_fig.update_yaxes(automargin=True)
    apply_mobile_friendly_layout(bar_fig, height=max(320, 42 * len(bar_source)), chart_kind="heatmap")
    st.plotly_chart(bar_fig, use_container_width=True, config=CHART_CONFIG)

section_title("এখন কোথায় বেশি বাড়ছে?", "সর্বশেষ রিপোর্টের বিভাগভিত্তিক তালিকা")
ranking = (
    latest[
        [
            "division",
            "new_total_24h",
            "suspected_24h",
            "confirmed_24h",
            "new_deaths_24h",
            "admitted_24h",
            "discharged_24h",
            "net_admitted_24h",
        ]
    ]
    .rename(
        columns={
            "division": "বিভাগ",
            "new_total_24h": "২৪ ঘণ্টায় সন্দেহজনক + নিশ্চিত",
            "suspected_24h": "২৪ ঘণ্টায় সন্দেহজনক",
            "confirmed_24h": "২৪ ঘণ্টায় নিশ্চিত",
            "new_deaths_24h": "২৪ ঘণ্টায় মৃত্যু",
            "admitted_24h": "২৪ ঘণ্টায় ভর্তি",
            "discharged_24h": "২৪ ঘণ্টায় ছাড়পত্র",
            "net_admitted_24h": "ভর্তি চাপ",
        }
    )
    .sort_values(["২৪ ঘণ্টায় সন্দেহজনক + নিশ্চিত", "২৪ ঘণ্টায় নিশ্চিত"], ascending=False)
)
ranking_display = ranking.copy()
for column in ranking_display.columns:
    if column != "বিভাগ":
        ranking_display[column] = ranking_display[column].map(bn_table_value)
st.dataframe(ranking_display, use_container_width=True, hide_index=True)

if not previous_window.empty:
    seven_day = previous_window[previous_window["report_date"] >= latest_date - pd.Timedelta(days=7)]
    yesterday_date = previous_window["report_date"].max()
    yesterday = previous_window[previous_window["report_date"] == yesterday_date][
        ["division", "new_total_24h", "new_deaths_24h"]
    ]
    baseline = seven_day.groupby("division", as_index=False)[["new_total_24h", "new_deaths_24h"]].mean()
    alerts = latest.merge(baseline, on="division", how="left", suffixes=("", "_avg7"))
    alerts = alerts.merge(yesterday, on="division", how="left", suffixes=("", "_yesterday"))
    alerts["case_rise_vs_avg"] = alerts["new_total_24h"] - alerts["new_total_24h_avg7"].fillna(0)
    alerts["death_rise_vs_avg"] = alerts["new_deaths_24h"] - alerts["new_deaths_24h_avg7"].fillna(0)
    alerts = alerts.sort_values(["case_rise_vs_avg", "new_total_24h"], ascending=False)

    def pct_change(current: float, baseline_value: float) -> str:
        if pd.isna(baseline_value) or baseline_value <= 0:
            return "আগের গড় নেই"
        change = ((current - baseline_value) / baseline_value) * 100
        direction = "বেশি" if change >= 0 else "কম"
        return f"{bn_num(round(abs(change)))}% {direction}"

    section_title("৭ দিনের তুলনায় কী বোঝা যাচ্ছে", "গড়ের সঙ্গে তুলনা করে দ্রুত পড়ুন")
    with st.expander("বিস্তারিত বিভাগভিত্তিক ব্যাখ্যা দেখুন", expanded=False):
        for _, row in alerts.iterrows():
            cases_today = int(row["new_total_24h"] or 0)
            cases_avg = float(row["new_total_24h_avg7"] or 0)
            deaths_today = int(row["new_deaths_24h"] or 0)
            deaths_avg = float(row["new_deaths_24h_avg7"] or 0)
            yesterday_cases = row.get("new_total_24h_yesterday")
            yesterday_deaths = row.get("new_deaths_24h_yesterday")
            status = "বাড়ছে" if cases_today > cases_avg else "কম বা স্থির"

            death_sentence = "গত ২৪ ঘণ্টায় মৃত্যু রিপোর্ট হয়নি"
            if deaths_today:
                death_sentence = f"মৃত্যু **{bn_num(deaths_today)}**, ৭ দিনের গড়ের চেয়ে {pct_change(deaths_today, deaths_avg)}"
                if not pd.isna(yesterday_deaths):
                    death_sentence += f", গতকালের চেয়ে {pct_change(deaths_today, yesterday_deaths)}"

            st.write(
                f"**{row['division']}** — {status}: গত ২৪ ঘণ্টায় সন্দেহজনক + নিশ্চিত **{bn_num(cases_today)}**, "
                f"৭ দিনের গড়ের চেয়ে {pct_change(cases_today, cases_avg)}"
                f"{'' if pd.isna(yesterday_cases) else f', গতকালের চেয়ে {pct_change(cases_today, yesterday_cases)}'}. "
                f"{death_sentence}."
            )

section_title("সময়ের সাথে প্রবণতা", "চার্ট ও হিটম্যাপ দিয়ে দীর্ঘমেয়াদি প্যাটার্ন দেখুন")
chart_tab, heatmap_tab = st.tabs(["প্রবণতা", "হিটম্যাপ"])

with chart_tab:
    trend_options = {
        "২৪ ঘণ্টার রোগের চাপ": {
            "column": "new_total_24h",
            "label": "২৪ ঘণ্টায় সন্দেহজনক + নিশ্চিত",
            "description": "হাম-এর চাপ বাড়ছে নাকি কমছে, এটা বোঝার সবচেয়ে সহজ সংকেত।",
        },
        "২৪ ঘণ্টার মৃত্যু": {
            "column": "new_deaths_24h",
            "label": "২৪ ঘণ্টায় মৃত্যু",
            "description": "গত ২৪ ঘণ্টায় রিপোর্ট হওয়া সন্দেহজনক ও নিশ্চিত মৃত্যুর সংখ্যা।",
        },
        "হাসপাতালের চাপ": {
            "column": "net_admitted_24h",
            "label": "২৪ ঘণ্টায় ভর্তি - ছাড়পত্র",
            "description": "ভর্তি ও ছাড়পত্র মিলিয়ে হাসপাতালের চাপ বাড়ছে কি না।",
        },
        "মোট নিশ্চিত রোগী": {
            "column": "confirmed_total",
            "label": "মোট নিশ্চিত রোগী",
            "description": "এ পর্যন্ত নিশ্চিত রোগীর মোট চাপ।",
        },
    }
    control_col1, control_col2 = st.columns([1, 1])
    with control_col1:
        trend_focus = st.selectbox(
            "কোন প্রবণতা দেখবেন",
            list(trend_options.keys()),
        )
        metric = trend_options[trend_focus]["column"]
        st.caption(trend_options[trend_focus]["description"])

    latest_by_division = (
        filtered[filtered["report_date"] == filtered["report_date"].max()]
        .groupby("division", as_index=False)[metric]
        .sum()
        .sort_values(metric, ascending=False)
    )
    top_three = latest_by_division.head(3)["division"].tolist()
    top_five = latest_by_division.head(5)["division"].tolist()

    with control_col2:
        division_preset = st.selectbox("বিভাগ দেখুন", ["শীর্ষ ৩", "শীর্ষ ৫", "সব", "নিজে বাছাই"])

    if division_preset == "শীর্ষ ৩":
        chart_divisions = top_three
    elif division_preset == "শীর্ষ ৫":
        chart_divisions = top_five
    elif division_preset == "সব":
        chart_divisions = divisions
    else:
        chart_divisions = st.multiselect("বিভাগ", divisions, default=top_three or divisions[:3])

    chart_data = filtered[filtered["division"].isin(chart_divisions)].copy()
    if chart_data.empty:
        st.info("প্রবণতা দেখতে অন্তত একটি বিভাগ বাছাই করুন।")
    else:
        national_trend = (
            filtered.groupby("report_date", as_index=False)[metric]
            .sum()
            .assign(division=TREND_LINE_BD)
        )
        chart_lines = pd.concat(
            [
                national_trend,
                chart_data[["report_date", "division", metric]],
            ],
            ignore_index=True,
        )
        fig = px.line(
            chart_lines.sort_values("report_date"),
            x="report_date",
            y=metric,
            color="division",
            markers=True,
            color_discrete_map={TREND_LINE_BD: NATIONAL_LINE},
            color_discrete_sequence=CHART_DIVISION_COLORS,
            labels={
                "report_date": "তারিখ",
                "division": "বিভাগ",
                metric: trend_options[trend_focus]["label"],
            },
        )
        fig.update_xaxes(
            range=[
                filtered["report_date"].min(),
                filtered["report_date"].max(),
            ]
        )
        fig.update_traces(line=dict(width=2.4))
        fig.update_traces(selector=dict(name=TREND_LINE_BD), line=dict(width=5), marker=dict(size=9))
        fig.update_layout(
            yaxis_title=trend_options[trend_focus]["label"],
            legend_title_text="",
        )
        apply_mobile_friendly_layout(fig, height=380)
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

        daily_summary = (
            filtered.groupby("report_date", as_index=False)
            .agg(
                total_24h=("new_total_24h", "sum"),
                deaths_24h=("new_deaths_24h", "sum"),
                net_admitted_24h=("net_admitted_24h", "sum"),
            )
            .sort_values("report_date")
        )
        daily_summary["৭ দিনের গড়"] = daily_summary["total_24h"].rolling(7, min_periods=1).mean().round(1)
        daily_summary["গতকাল থেকে পরিবর্তন"] = daily_summary["total_24h"].diff().fillna(0).astype(int)
        daily_summary = daily_summary.rename(
            columns={
                "report_date": "তারিখ",
                "total_24h": "২৪ ঘণ্টায় সন্দেহজনক + নিশ্চিত",
                "deaths_24h": "২৪ ঘণ্টায় মৃত্যু",
                "net_admitted_24h": "ভর্তি চাপ",
            }
        )
        daily_summary["তারিখ"] = daily_summary["তারিখ"].dt.strftime("%Y-%m-%d").map(bn_date)
        daily_display = daily_summary.tail(7).copy()
        for column in daily_display.columns:
            if column != "তারিখ":
                daily_display[column] = daily_display[column].map(bn_table_value)
        st.dataframe(daily_display, use_container_width=True, hide_index=True)

with heatmap_tab:
    heat_col1, heat_col2 = st.columns([1, 1])
    with heat_col1:
        heat_metric = st.selectbox(
            "হিটম্যাপে কী দেখবেন",
            ["suspected_24h", "confirmed_24h", "admitted_24h", "confirmed_total"],
            format_func=lambda x: {
                "suspected_24h": "২৪ ঘণ্টায় সন্দেহজনক",
                "confirmed_24h": "২৪ ঘণ্টায় নিশ্চিত",
                "admitted_24h": "২৪ ঘণ্টায় ভর্তি",
                "confirmed_total": "মোট নিশ্চিত",
            }[x],
        )
    heat_latest = (
        filtered[filtered["report_date"] == filtered["report_date"].max()]
        .groupby("division", as_index=False)[heat_metric]
        .sum()
        .sort_values(heat_metric, ascending=False)
    )
    with heat_col2:
        heat_divisions = st.multiselect("বিভাগ", divisions, default=heat_latest.head(6)["division"].tolist())

    heat_data = filtered[filtered["division"].isin(heat_divisions)].copy()
    if heat_data.empty:
        st.info("হিটম্যাপ দেখতে অন্তত একটি বিভাগ বাছাই করুন।")
    else:
        heat = heat_data.pivot_table(index="division", columns=heat_data["report_date"].dt.date, values=heat_metric, aggfunc="sum").fillna(0)
        heat.columns = [col.strftime("%d/%m") for col in heat.columns]
        fig = px.imshow(
            heat,
            aspect="auto",
            color_continuous_scale=[
                [0.0, "#1d1d1f"],
                [0.2, "#5e5ce6"],
                [0.45, "#ff9f0a"],
                [0.7, "#ff375f"],
                [1.0, "#ff453a"],
            ],
            labels={"x": "তারিখ", "y": "বিভাগ", "color": "সংখ্যা"},
        )
        apply_mobile_friendly_layout(fig, height=360, chart_kind="heatmap")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.markdown(
    """
    <div class="page-footer">
        তথ্যসূত্র: <a href="https://dghs.gov.bd/pages/press-releases/" target="_blank" rel="noopener">
        স্বাস্থ্য অধিদপ্তর (DGHS)</a> দৈনিক হাম প্রেস রিলিজ ·
        ডেটা স্বয়ংক্রিয়ভাবে PDF থেকে সংগ্রহ ও যাচাই করা হয় ·
        <a href="https://github.com/tuhinaranyo/BD_measles_outbreak_map" target="_blank" rel="noopener">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
