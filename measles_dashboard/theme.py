"""Apple Intelligence–inspired design tokens for the public dashboard."""

from __future__ import annotations

FONT_STACK = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'

COLORS = {
    "bg": "#000000",
    "surface": "#1d1d1f",
    "surface_elevated": "#2c2c2e",
    "text": "#f5f5f7",
    "muted": "#86868b",
    "muted_dark": "#6e6e73",
    "link": "#2997ff",
    "glass": "rgba(255, 255, 255, 0.06)",
    "glass_border": "rgba(255, 255, 255, 0.11)",
    "grid": "rgba(255, 255, 255, 0.08)",
    "gradient": "linear-gradient(135deg, #5e5ce6 0%, #bf5af2 28%, #ff375f 52%, #ff9f0a 78%, #30d158 100%)",
    "gradient_text": "linear-gradient(90deg, #5e5ce6, #bf5af2, #ff375f, #ff9f0a)",
}

RISK = {
    "High alert": {"color": "#ff453a", "soft": "rgba(255, 69, 58, 0.18)", "glow": "rgba(255, 69, 58, 0.35)", "rank": 3},
    "Watch closely": {"color": "#ffd60a", "soft": "rgba(255, 214, 10, 0.14)", "glow": "rgba(255, 214, 10, 0.25)", "rank": 2},
    "Lower signal": {"color": "#30d158", "soft": "rgba(48, 209, 88, 0.14)", "glow": "rgba(48, 209, 88, 0.22)", "rank": 1},
}

CHART_DIVISION_COLORS = [
    "#64d2ff",
    "#bf5af2",
    "#ff9f0a",
    "#30d158",
    "#ff375f",
    "#ffd60a",
    "#5e5ce6",
    "#ac8e68",
]

NATIONAL_LINE = "#2997ff"

RADIUS = {
    "sm": "12px",
    "md": "16px",
    "lg": "20px",
    "xl": "24px",
    "pill": "999px",
}


def iframe_shell_css(*, hide_scroll: bool = True) -> str:
    """Shared layout tokens and chip styles for components.html iframes."""
    overflow = "hidden" if hide_scroll else "auto"
    return f"""
        :root {{
            --text: {COLORS["text"]};
            --muted: {COLORS["muted"]};
            --glass: {COLORS["glass"]};
            --glass-border: {COLORS["glass_border"]};
            --surface: {COLORS["surface"]};
            --radius-sm: {RADIUS["sm"]};
            --radius-md: {RADIUS["md"]};
            --radius-lg: {RADIUS["lg"]};
            --radius-xl: {RADIUS["xl"]};
            --radius-pill: {RADIUS["pill"]};
        }}
        html, body {{
            margin: 0;
            padding: 0;
            overflow: {overflow};
            font-family: {FONT_STACK};
            color: var(--text);
            background: transparent;
        }}
        .chip {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            min-height: 32px;
            padding: 6px 14px;
            border-radius: var(--radius-pill);
            border: 1px solid var(--glass-border);
            background: var(--glass);
            backdrop-filter: blur(16px);
            font-size: 0.76rem;
            font-weight: 600;
            color: var(--muted);
            white-space: nowrap;
        }}
        .chip b, .chip strong {{
            color: var(--text);
            font-weight: 700;
        }}
        .chip-dot {{
            width: 8px;
            height: 8px;
            border-radius: var(--radius-pill);
            flex-shrink: 0;
        }}
        .chip-accent {{
            color: var(--accent, var(--text));
            border-color: var(--accent, var(--glass-border));
            background: var(--soft, var(--glass));
        }}
        .chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .chip-row-scroll {{
            display: flex;
            flex-wrap: nowrap;
            gap: 8px;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }}
        .chip-row-scroll::-webkit-scrollbar {{
            display: none;
        }}
        .surface {{
            box-sizing: border-box;
            border-radius: var(--radius-xl);
            border: 1px solid var(--glass-border);
            background: var(--glass);
            backdrop-filter: blur(20px);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }}
    """


def plotly_base_layout(*, height: int = 420) -> dict:
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        autosize=True,
        font=dict(family=FONT_STACK, color=COLORS["text"], size=12),
        margin=dict(l=12, r=12, t=40, b=48),
        hoverlabel=dict(
            bgcolor=COLORS["surface_elevated"],
            bordercolor=COLORS["glass_border"],
            font=dict(family=FONT_STACK, color=COLORS["text"]),
        ),
    )


def style_axes(fig) -> None:
    axis = dict(
        gridcolor=COLORS["grid"],
        zerolinecolor=COLORS["grid"],
        linecolor=COLORS["grid"],
        tickfont=dict(color=COLORS["muted"], size=10),
        title_font=dict(color=COLORS["muted"]),
    )
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
