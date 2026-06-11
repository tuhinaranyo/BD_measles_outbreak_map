from __future__ import annotations

from html import escape
import json
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from measles_dashboard.config import DB_PATH, ROOT
from measles_dashboard.db import init_db
from measles_dashboard.ui import inject_style


st.set_page_config(page_title="বাংলাদেশ হাম সতর্কতা", layout="wide")
inject_style()


RISK_STYLE = {
    "High alert": {"color": "#d71920", "soft": "#fff0ef", "rank": 3},
    "Watch closely": {"color": "#c5922d", "soft": "#fff8e6", "rank": 2},
    "Lower signal": {"color": "#006a4e", "soft": "#edf7f0", "rank": 1},
}

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
    """Plotly layout tweaks so charts read well on a 360–420px phone."""
    if chart_kind == "heatmap":
        fig.update_layout(
            autosize=True,
            height=max(height, 440),
            margin=dict(l=4, r=4, t=36, b=72),
            font=dict(size=11),
            coloraxis_colorbar=dict(len=0.75, thickness=12, tickfont=dict(size=10)),
        )
        fig.update_xaxes(automargin=True, tickangle=-90, tickfont=dict(size=9))
        fig.update_yaxes(automargin=True, tickfont=dict(size=10))
        return

    fig.update_layout(
        autosize=True,
        height=max(height, 420),
        margin=dict(l=8, r=8, t=48, b=56),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
            itemsizing="constant",
        ),
        font=dict(size=12),
    )
    fig.update_xaxes(automargin=True, tickformat="%d %b", tickfont=dict(size=10))
    fig.update_yaxes(automargin=True, tickfont=dict(size=10))


CHART_CONFIG: dict = {
    "responsive": True,
    "displayModeBar": False,
    "doubleClick": "reset",
    "scrollZoom": False,
}


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
            <div class="bd-map-card">
                <span style="background:{style['color']}"></span>
                <b>{escape(division)}</b>
                <small>{escape(status_label)} · ২৪ ঘণ্টায় {bn_num(total)} · মৃত্যু {bn_num(deaths)}</small>
            </div>
            """
        )

    return f"""
    <style>
        :root {{
            --ink: #14231d;
            --muted: #65736c;
            --line: #dfe8df;
            --green: #006a4e;
            --red: #d71920;
            --gold: #c5922d;
        }}
        body {{
            margin: 0;
            font-family: "Source Sans Pro", Arial, sans-serif;
            color: var(--ink);
            background: transparent;
        }}
        .bd-map-panel {{
            box-sizing: border-box;
            display: grid;
            grid-template-columns: minmax(0, .86fr) minmax(320px, 1.1fr);
            gap: 18px;
            align-items: center;
            margin: 0;
            padding: 20px;
            border: 1px solid rgba(0, 106, 78, .18);
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(255,255,255,.96), rgba(237,247,240,.92)),
                linear-gradient(90deg, rgba(0,106,78,.06) 1px, transparent 1px);
            box-shadow: 0 18px 44px rgba(0, 67, 50, .09);
        }}
        .public-kicker {{
            display: inline-flex;
            color: var(--red);
            font-size: .78rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: .04em;
            margin-bottom: 8px;
        }}
        .bd-map-copy h2 {{
            margin: 4px 0 8px;
            font-size: 1.65rem;
            line-height: 1.12;
        }}
        .bd-map-copy p {{
            color: var(--muted);
            line-height: 1.55;
            margin: 0 0 12px;
            font-size: .96rem;
        }}
        .bd-map-legend, .bd-map-cards {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .bd-map-source {{
            display: block;
            margin-top: 10px;
            color: #718178;
            font-size: .72rem;
            line-height: 1.35;
        }}
        .bd-map-legend span, .bd-map-card {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            min-height: 30px;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(0, 67, 50, .12);
            background: rgba(255, 255, 255, .88);
            color: var(--ink);
            font-size: .78rem;
            font-weight: 800;
        }}
        .bd-map-legend i, .bd-map-card span {{
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }}
        .bd-map-legend .high {{ background: var(--red); }}
        .bd-map-legend .watch {{ background: var(--gold); }}
        .bd-map-legend .lower {{ background: var(--green); }}
        .bd-map-wrap {{
            justify-self: center;
            width: min(100%, 470px);
            padding: 10px;
            border-radius: 22px;
            background: linear-gradient(180deg, #ffffff, #f2faf4);
            border: 1px solid rgba(0, 106, 78, .12);
        }}
        .bd-map-svg {{
            width: 100%;
            height: auto;
            display: block;
            overflow: visible;
        }}
        .bd-region {{
            stroke-width: 3.2;
            stroke-linejoin: round;
            filter: drop-shadow(0 6px 10px rgba(0, 67, 50, .10));
        }}
        .bd-label text {{
            text-anchor: middle;
            pointer-events: none;
        }}
        .bd-alert-symbol {{
            fill: #ffffff;
            font-size: 17px;
            font-weight: 900;
        }}
        .bd-name {{
            fill: #16372d;
            font-size: 18px;
            font-weight: 900;
        }}
        .bd-count {{
            fill: #5f2f31;
            font-size: 19px;
            font-weight: 900;
        }}
        .bd-map-cards {{
            grid-column: 1 / -1;
        }}
        .bd-map-card b {{
            font-size: .8rem;
        }}
        .bd-map-card small {{
            color: var(--muted);
            font-size: .74rem;
            font-weight: 750;
        }}
        @media (max-width: 760px) {{
            .bd-map-panel {{
                grid-template-columns: 1fr;
                padding: 14px;
                gap: 12px;
                border-radius: 16px;
            }}
            .bd-map-copy h2 {{
                font-size: 1.35rem;
            }}
            .bd-map-wrap {{
                width: min(100%, 360px);
                padding: 6px;
            }}
            .bd-name {{
                font-size: 16px;
            }}
            .bd-count {{
                font-size: 17px;
            }}
            .bd-map-cards {{
                max-height: 160px;
                overflow: auto;
                padding-bottom: 2px;
            }}
        }}
        @media (max-width: 480px) {{
            .bd-map-panel {{
                padding: 12px;
            }}
            .bd-map-copy h2 {{
                font-size: 1.2rem;
            }}
            .bd-map-copy p {{
                font-size: .88rem;
            }}
            .bd-name {{
                font-size: 14px;
            }}
            .bd-count {{
                font-size: 15px;
            }}
            .bd-alert-symbol {{
                font-size: 14px;
            }}
            .bd-map-cards {{
                max-height: 120px;
            }}
        }}
    </style>
    <section class="bd-map-panel">
        <div class="bd-map-copy">
            <div class="public-kicker">বিভাগভিত্তিক সতর্কতা</div>
            <h2>আজ কোন এলাকায় বেশি খেয়াল রাখবেন</h2>
            <p>রঙ দেখে দ্রুত বুঝুন। লাল মানে বেশি সতর্কতা, হলুদ মানে খেয়াল রাখুন, সবুজ মানে আজকের সংকেত কম। মানচিত্রের সংখ্যা হলো গত ২৪ ঘণ্টায় সন্দেহজনক ও নিশ্চিত রোগীর মোট সংখ্যা।</p>
            <div class="bd-map-legend">
                <span><i class="high"></i> বেশি সতর্কতা</span>
                <span><i class="watch"></i> খেয়াল রাখুন</span>
                <span><i class="lower"></i> কম সংকেত</span>
            </div>
            <small class="bd-map-source">তথ্য: স্বাস্থ্য অধিদপ্তরের দৈনিক পিডিএফ রিপোর্ট থেকে।</small>
        </div>
        <div class="bd-map-wrap" aria-label="বাংলাদেশের বিভাগভিত্তিক সতর্কতা মানচিত্র {bn_date(latest_date.date())}">
            <svg class="bd-map-svg" viewBox="{division_map['viewBox']}" role="img">
                <rect x="0" y="0" width="{division_map['width']}" height="{division_map['height']}" rx="28" fill="#f7fbf7"></rect>
                <g>{''.join(regions)}</g>
                <g>{''.join(labels)}</g>
            </svg>
        </div>
        <div class="bd-map-cards">{''.join(cards)}</div>
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
    <div class="update-strip">
        <span>সর্বশেষ: <b>{bn_date(all_max_date)}</b></span>
        <span>রিপোর্ট: <b>{bn_num(validated_count)}</b></span>
        <span>বিভাগ: <b>{bn_num(len(public_divisions))}</b></span>
        <span>সময়: <b>শেষ ১৫ দিন</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

default_start_date = max(all_min_date, all_max_date - pd.Timedelta(days=14))
start_date, end_date = default_start_date, all_max_date

divisions = sorted(stats["division"].dropna().unique())

filtered = stats[
    (stats["report_date"].dt.date >= start_date)
    & (stats["report_date"].dt.date <= end_date)
].copy()
filtered["new_total_24h"] = filtered["suspected_24h"].fillna(0) + filtered["confirmed_24h"].fillna(0)
filtered["new_deaths_24h"] = filtered["suspected_deaths_24h"].fillna(0) + filtered["confirmed_deaths_24h"].fillna(0)
filtered["net_admitted_24h"] = filtered["admitted_24h"].fillna(0) - filtered["discharged_24h"].fillna(0)

latest_date = filtered["report_date"].max()
latest = filtered[filtered["report_date"] == latest_date].copy()
previous_window = filtered[filtered["report_date"] < latest_date].copy()

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

map_data = latest.copy()
if previous_window.empty:
    map_data["avg_total_7d"] = 0.0
    map_data["yesterday_total"] = None
else:
    map_baseline = (
        previous_window[previous_window["report_date"] >= latest_date - pd.Timedelta(days=7)]
        .groupby("division", as_index=False)["new_total_24h"]
        .mean()
        .rename(columns={"new_total_24h": "avg_total_7d"})
    )
    yesterday_date = previous_window["report_date"].max()
    map_yesterday = (
        previous_window[previous_window["report_date"] == yesterday_date][["division", "new_total_24h"]]
        .rename(columns={"new_total_24h": "yesterday_total"})
    )
    map_data = map_data.merge(map_baseline, on="division", how="left")
    map_data = map_data.merge(map_yesterday, on="division", how="left")

map_data["avg_total_7d"] = map_data["avg_total_7d"].fillna(0)
map_data["total_24h"] = map_data["new_total_24h"].fillna(0).astype(int)
map_data["deaths_24h"] = map_data["new_deaths_24h"].fillna(0).astype(int)
map_data["rise_vs_avg"] = map_data["total_24h"] - map_data["avg_total_7d"]
max_total_24h = max(int(map_data["total_24h"].max()), 1)


def map_status(row: pd.Series) -> str:
    if row["deaths_24h"] > 0 or row["total_24h"] >= 150:
        return "High alert"
    if row["total_24h"] >= 75:
        return "Watch closely"
    if row["avg_total_7d"] > 0 and row["total_24h"] >= 20 and row["total_24h"] > row["avg_total_7d"] * 1.15:
        return "Watch closely"
    return "Lower signal"


map_data["status"] = map_data.apply(map_status, axis=1)
division_names = {item["bn"]: item["name"] for item in load_division_map()["divisions"]}
map_data["division_label"] = map_data["division"].map(lambda value: division_names.get(value, value))

components.html(render_warning_map(map_data, latest_date), height=620, scrolling=True)

st.subheader("এখন কোথায় বেশি বাড়ছে?")
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

    st.subheader("৭ দিনের তুলনায় কী বোঝা যাচ্ছে")
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
            color_discrete_map={TREND_LINE_BD: "#d71920"},
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
        fig = px.imshow(heat, aspect="auto", color_continuous_scale="YlOrRd", labels={"x": "তারিখ", "y": "বিভাগ", "color": "সংখ্যা"})
        apply_mobile_friendly_layout(fig, height=360, chart_kind="heatmap")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
