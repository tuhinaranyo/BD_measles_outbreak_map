from __future__ import annotations

import streamlit as st


def inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #14231d;
            --muted: #65736c;
            --line: #dfe8df;
            --paper: #fbfcf8;
            --panel: #ffffff;
            --green: #006a4e;
            --deep-green: #004332;
            --red: #d71920;
            --soft-red: #fff0ef;
            --gold: #c5922d;
            --blue: #2f6f8f;
            --sage: #eaf4ed;
        }

        [data-testid="stAppViewContainer"] {
            background:
                linear-gradient(180deg, rgba(0, 106, 78, .055), transparent 360px),
                linear-gradient(90deg, rgba(0, 106, 78, .045) 1px, transparent 1px),
                linear-gradient(rgba(215, 25, 32, .035) 1px, transparent 1px),
                var(--paper);
            background-size: 44px 44px;
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: rgba(251, 252, 248, .86);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(223, 232, 223, .9);
        }

        [data-testid="stSidebar"] {
            background: #f6faf6;
            border-right: 1px solid var(--line);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 2.1rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--ink);
        }

        h1 {
            font-size: 2.55rem !important;
            line-height: 1.05 !important;
            margin-bottom: .35rem !important;
        }

        h2, h3 {
            margin-top: 1.25rem !important;
        }

        .hero {
            position: relative;
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 26px 28px;
            margin-bottom: 22px;
            box-shadow: 0 18px 48px rgba(51, 39, 24, .08);
            overflow: hidden;
        }

        .hero:before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(135deg, rgba(242, 109, 79, .14), transparent 34%),
                linear-gradient(45deg, transparent 62%, rgba(26, 161, 121, .13));
            pointer-events: none;
        }

        .hero > * {
            position: relative;
        }

        .public-header {
            position: relative;
            min-height: 250px;
            display: flex;
            align-items: flex-end;
            padding: 34px 34px 30px;
            margin-bottom: 18px;
            border-radius: 18px;
            border: 1px solid var(--line);
            background:
                linear-gradient(90deg, rgba(0, 106, 78, .08) 1px, transparent 1px),
                linear-gradient(rgba(0, 106, 78, .06) 1px, transparent 1px),
                linear-gradient(135deg, #ffffff 0%, #f5fbf6 52%, #fff3f2 100%);
            background-size: 36px 36px, 36px 36px, auto;
            box-shadow: 0 22px 56px rgba(0, 67, 50, .10);
            overflow: hidden;
        }

        .public-header:before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 9px;
            background: linear-gradient(180deg, var(--green), var(--red));
        }

        .public-header:after {
            content: "";
            position: absolute;
            right: -80px;
            top: -90px;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            border: 38px solid rgba(215, 25, 32, .09);
            opacity: 1;
        }

        .public-header > div {
            max-width: 820px;
            position: relative;
            z-index: 1;
        }

        .public-kicker {
            display: inline-flex;
            color: var(--red);
            font-size: .82rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: .04em;
            margin-bottom: 12px;
        }

        .public-header h1 {
            max-width: 780px;
            font-size: 2.85rem !important;
            line-height: 1.02 !important;
            margin: 0 0 12px !important;
            font-weight: 900 !important;
        }

        .public-header p {
            color: var(--muted);
            max-width: 680px;
            font-size: 1.08rem;
            line-height: 1.55;
            margin: 0;
        }

        .care-note {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 12px;
            align-items: start;
            margin: 8px 0 18px;
            padding: 14px 16px;
            border: 1px solid rgba(215, 25, 32, .18);
            border-left: 5px solid var(--red);
            border-radius: 14px;
            background: linear-gradient(135deg, #ffffff, var(--soft-red));
            box-shadow: 0 12px 28px rgba(0, 67, 50, .06);
        }

        .care-note b {
            display: block;
            color: var(--deep-green);
            font-size: .94rem;
            margin-bottom: 3px;
        }

        .care-note span {
            color: #5f2f31;
            line-height: 1.5;
            font-size: .92rem;
        }

        .care-mark {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: var(--red);
            color: #fff;
            font-weight: 900;
        }

        .map-note {
            margin: -4px 0 10px;
            max-width: 860px;
            color: #51645a;
            font-size: .92rem;
            line-height: 1.5;
        }

        .bd-map-panel {
            display: grid;
            grid-template-columns: minmax(0, .86fr) minmax(320px, 1.1fr);
            gap: 18px;
            align-items: center;
            margin: 6px 0 26px;
            padding: 20px;
            border: 1px solid rgba(0, 106, 78, .18);
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(255,255,255,.96), rgba(237,247,240,.92)),
                linear-gradient(90deg, rgba(0,106,78,.06) 1px, transparent 1px);
            box-shadow: 0 18px 44px rgba(0, 67, 50, .09);
        }

        .bd-map-copy h2 {
            margin: 4px 0 8px !important;
            font-size: 1.65rem !important;
            line-height: 1.12 !important;
        }

        .bd-map-copy p {
            color: var(--muted);
            line-height: 1.55;
            margin: 0 0 12px;
            font-size: .96rem;
        }

        .bd-map-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .bd-map-legend span,
        .bd-map-card {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            min-height: 30px;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(0, 67, 50, .12);
            background: rgba(255, 255, 255, .82);
            color: var(--ink);
            font-size: .78rem;
            font-weight: 800;
        }

        .bd-map-legend i,
        .bd-map-card span {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }

        .bd-map-legend .high { background: var(--red); }
        .bd-map-legend .watch { background: var(--gold); }
        .bd-map-legend .lower { background: var(--green); }

        .bd-map-wrap {
            justify-self: center;
            width: min(100%, 470px);
            padding: 10px;
            border-radius: 22px;
            background: linear-gradient(180deg, #ffffff, #f2faf4);
            border: 1px solid rgba(0, 106, 78, .12);
        }

        .bd-map-svg {
            width: 100%;
            height: auto;
            display: block;
            overflow: visible;
        }

        .bd-region {
            stroke-width: 3.2;
            stroke-linejoin: round;
            filter: drop-shadow(0 6px 10px rgba(0, 67, 50, .10));
        }

        .bd-label text {
            text-anchor: middle;
            pointer-events: none;
        }

        .bd-alert-symbol {
            fill: #ffffff;
            font-size: 17px;
            font-weight: 900;
        }

        .bd-name {
            fill: #16372d;
            font-size: 18px;
            font-weight: 900;
        }

        .bd-count {
            fill: #5f2f31;
            font-size: 19px;
            font-weight: 900;
        }

        .bd-map-cards {
            grid-column: 1 / -1;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .bd-map-card b {
            font-size: .8rem;
        }

        .bd-map-card small {
            color: var(--muted);
            font-size: .74rem;
            font-weight: 750;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--green);
            font-weight: 800;
            font-size: .82rem;
            text-transform: uppercase;
            letter-spacing: .04em;
            margin-bottom: 10px;
        }

        .hero-title {
            max-width: 820px;
            font-size: 2.9rem;
            line-height: 1.02;
            font-weight: 850;
            color: var(--ink);
            margin-bottom: 10px;
        }

        .hero-copy {
            max-width: 760px;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.55;
        }

        .hero-actions {
            margin-top: 18px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            min-height: 34px;
            padding: 7px 12px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: #fffaf0;
            color: var(--ink);
            font-weight: 700;
            text-decoration: none !important;
        }

        .pill.primary {
            background: var(--ink);
            color: #fff !important;
            border-color: var(--ink);
        }

        [data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 18px 18px 16px;
            box-shadow: 0 12px 32px rgba(51, 39, 24, .07);
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted);
            font-weight: 750;
        }

        [data-testid="stMetricValue"] {
            color: var(--ink);
            font-weight: 850;
        }

        div[data-testid="stDataFrame"], div[data-testid="stTable"] {
            border: 1px solid var(--line);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 12px 32px rgba(51, 39, 24, .06);
        }

        [data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid var(--line);
            box-shadow: 0 10px 24px rgba(51, 39, 24, .05);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 0;
        }

        .stTabs [data-baseweb="tab"] {
            border: 1px solid var(--line);
            border-radius: 999px;
            background: #f7fbf7;
            color: var(--muted);
            padding: 8px 16px;
        }

        .stTabs [aria-selected="true"] {
            background: var(--deep-green) !important;
            color: #fff !important;
            border-color: var(--deep-green) !important;
        }

        div.stButton > button,
        div[data-testid="stDownloadButton"] > button,
        a[data-testid="stLinkButton"] {
            border-radius: 999px !important;
            border: 1px solid var(--deep-green) !important;
            background: var(--deep-green) !important;
            color: #fff !important;
            font-weight: 800 !important;
            box-shadow: 0 8px 20px rgba(0, 67, 50, .14);
        }

        [data-testid="stMarkdownContainer"] a {
            color: var(--blue);
            font-weight: 800;
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #fff;
            box-shadow: 0 10px 24px rgba(51, 39, 24, .05);
        }

        div.stButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        a[data-testid="stLinkButton"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 26px rgba(23, 20, 18, .16);
        }

        [data-testid="stSelectbox"],
        [data-testid="stMultiSelect"],
        [data-testid="stDateInput"],
        [data-testid="stNumberInput"] {
            background: rgba(255,255,255,.68);
            border-radius: 14px;
        }

        .status-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 6px 0 18px;
        }

        .status-card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 10px 28px rgba(51, 39, 24, .06);
        }

        .status-card b {
            display: block;
            font-size: .82rem;
            color: var(--muted);
            margin-bottom: 4px;
        }

        .status-card span {
            font-weight: 850;
            color: var(--ink);
        }

        .update-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: flex-end;
            margin: 18px 2px 18px;
            color: #6c7d73;
            font-size: .78rem;
            font-weight: 700;
        }

        .update-strip span {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 5px 9px;
            border-radius: 999px;
            background: rgba(234, 244, 237, .92);
            border: 1px solid rgba(0, 106, 78, .15);
        }

        .update-strip b {
            color: var(--green);
            font-weight: 850;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 16px 0 24px;
        }

        .metric-tile {
            min-height: 112px;
            border-radius: 14px;
            padding: 16px;
            border: 1px solid var(--line);
            background: #fff;
            box-shadow: 0 14px 34px rgba(0, 67, 50, .07);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .metric-tile b {
            color: var(--muted);
            font-size: .88rem;
            line-height: 1.25;
        }

        .metric-tile span {
            color: var(--ink);
            font-size: 2rem;
            line-height: 1;
            font-weight: 900;
        }

        .metric-tile.green { background: linear-gradient(135deg, #ffffff, rgba(0, 106, 78, .13)); border-top: 4px solid var(--green); }
        .metric-tile.blue { background: linear-gradient(135deg, #ffffff, rgba(47, 111, 143, .12)); border-top: 4px solid var(--blue); }
        .metric-tile.coral { background: linear-gradient(135deg, #ffffff, rgba(215, 25, 32, .13)); border-top: 4px solid var(--red); }
        .metric-tile.violet { background: linear-gradient(135deg, #ffffff, rgba(197, 146, 45, .13)); border-top: 4px solid var(--gold); }

        .stale-data-banner {
            margin: 6px 0 18px;
            padding: 12px 14px;
            border: 1px solid rgba(215, 25, 32, .35);
            border-left: 5px solid var(--red);
            border-radius: 14px;
            background: linear-gradient(135deg, #fff7f6, #fff);
            color: #5f2f31;
            font-size: .92rem;
            line-height: 1.45;
        }

        .stale-data-banner b { color: var(--red); }

        .page-footer {
            margin-top: 2.5rem;
            padding-top: 1rem;
            border-top: 1px solid var(--line);
            color: var(--muted);
            font-size: .82rem;
            line-height: 1.5;
        }

        /* Plotly charts: let Streamlit's container handle width.
           On phones, cap the height so the chart and its (horizontal)
           legend both fit on the first screen. */
        [data-testid="stPlotlyChart"] {
            width: 100% !important;
        }
        [data-testid="stPlotlyChart"] > div,
        .js-plotly-plot,
        .plot-container {
            width: 100% !important;
        }

        @media (max-width: 760px) {
            .hero-title { font-size: 2rem; }
            .public-header { min-height: 220px; padding: 24px; }
            .public-header:after { opacity: .25; right: -30px; }
            .public-header h1 { font-size: 2.1rem !important; }
            .status-strip { grid-template-columns: 1fr; }
            .update-strip {
                justify-content: flex-start;
                gap: 6px;
                font-size: .72rem;
                margin-top: 16px;
            }
            .update-strip span {
                padding: 4px 8px;
            }
            .metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
            }
            .metric-tile {
                min-height: 104px;
                padding: 14px;
                border-radius: 16px;
            }
            .metric-tile span {
                font-size: 1.72rem;
            }
            .metric-tile b {
                font-size: .8rem;
            }
            .bd-map-panel {
                grid-template-columns: 1fr;
                padding: 14px;
                gap: 12px;
                border-radius: 16px;
            }
            .bd-map-copy h2 {
                font-size: 1.35rem !important;
            }
            .bd-map-wrap {
                width: min(100%, 360px);
                padding: 6px;
            }
            .bd-name {
                font-size: 16px;
            }
            .bd-count {
                font-size: 17px;
            }
            .bd-map-cards {
                max-height: 132px;
                overflow: auto;
                padding-bottom: 2px;
            }
            /* Compact charts on phones — legend sits below the plot area. */
            [data-testid="stPlotlyChart"] {
                min-height: 360px;
            }
            [data-testid="stPlotlyChart"] .js-plotly-plot,
            [data-testid="stPlotlyChart"] .plot-container {
                min-height: 360px;
            }
            /* Stack chart controls vertically on narrow screens. */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            [data-testid="column"] {
                min-width: min(100%, 280px) !important;
                flex: 1 1 100% !important;
            }
            div.stDownloadButton > button,
            a[data-testid="stLinkButton"] {
                width: 100% !important;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 6px 12px;
                font-size: .85rem;
            }
            /* Make data tables horizontally scrollable instead of squished. */
            div[data-testid="stDataFrame"] > div {
                overflow-x: auto !important;
            }
            /* Tighten dashboard headings on small screens. */
            h2 { font-size: 1.35rem !important; }
            h3 { font-size: 1.15rem !important; }
            .block-container {
                padding-left: .6rem;
                padding-right: .6rem;
                padding-top: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, copy: str, eyebrow: str, actions: str = "") -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div class="eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-copy">{copy}</div>
            {actions}
        </section>
        """,
        unsafe_allow_html=True,
    )
