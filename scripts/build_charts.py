import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

IN = Path("data/processed")
OUT = Path("site/charts")
OUT.mkdir(parents=True, exist_ok=True)

# THEME
BG = "#0d0d0d"
PAPER  = "#111111"
TEXT = "#cccccc"
GRID = "#1e1e1e"
RED = "#c0392b"
AMBER = "#e8a838"
BLUE = "#4a7c9e"
GREEN = "#4a9e6b"

COUNTRY_COLORS = {
    "Germany": "#7f8c8d",
    "Russia": "#8e44ad",
    "Chile": "#16a085",
    "China": "#d35400",
    "Hungary": RED,
    "United States of America": AMBER,
}

ADMIN_COLORS = {
    "Obama": BLUE,
    "Trump 1st": "#9e4a4a",
    "Biden": GREEN,
    "Trump 2nd": RED,
}

LAYOUT = dict(
    paper_bgcolor=PAPER,
    plot_bgcolor=BG,
    font=dict(color=TEXT, family="'Courier New', monospace", size=12),
    title_font=dict(size=14, color="#999999"),
    margin=dict(t=50, b=50, l=60, r=30),
    hoverlabel=dict(bgcolor="#1a1a1a", font_color=TEXT, font_family="'Courier New', monospace"),
)


def save(fig, name):
    fig.write_json(OUT / f"{name}.json")
    fig.write_html(OUT / f"{name}.html", include_plotlyjs="cdn")
    print(f"  {name}")


# GLOBAL ACADEMIC FREEDOM CHOROPLETH (ANIMATED 1990–2025) 
df = pd.read_csv(IN / "vdem_global_animated.csv")
df = df.sort_values("year")

fig = px.choropleth(
    df,
    locations="country_text_id",
    color="v2xca_academ",
    hover_name="country_name",
    animation_frame="year",
    hover_data={
        "v2xca_academ": ":.2f",
        "v2x_libdem": ":.2f",
        "regime_label": True,
        "country_text_id": False,
        "year": False,
    },
    color_continuous_scale=[[0, "#3d0000"], [0.4, "#8b1a1a"], [1, BLUE]],
    range_color=[0, 1],
    labels={
        "v2xca_academ": "Academic Freedom",
        "v2x_libdem": "Liberal Democracy",
        "regime_label": "Regime",
    },
)

fig.update_layout(
    **LAYOUT,
    # Map fills the top 70% of the paper; bottom 30% holds the horizontal
    # colorbar + animation controls. Full width (no column carved out for bar).
    geo=dict(
        domain=dict(x=[0, 1.0], y=[0.30, 1.0]),
        bgcolor=BG,
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#2a2a2a",
        showland=True,
        landcolor="#1a1a1a",
        showocean=True,
        oceancolor=BG,
        showlakes=False,
        showcountries=True,
        countrycolor="#2a2a2a",
        lataxis_range=[-60, 85],
    ),
    # Horizontal colorbar sits between the map and the animation controls
    coloraxis_colorbar=dict(
        orientation="h",
        title=dict(text="Academic Freedom", font=dict(color=TEXT, size=11), side="top"),
        tickcolor=TEXT,
        outlinecolor=GRID,
        tickfont=dict(color=TEXT, size=10),
        len=0.86,
        thickness=12,
        x=0.5,
        xanchor="center",
        y=0.26,
        yanchor="top",
    ),
)

# Blend leftover whitespace; minimal outer margins — geo domain handles spacing
fig.update_layout(paper_bgcolor=BG, margin=dict(t=5, b=5, l=10, r=10))

# Animation controls sit below the colorbar in the bottom 30% of the paper
fig.layout.sliders[0].update(
    currentvalue=dict(prefix="Year: ", font=dict(color=TEXT, size=13)),
    bgcolor="#1a1a1a",
    bordercolor=GRID,
    tickcolor=GRID,
    font=dict(color=TEXT),
    pad=dict(t=4, b=4),
    y=0.13,
    yanchor="top",
    len=0.74,
    x=0.13,
    xanchor="left",
)
fig.layout.updatemenus[0].update(
    bgcolor="#1a1a1a",
    bordercolor=GRID,
    font=dict(color=TEXT, size=12),
    x=0.02,
    y=0.13,
    yanchor="top",
    buttons=[
        dict(
            args=[None, {"frame": {"duration": 350, "redraw": True}, "fromcurrent": True,
                         "transition": {"duration": 200, "easing": "linear"}}],
            label="▶  Play",
            method="animate",
        ),
        dict(
            args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
            label="◼  Pause",
            method="animate",
        ),
    ],
)

save(fig, "chart_01_global_choropleth")


