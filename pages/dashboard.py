from __future__ import annotations

import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from measles_dashboard.config import DB_PATH
from measles_dashboard.db import init_db
from measles_dashboard.ui import inject_style


st.set_page_config(page_title="DGHS Measles Dashboard", layout="wide")
inject_style()


DIVISION_POINTS = {
    "\u09a2\u09be\u0995\u09be": {"name": "Dhaka", "lat": 23.8103, "lon": 90.4125},
    "\u09b0\u09be\u099c\u09b6\u09be\u09b9\u09c0": {"name": "Rajshahi", "lat": 24.3745, "lon": 88.6042},
    "\u099a\u099f\u09cd\u099f\u0997\u09cd\u09b0\u09be\u09ae": {"name": "Chattogram", "lat": 22.3569, "lon": 91.7832},
    "\u09ac\u09b0\u09bf\u09b6\u09be\u09b2": {"name": "Barishal", "lat": 22.7010, "lon": 90.3535},
    "\u09b8\u09bf\u09b2\u09c7\u099f": {"name": "Sylhet", "lat": 24.8949, "lon": 91.8687},
    "\u09ae\u09df\u09ae\u09a8\u09b8\u09bf\u0982\u09b9": {"name": "Mymensingh", "lat": 24.7471, "lon": 90.4203},
    "\u0996\u09c1\u09b2\u09a8\u09be": {"name": "Khulna", "lat": 22.8456, "lon": 89.5403},
    "\u09b0\u0982\u09aa\u09c1\u09b0": {"name": "Rangpur", "lat": 25.7439, "lon": 89.2752},
}

RISK_STYLE = {
    "High alert": {"color": "#d71920", "rank": 3},
    "Watch closely": {"color": "#c5922d", "rank": 2},
    "Lower signal": {"color": "#006a4e", "rank": 1},
}


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
map_data["lat"] = map_data["division"].map(lambda value: DIVISION_POINTS.get(value, {}).get("lat"))
map_data["lon"] = map_data["division"].map(lambda value: DIVISION_POINTS.get(value, {}).get("lon"))
map_data["division_label"] = map_data["division"].map(lambda value: DIVISION_POINTS.get(value, {}).get("name", value))
map_data["marker_size"] = 18 + (map_data["total_24h"] / max_total_24h) * 34
map_data = map_data.dropna(subset=["lat", "lon"])

st.subheader("Bangladesh warning map")
st.markdown(
    """
    <div class="map-note">
        Red markers mean deaths were reported or the 24-hour suspected + confirmed count is very high. Gold means the division needs close watching. Green means the latest signal is lower, but still worth attention.
    </div>
    """,
    unsafe_allow_html=True,
)

map_fig = go.Figure()
for status_name, style in RISK_STYLE.items():
    status_rows = map_data[map_data["status"] == status_name]
    if status_rows.empty:
        continue
    map_fig.add_trace(
        go.Scattergeo(
            lat=status_rows["lat"],
            lon=status_rows["lon"],
            mode="markers+text",
            name=status_name,
            text=["!" if status_name != "Lower signal" else "" for _ in range(len(status_rows))],
            textfont=dict(color="#ffffff", size=16, family="Arial Black"),
            marker=dict(
                size=status_rows["marker_size"],
                color=style["color"],
                opacity=0.9,
                line=dict(color="#ffffff", width=2),
            ),
            customdata=status_rows[
                ["division_label", "total_24h", "suspected_24h", "confirmed_24h", "deaths_24h", "avg_total_7d"]
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Status: " + status_name + "<br>"
                "24h suspected + confirmed: %{customdata[1]:,}<br>"
                "24h suspected: %{customdata[2]:,}<br>"
                "24h confirmed: %{customdata[3]:,}<br>"
                "24h deaths: %{customdata[4]:,}<br>"
                "7-day average: %{customdata[5]:.1f}"
                "<extra></extra>"
            ),
        )
    )

map_fig.update_geos(
    projection_type="mercator",
    lonaxis_range=[88.0, 92.8],
    lataxis_range=[20.5, 26.8],
    showland=True,
    landcolor="#eef7ef",
    showocean=True,
    oceancolor="#f6fbff",
    showcountries=True,
    countrycolor="#7fa28e",
    showsubunits=True,
    subunitcolor="#c9d8cd",
    showlakes=False,
    bgcolor="rgba(0,0,0,0)",
)
map_fig.update_layout(
    height=560,
    margin=dict(l=0, r=0, t=4, b=0),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.01,
        xanchor="left",
        x=0,
        bgcolor="rgba(255,255,255,.82)",
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(map_fig, use_container_width=True)

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
