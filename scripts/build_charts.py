import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    "Russia": "#8e44ad",
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
fig.update_layout(paper_bgcolor=BG, margin=dict(t=25, b=30, l=10, r=10))

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

# 2. REGIME TIMELINE AREA CHART 
df = pd.read_csv(IN / "vdem_regime_timeline.csv")

REGIME_ORDER = ["Closed Autocracy", "Electoral Autocracy", "Electoral Democracy", "Liberal Democracy"]
REGIME_COLORS = {
    "Closed Autocracy":    "#c0392b",   # vivid red
    "Electoral Autocracy": "#c47a3a",   # terracotta / burnt orange
    "Electoral Democracy": "#6ab0d4",   # sky blue
    "Liberal Democracy":   "#2a5f9e",   # deep navy blue
}

fig = go.Figure()
for regime in REGIME_ORDER:
    sub = df[df["regime_label"] == regime].sort_values("year")
    fig.add_trace(go.Scatter(
        x=sub["year"],
        y=sub["share"],
        name=regime,
        mode="lines",
        stackgroup="one",
        fillcolor=REGIME_COLORS[regime],
        line=dict(width=0.5, color=REGIME_COLORS[regime]),
        hovertemplate="%{fullData.name}: %{y:.1%}<extra></extra>",
    ))

MILESTONES = [
    (1945, 0.97, "WW2 ends"),
    (2010, 0.97, "reversal begins"),
]

for x, y, label in MILESTONES:
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1,
                  line=dict(color="#555555", width=1, dash="dot"))

fig.update_layout(
    **LAYOUT,
    xaxis=dict(title="", gridcolor=GRID, showgrid=False, range=[1900, 2025]),
    yaxis=dict(title="Share of Countries", tickformat=".0%", gridcolor=GRID),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)",
                traceorder="normal"),
    hovermode="x unified",
    annotations=[
        dict(
            x=x, y=y, xref="x", yref="y",
            text=label, showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(color="#ffffff", size=10, family="'Courier New', monospace"),
        )
        for x, y, label in MILESTONES
    ],
)
fig.update_layout(margin=dict(t=50, b=75, l=60, r=30))
save(fig, "chart_02_regime_timeline")


# 2b. REGIME TYPE vs ACADEMIC FREEDOM SCATTER (animated 1990–2025)
scatter_df = pd.read_csv(IN / "vdem_global_animated.csv")
scatter_df = scatter_df.dropna(subset=["v2x_libdem", "v2xca_academ", "regime_label"])
scatter_df = scatter_df.sort_values("year")

fig = px.scatter(
    scatter_df,
    x="v2x_libdem",
    y="v2xca_academ",
    color="regime_label",
    animation_frame="year",
    hover_name="country_name",
    hover_data={"v2x_libdem": ":.2f", "v2xca_academ": ":.2f",
                "regime_label": True, "year": False},
    color_discrete_map=REGIME_COLORS,
    category_orders={"regime_label": [
        "Closed Autocracy", "Liberal Democracy",
        "Electoral Autocracy", "Electoral Democracy",
    ]},
    labels={"v2x_libdem": "Liberal Democracy Index (0–1)",
            "v2xca_academ": "Academic Freedom Index (0–1)",
            "regime_label": "Regime"},
    range_x=[-0.02, 1.02],
    range_y=[-0.02, 1.02],
)

fig.update_traces(marker=dict(size=7, opacity=0.85, line=dict(width=0.5, color="#111111")))

fig.update_layout(
    **LAYOUT,
    xaxis=dict(title="Liberal Democracy Index (0–1)", gridcolor=GRID),
    yaxis=dict(title="Academic Freedom Index (0–1)", gridcolor=GRID),
    legend=dict(title="", orientation="h", yanchor="bottom", y=1.02,
                bgcolor="rgba(0,0,0,0)", traceorder="normal",
                entrywidthmode="fraction", entrywidth=0.5),
    hovermode="closest",
)

fig.update_layout(margin=dict(t=50, b=130, l=60, r=30))

fig.layout.sliders[0].update(
    currentvalue=dict(prefix="Year: ", font=dict(color=TEXT, size=13)),
    bgcolor="#1a1a1a", bordercolor=GRID, tickcolor=GRID,
    font=dict(color=TEXT),
    pad=dict(t=4, b=4), y=-0.12, yanchor="top", len=0.74, x=0.13, xanchor="left",
)
fig.layout.updatemenus[0].update(
    bgcolor="#1a1a1a", bordercolor=GRID,
    font=dict(color=TEXT, size=12),
    x=0.02, y=-0.12, yanchor="top",
    buttons=[
        dict(args=[None, {"frame": {"duration": 350, "redraw": True}, "fromcurrent": True,
                          "transition": {"duration": 200, "easing": "linear"}}],
             label="▶  Play", method="animate"),
        dict(args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
             label="◼  Pause", method="animate"),
    ],
)

save(fig, "chart_02b_regime_af_scatter")


# 3. SIX CASE COUNTRIES LINE CHART 
df = pd.read_csv(IN / "vdem_cases.csv")

fig = go.Figure()
for country, color in COUNTRY_COLORS.items():
    sub = df[df["country_name"] == country].sort_values("year")
    fig.add_trace(go.Scatter(
        x=sub["year"],
        y=sub["v2xca_academ"],
        name=country,
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=4),
        customdata=sub[["v2x_libdem"]].values,
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Year: %{x}<br>"
            "Academic Freedom: %{y:.3f}<br>"
            "Liberal Democracy: %{customdata[0]:.3f}"
            "<extra></extra>"
        ),
    ))

fig.update_layout(
    **LAYOUT,
    xaxis=dict(title="", gridcolor=GRID, dtick=2),
    yaxis=dict(title="Academic Freedom Index (0–1)", gridcolor=GRID),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"),
    hovermode="x unified",
)
fig.update_layout(margin=dict(t=50, b=75, l=60, r=30))
save(fig, "chart_03_case_countries")


# 4. US BOOK BANS CHOROPLETH
df = pd.read_csv(IN / "bans_by_state.csv")
df = df[df["state_po"] != "DC"].copy()

fig = px.choropleth(
    df,
    locations="state_po",
    locationmode="USA-states",
    color="bans",
    scope="usa",
    hover_name="state_title",
    hover_data={
        "bans":      True,
        "gop_share": ":.1f",
        "state_po":  False,
    },
    color_continuous_scale=[[0, "#1a1a1a"], [0.3, "#5a1010"], [1, RED]],
    labels={"bans": "Book Bans", "gop_share": "GOP Vote Share (%)"},
)
fig.update_layout(
    **LAYOUT,
    geo=dict(bgcolor=BG, showlakes=False, lakecolor=BG),
    coloraxis_colorbar=dict(
        title=dict(text="Bans", font=dict(color=TEXT)),
        tickcolor=TEXT,
        outlinecolor=GRID,
        tickfont=dict(color=TEXT),
        len=0.6,
    ),
)
fig.update_layout(margin=dict(t=50, b=75, l=60, r=30))
save(fig, "chart_04_bans_choropleth")


# 5. MONTHLY BANS TIMELINE
df = pd.read_csv(IN / "bans_monthly.csv")
df["month_dt"] = pd.to_datetime(df["month"])

fig = go.Figure(go.Bar(
    x=df["month_dt"],
    y=df["count"],
    marker_color=RED,
    marker_line_width=0,
    hovertemplate="<b>%{x|%b %Y}</b>: %{y} bans<extra></extra>",
))
fig.update_layout(
    **LAYOUT,
    xaxis=dict(title="", gridcolor=GRID, tickformat="%b '%y", dtick="M1"),
    yaxis=dict(title="Number of Bans", gridcolor=GRID),
    bargap=0.2,
)
fig.update_layout(margin=dict(t=50, b=75, l=60, r=30))
save(fig, "chart_05_bans_timeline")


# 6. DOE QUARTERLY SPENDING
df = pd.read_csv(IN / "doe_spending_clean.csv")

bar_colors = [ADMIN_COLORS[a] for a in df["administration"]]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df["fiscal_quarter"],
    y=df["obligations_bn"],
    marker=dict(color=bar_colors, line=dict(width=0)),
    customdata=df["administration"].values,
    hovertemplate="<b>%{x}</b><br>$%{y:.2f}B<br>%{customdata}<extra></extra>",
    showlegend=False,
))
# Invisible traces for legend
for admin, color in ADMIN_COLORS.items():
    fig.add_trace(go.Bar(x=[None], y=[None], name=admin, marker_color=color, showlegend=True))

fig.update_layout(
    **LAYOUT,
    xaxis=dict(title="", tickangle=-45, gridcolor=GRID, showgrid=False),
    yaxis=dict(title="Obligations ($B)", gridcolor=GRID),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"),
    bargap=0.1,
    barmode="overlay",
)
fig.update_layout(margin=dict(t=50, b=75, l=60, r=30))
save(fig, "chart_08_doe_spending")


# 7. LITERACY RATE vs LIBERAL DEMOCRACY (animated 2000–2024) 
df = pd.read_csv(IN / "literacy_regime_animated.csv")
df = df.sort_values("year")

fig = px.scatter(
    df,
    x="v2x_libdem",
    y="literacy_rate",
    color="regime_label",
    animation_frame="year",
    hover_name="country_name",
    hover_data={"v2x_libdem": ":.2f", "literacy_rate": ":.1f",
                "regime_label": True, "year": False},
    color_discrete_map=REGIME_COLORS,
    category_orders={"regime_label": [
        "Closed Autocracy", "Liberal Democracy",
        "Electoral Autocracy", "Electoral Democracy",
    ]},
    labels={"v2x_libdem": "Liberal Democracy Index (0–1)",
            "literacy_rate": "Literacy Rate (% ages 15+)",
            "regime_label": "Regime"},
    range_x=[-0.02, 1.02],
    range_y=[15, 105],
)

fig.update_traces(marker=dict(size=7, opacity=0.85, line=dict(width=0.5, color="#111111")))

fig.update_layout(
    **LAYOUT,
    xaxis=dict(title="Liberal Democracy Index (0–1)", gridcolor=GRID),
    yaxis=dict(title="Literacy Rate (% ages 15+)", gridcolor=GRID),
    legend=dict(title="", orientation="h", yanchor="bottom", y=1.02,
                bgcolor="rgba(0,0,0,0)", traceorder="normal",
                entrywidthmode="fraction", entrywidth=0.5),
    hovermode="closest",
)
fig.update_layout(margin=dict(t=50, b=130, l=60, r=30))

fig.layout.sliders[0].update(
    currentvalue=dict(prefix="Year: ", font=dict(color=TEXT, size=13)),
    bgcolor="#1a1a1a", bordercolor=GRID, tickcolor=GRID,
    font=dict(color=TEXT),
    pad=dict(t=4, b=4), y=-0.12, yanchor="top", len=0.74, x=0.13, xanchor="left",
)
fig.layout.updatemenus[0].update(
    bgcolor="#1a1a1a", bordercolor=GRID,
    font=dict(color=TEXT, size=12),
    x=0.02, y=-0.12, yanchor="top",
    buttons=[
        dict(args=[None, {"frame": {"duration": 350, "redraw": True}, "fromcurrent": True,
                          "transition": {"duration": 200, "easing": "linear"}}],
             label="▶  Play", method="animate"),
        dict(args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
             label="◼  Pause", method="animate"),
    ],
)

save(fig, "chart_10_literacy")

print(f"\nAll 7 charts written to {OUT}/")



