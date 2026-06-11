from __future__ import annotations

import streamlit as st

from .theme import COLORS, FONT_STACK


def inject_style() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --bg: {COLORS["bg"]};
            --surface: {COLORS["surface"]};
            --surface-2: {COLORS["surface_elevated"]};
            --text: {COLORS["text"]};
            --muted: {COLORS["muted"]};
            --link: {COLORS["link"]};
            --glass: {COLORS["glass"]};
            --glass-border: {COLORS["glass_border"]};
            --radius-lg: 22px;
            --radius-xl: 28px;
        }}

        html, body, [class*="css"] {{
            font-family: {FONT_STACK};
        }}

        [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(ellipse 80% 50% at 50% -10%, rgba(94, 92, 230, 0.22), transparent 55%),
                radial-gradient(ellipse 60% 40% at 100% 20%, rgba(191, 90, 242, 0.12), transparent 50%),
                radial-gradient(ellipse 50% 30% at 0% 80%, rgba(48, 209, 88, 0.08), transparent 45%),
                var(--bg);
            color: var(--text);
        }}

        [data-testid="stHeader"] {{
            background: rgba(0, 0, 0, 0.72);
            backdrop-filter: saturate(180%) blur(20px);
            border-bottom: 1px solid var(--glass-border);
        }}

        [data-testid="stSidebar"] {{
            background: var(--surface);
            border-right: 1px solid var(--glass-border);
        }}

        .block-container {{
            max-width: 1080px;
            padding-top: 1.5rem;
            padding-bottom: 5rem;
        }}

        h1, h2, h3, h4 {{
            color: var(--text) !important;
            letter-spacing: -0.02em;
            font-weight: 700 !important;
        }}

        h1 {{
            font-size: clamp(2.2rem, 7vw, 3.4rem) !important;
            line-height: 1.05 !important;
            letter-spacing: -0.03em !important;
        }}

        h2 {{
            font-size: clamp(1.35rem, 4vw, 1.75rem) !important;
            margin-top: 2rem !important;
            margin-bottom: 0.75rem !important;
        }}

        p, li, label, .stCaption {{
            color: var(--muted);
        }}

        .gradient-text {{
            background: linear-gradient(90deg, #5e5ce6, #bf5af2, #ff375f, #ff9f0a);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent;
        }}

        .apple-hero {{
            text-align: center;
            padding: clamp(2rem, 8vw, 4.5rem) clamp(1rem, 4vw, 2rem) clamp(2rem, 6vw, 3rem);
            margin: 0 0 1.5rem;
        }}

        .apple-hero .hero-eyebrow {{
            display: inline-block;
            margin: 0 0 1rem;
            padding: 6px 14px;
            border-radius: 999px;
            border: 1px solid var(--glass-border);
            background: var(--glass);
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .apple-hero .hero-lead {{
            max-width: 640px;
            margin: 1rem auto 0;
            font-size: clamp(1rem, 2.8vw, 1.2rem);
            line-height: 1.55;
            color: var(--muted);
        }}

        .apple-hero .hero-lead b {{
            color: var(--text);
            font-weight: 600;
        }}

        .section-head {{
            margin: 2.25rem 0 1rem;
            padding: 0 0.25rem;
        }}

        .section-head h2 {{
            margin: 0 !important;
            font-size: clamp(1.4rem, 4vw, 1.85rem) !important;
            font-weight: 700 !important;
        }}

        .section-head p {{
            margin: 0.45rem 0 0;
            font-size: 0.95rem;
            line-height: 1.5;
            color: var(--muted);
        }}

        .glass-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin: 0 0 1.25rem;
        }}

        .glass-strip span {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            border-radius: 999px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            backdrop-filter: blur(16px);
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--muted);
        }}

        .glass-strip b {{
            color: var(--text);
            font-weight: 700;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 0 0 1.75rem;
        }}

        .metric-tile {{
            border-radius: var(--radius-lg);
            padding: 18px 16px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            backdrop-filter: blur(20px);
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 108px;
        }}

        .metric-tile b {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--muted);
            line-height: 1.3;
        }}

        .metric-tile span {{
            font-size: clamp(1.65rem, 5vw, 2.15rem);
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.03em;
            color: var(--text);
        }}

        .metric-tile.green {{ box-shadow: inset 0 1px 0 rgba(48, 209, 88, 0.35); }}
        .metric-tile.blue {{ box-shadow: inset 0 1px 0 rgba(41, 151, 255, 0.35); }}
        .metric-tile.coral {{ box-shadow: inset 0 1px 0 rgba(255, 69, 58, 0.35); }}
        .metric-tile.violet {{ box-shadow: inset 0 1px 0 rgba(191, 90, 242, 0.35); }}

        .stale-data-banner {{
            margin: 0 0 1rem;
            padding: 14px 16px;
            border-radius: var(--radius-lg);
            background: rgba(255, 69, 58, 0.1);
            border: 1px solid rgba(255, 69, 58, 0.35);
            color: #ffb4ad;
            font-size: 0.92rem;
            line-height: 1.45;
        }}

        .stale-data-banner b {{ color: #ff6961; }}

        .page-footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--glass-border);
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.6;
            text-align: center;
        }}

        .page-footer a {{
            color: var(--link) !important;
            text-decoration: none;
        }}

        [data-testid="stPlotlyChart"] {{
            width: 100% !important;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-xl);
            padding: 8px 4px 4px;
            backdrop-filter: blur(12px);
            overflow: hidden;
        }}

        [data-testid="stPlotlyChart"] > div,
        .js-plotly-plot,
        .plot-container {{
            width: 100% !important;
        }}

        div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-lg);
            overflow: hidden;
            background: var(--glass);
        }}

        [data-testid="stAlert"] {{
            border-radius: var(--radius-lg);
            border: 1px solid var(--glass-border);
            background: var(--glass);
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-lg);
            background: var(--glass);
            backdrop-filter: blur(12px);
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 6px;
            background: transparent;
            border-bottom: none;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 999px;
            border: 1px solid var(--glass-border);
            background: var(--glass);
            color: var(--muted);
            padding: 8px 18px;
            font-weight: 600;
        }}

        .stTabs [aria-selected="true"] {{
            background: var(--text) !important;
            color: var(--bg) !important;
            border-color: var(--text) !important;
        }}

        div.stButton > button,
        div[data-testid="stDownloadButton"] > button,
        a[data-testid="stLinkButton"] {{
            border-radius: 999px !important;
            border: 1px solid var(--glass-border) !important;
            background: var(--glass) !important;
            color: var(--link) !important;
            font-weight: 600 !important;
            backdrop-filter: blur(12px);
            transition: background 0.2s ease, transform 0.2s ease;
        }}

        div.stButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        a[data-testid="stLinkButton"]:hover {{
            background: rgba(41, 151, 255, 0.15) !important;
            transform: scale(1.01);
        }}

        [data-testid="stSelectbox"] label,
        [data-testid="stMultiSelect"] label {{
            color: var(--muted) !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
        }}

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
            background: var(--glass) !important;
            border-color: var(--glass-border) !important;
            border-radius: 14px !important;
            color: var(--text) !important;
        }}

        [data-testid="stMarkdownContainer"] a {{
            color: var(--link);
        }}

        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        @media (max-width: 760px) {{
            .metric-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
            }}
            .metric-tile {{
                min-height: 96px;
                padding: 14px 12px;
            }}
            .glass-strip {{
                justify-content: flex-start;
            }}
            [data-testid="stHorizontalBlock"] {{
                flex-wrap: wrap !important;
            }}
            [data-testid="column"] {{
                min-width: min(100%, 280px) !important;
                flex: 1 1 100% !important;
            }}
            div.stDownloadButton > button,
            a[data-testid="stLinkButton"] {{
                width: 100% !important;
            }}
            div[data-testid="stDataFrame"] > div {{
                overflow-x: auto !important;
            }}
            .block-container {{
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str = "") -> None:
    sub = f'<p>{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="section-head"><h2>{title}</h2>{sub}</div>',
        unsafe_allow_html=True,
    )


def hero(title: str, copy: str, eyebrow: str, actions: str = "") -> None:
    st.markdown(
        f"""
        <section class="apple-hero">
            <p class="hero-eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            <p class="hero-lead">{copy}</p>
            {actions}
        </section>
        """,
        unsafe_allow_html=True,
    )
