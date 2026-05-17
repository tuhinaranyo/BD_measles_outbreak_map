from __future__ import annotations

import streamlit as st


def inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #171412;
            --muted: #6e665f;
            --line: #e9e1d6;
            --paper: #fffdf8;
            --panel: #ffffff;
            --green: #1aa179;
            --coral: #f26d4f;
            --yellow: #f5bd3d;
            --blue: #4d73ff;
            --violet: #9b7cff;
        }

        [data-testid="stAppViewContainer"] {
            background:
                linear-gradient(90deg, rgba(242, 109, 79, .08) 1px, transparent 1px),
                linear-gradient(rgba(77, 115, 255, .06) 1px, transparent 1px),
                var(--paper);
            background-size: 44px 44px;
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: rgba(255, 253, 248, .78);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(233, 225, 214, .75);
        }

        [data-testid="stSidebar"] {
            background: #fff9ef;
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
            min-height: 230px;
            display: flex;
            align-items: flex-end;
            padding: 34px 34px 30px;
            margin-bottom: 18px;
            border-radius: 22px;
            border: 1px solid var(--line);
            background:
                radial-gradient(circle at 88% 18%, rgba(245, 189, 61, .34), transparent 22%),
                radial-gradient(circle at 8% 12%, rgba(26, 161, 121, .22), transparent 26%),
                linear-gradient(135deg, #fff 0%, #fff8ec 44%, #eef8f5 100%);
            box-shadow: 0 22px 60px rgba(51, 39, 24, .10);
            overflow: hidden;
        }

        .public-header:after {
            content: "";
            position: absolute;
            right: 34px;
            top: 34px;
            width: 210px;
            height: 150px;
            border: 2px solid rgba(23, 20, 18, .12);
            border-radius: 28px;
            transform: rotate(-7deg);
            background:
                linear-gradient(90deg, transparent 28px, rgba(23, 20, 18, .08) 29px, transparent 30px),
                linear-gradient(rgba(23, 20, 18, .08) 1px, transparent 1px);
            background-size: 42px 100%, 100% 34px;
            opacity: .8;
        }

        .public-header > div {
            max-width: 820px;
            position: relative;
            z-index: 1;
        }

        .public-kicker {
            display: inline-flex;
            color: var(--green);
            font-size: .82rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: .04em;
            margin-bottom: 12px;
        }

        .public-header h1 {
            max-width: 780px;
            font-size: 3rem !important;
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
            background: #fffaf0;
            color: var(--muted);
            padding: 8px 16px;
        }

        .stTabs [aria-selected="true"] {
            background: var(--ink) !important;
            color: #fff !important;
            border-color: var(--ink) !important;
        }

        div.stButton > button,
        div[data-testid="stDownloadButton"] > button,
        a[data-testid="stLinkButton"] {
            border-radius: 999px !important;
            border: 1px solid var(--ink) !important;
            background: var(--ink) !important;
            color: #fff !important;
            font-weight: 800 !important;
            box-shadow: 0 8px 20px rgba(23, 20, 18, .12);
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
            margin: -4px 2px 18px;
            color: #718078;
            font-size: .78rem;
            font-weight: 700;
        }

        .update-strip span {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 5px 9px;
            border-radius: 999px;
            background: rgba(238, 248, 245, .86);
            border: 1px solid rgba(26, 161, 121, .16);
        }

        .update-strip b {
            color: #2d6d61;
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
            border-radius: 18px;
            padding: 16px;
            border: 1px solid var(--line);
            background: #fff;
            box-shadow: 0 14px 34px rgba(51, 39, 24, .08);
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

        .metric-tile.green { background: linear-gradient(135deg, #ffffff, rgba(26, 161, 121, .14)); }
        .metric-tile.blue { background: linear-gradient(135deg, #ffffff, rgba(77, 115, 255, .13)); }
        .metric-tile.coral { background: linear-gradient(135deg, #ffffff, rgba(242, 109, 79, .14)); }
        .metric-tile.violet { background: linear-gradient(135deg, #ffffff, rgba(155, 124, 255, .14)); }

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
                margin-top: -2px;
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
