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


st.set_page_config(page_title="DGHS Measles Dashboard", layout="wide")
inject_style()


RISK_STYLE = {
    "High alert": {"color": "#d71920", "soft": "#fff0ef", "rank": 3},
    "Watch closely": {"color": "#c5922d", "soft": "#fff8e6", "rank": 2},
    "Lower signal": {"color": "#006a4e", "soft": "#edf7f0", "rank": 1},
}

MAP_PATH = ROOT / "assets" / "bd_divisions_svg.json"


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
        label_x, label_y = shape["label"]
        alert_symbol = "!" if status == "High alert" else "•" if status == "Watch closely" else ""
        regions.append(
            f"""
            <path class="bd-region" d="{shape['path']}" fill="{style['soft']}" stroke="{style['color']}">
                <title>{escape(shape['name'])}: {escape(status)}, 24h total {total:,}, deaths {deaths:,}</title>
            </path>
            """
        )
        labels.append(
            f"""
            <g class="bd-label">
                <circle cx="{label_x}" cy="{label_y - 18}" r="13" fill="{style['color']}"></circle>
                <text x="{label_x}" y="{label_y - 13}" class="bd-alert-symbol">{alert_symbol}</text>
                <text x="{label_x}" y="{label_y + 7}" class="bd-name">{escape(shape['name'])}</text>
                <text x="{label_x}" y="{label_y + 28}" class="bd-count">{total:,}</text>
            </g>
            """
        )
        cards.append(
            f"""
            <div class="bd-map-card">
                <span style="background:{style['color']}"></span>
                <b>{escape(shape['name'])}</b>
                <small>{escape(status)} · 24h {total:,} · deaths {deaths:,}</small>
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
                max-height: 132px;
                overflow: auto;
                padding-bottom: 2px;
            }}
        }}
    </style>
    <section class="bd-map-panel">
        <div class="bd-map-copy">
            <div class="public-kicker">Division warning map</div>
            <h2>Where families should watch closely today</h2>
            <p>Static division borders with live alert colors from the latest validated DGHS report. The number on each division is suspected + confirmed reports in the last 24 hours.</p>
            <div class="bd-map-legend">
                <span><i class="high"></i> High alert</span>
                <span><i class="watch"></i> Watch closely</span>
                <span><i class="lower"></i> Lower signal</span>
            </div>
            <small class="bd-map-source">Boundary source: Bangladesh GeoJSON / geoBoundaries.</small>
        </div>
        <div class="bd-map-wrap" aria-label="Bangladesh division warning map for {latest_date.date()}">
            <svg class="bd-map-svg" viewBox="{division_map['viewBox']}" role="img">
                <rect x="0" y="0" width="{division_map['width']}" height="{division_map['height']}" rx="28" fill="#f7fbf7"></rect>
                <g>{''.join(regions)}</g>
                <g>{''.join(labels)}</g>
            </svg>
        </div>
        <div class="bd-map-cards">{''.join(cards)}</div>
    </section>
    """


@st.cache_data(ttl=120)
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

st.markdown(
    """
    <section class="public-header">
        <div>
            <div class="public-kicker">Bangladesh measles alert</div>
            <h1>Protect children by seeing where measles is rising</h1>
            <p>Daily DGHS reports made easier to understand, so families, communities, and caregivers can notice risk early and act with care.</p>
        </div>
    </section>
    <div class="care-note">
        <div class="care-mark">!</div>
        <div>
            <b>Every number here represents families who need protection and support.</b>
            <span>Use the latest 24-hour signals to stay aware, check vaccination status, and seek medical advice quickly if a child has fever with rash or measles-like symptoms.</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if stats.empty:
    st.info("No extracted report data yet. Run `python update_data.py`, or place PDFs in `data/raw_pdfs` and run `python update_data.py --local-only`.")
    if not reports.empty:
        st.subheader("Reports needing attention")
        st.dataframe(reports[["report_date", "title", "status", "validation_message"]], use_container_width=True)
    st.stop()

valid_report_dates = set(reports.loc[reports["status"] == "extracted", "report_date"].astype(str))
review_count = int((reports["status"] != "extracted").sum()) if not reports.empty else 0
all_min_date = stats["report_date"].min().date()
all_max_date = stats["report_date"].max().date()
public_divisions = sorted(stats["division"].dropna().unique())

show_review_rows = False
validated_count = int((reports["status"] == "extracted").sum()) if not reports.empty else 0
st.markdown(
    f"""
    <div class="update-strip">
        <span>Latest: <b>{all_max_date}</b></span>
        <span>Reports: <b>{validated_count}</b></span>
        <span>Divisions: <b>{len(public_divisions)}</b></span>
        <span>Window: <b>15 days</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)
if not show_review_rows:
    stats = stats[stats["report_date"].dt.strftime("%Y-%m-%d").isin(valid_report_dates)].copy()

if stats.empty:
    st.warning("No validated report rows are available for the selected mode.")
    st.stop()

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
        <div class="metric-tile green"><b>24h suspected</b><span>{today_suspected:,}</span></div>
        <div class="metric-tile blue"><b>24h confirmed</b><span>{today_confirmed:,}</span></div>
        <div class="metric-tile coral"><b>24h deaths</b><span>{today_deaths:,}</span></div>
        <div class="metric-tile violet"><b>Cumulative confirmed</b><span>{total_confirmed:,}</span></div>
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

components.html(render_warning_map(map_data, latest_date), height=840, scrolling=False)

st.subheader("Where is increasing now?")
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
            "division": "Division",
            "new_total_24h": "24h suspected + confirmed",
            "suspected_24h": "24h suspected",
            "confirmed_24h": "24h confirmed",
            "new_deaths_24h": "24h deaths",
            "admitted_24h": "24h admitted",
            "discharged_24h": "24h discharged",
            "net_admitted_24h": "24h net admitted",
        }
    )
    .sort_values(["24h suspected + confirmed", "24h confirmed"], ascending=False)
)
st.dataframe(ranking, use_container_width=True, hide_index=True)

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
            return "no previous baseline"
        change = ((current - baseline_value) / baseline_value) * 100
        direction = "higher" if change >= 0 else "lower"
        return f"{abs(change):.0f}% {direction}"

    st.subheader("7-day rise signals")
    for _, row in alerts.iterrows():
        cases_today = int(row["new_total_24h"] or 0)
        cases_avg = float(row["new_total_24h_avg7"] or 0)
        deaths_today = int(row["new_deaths_24h"] or 0)
        deaths_avg = float(row["new_deaths_24h_avg7"] or 0)
        yesterday_cases = row.get("new_total_24h_yesterday")
        yesterday_deaths = row.get("new_deaths_24h_yesterday")
        status = "Increasing" if cases_today > cases_avg else "Stable or lower"

        death_sentence = "No deaths reported in the last 24 hours"
        if deaths_today:
            death_sentence = f"Deaths are **{deaths_today:,}**, {pct_change(deaths_today, deaths_avg)} than the 7-day average"
            if not pd.isna(yesterday_deaths):
                death_sentence += f" and {pct_change(deaths_today, yesterday_deaths)} than yesterday"

        st.write(
            f"**{row['division']}** — {status}: last-24-hours suspected + confirmed reports are **{cases_today:,}**, "
            f"{pct_change(cases_today, cases_avg)} than the 7-day average"
            f"{'' if pd.isna(yesterday_cases) else f' and {pct_change(cases_today, yesterday_cases)} than yesterday'}. "
            f"{death_sentence}."
        )

chart_tab, heatmap_tab = st.tabs(["Trends", "Heatmap"])

with chart_tab:
    metric_options = [
        "suspected_24h",
        "confirmed_24h",
        "admitted_24h",
        "discharged_24h",
        "suspected_deaths_24h",
        "confirmed_deaths_24h",
    ]
    control_col1, control_col2 = st.columns([1, 1])
    with control_col1:
        metric = st.selectbox(
            "Metric",
            metric_options,
            format_func=lambda x: x.replace("_", " ").title(),
        )

    latest_by_division = (
        filtered[filtered["report_date"] == filtered["report_date"].max()]
        .groupby("division", as_index=False)[metric]
        .sum()
        .sort_values(metric, ascending=False)
    )
    top_three = latest_by_division.head(3)["division"].tolist()
    top_five = latest_by_division.head(5)["division"].tolist()

    with control_col2:
        division_preset = st.selectbox("Division view", ["Top 3", "Top 5", "All", "Custom"])

    if division_preset == "Top 3":
        chart_divisions = top_three
    elif division_preset == "Top 5":
        chart_divisions = top_five
    elif division_preset == "All":
        chart_divisions = divisions
    else:
        chart_divisions = st.multiselect("Divisions", divisions, default=top_three or divisions[:3])

    chart_data = filtered[filtered["division"].isin(chart_divisions)].copy()
    if chart_data.empty:
        st.info("Choose at least one division to show the trend chart.")
    else:
        fig = px.line(chart_data.sort_values("report_date"), x="report_date", y=metric, color="division", markers=True)
        fig.update_xaxes(range=[str(start_date), str(end_date)])
        fig.update_layout(height=460, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

with heatmap_tab:
    heat_col1, heat_col2 = st.columns([1, 1])
    with heat_col1:
        heat_metric = st.selectbox(
            "Heatmap metric",
            ["suspected_24h", "confirmed_24h", "admitted_24h", "confirmed_total"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
    heat_latest = (
        filtered[filtered["report_date"] == filtered["report_date"].max()]
        .groupby("division", as_index=False)[heat_metric]
        .sum()
        .sort_values(heat_metric, ascending=False)
    )
    with heat_col2:
        heat_divisions = st.multiselect("Heatmap divisions", divisions, default=heat_latest.head(6)["division"].tolist())

    heat_data = filtered[filtered["division"].isin(heat_divisions)].copy()
    if heat_data.empty:
        st.info("Choose at least one division to show the heatmap.")
    else:
        heat = heat_data.pivot_table(index="division", columns=heat_data["report_date"].dt.date, values=heat_metric, aggfunc="sum").fillna(0)
        fig = px.imshow(heat, aspect="auto", color_continuous_scale="YlOrRd")
        fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
