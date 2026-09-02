"""Plotly chart builders shared by the Streamlit views."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


SENTIMENT_COLORS = {"Negativo": "#B42318", "Neutro": "#526174", "Positivo": "#15803D"}


def apply_plotly_theme(
    figure,
    *,
    height: int | None = 280,
    top_margin: int = 10,
    right_margin: int = 10,
    showlegend: bool = False,
):
    """Apply the shared analytics theme without changing chart data."""
    figure.update_layout(
        showlegend=showlegend,
        height=height,
        margin=dict(l=0, r=right_margin, t=top_margin, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#172033", family="Arial, sans-serif"),
        colorway=["#4F46E5", "#15803D", "#B42318", "#526174"],
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E2E8F0", font_color="#172033"),
    )
    figure.update_xaxes(gridcolor="#E2E8F0", zeroline=False, linecolor="#E2E8F0")
    figure.update_yaxes(gridcolor="#E2E8F0", zeroline=False, linecolor="#E2E8F0")
    return figure


def render_probability_chart(
    probabilities: dict[str, float],
    *,
    probability_label: str = "Probabilidad",
) -> None:
    """Render the local model probability distribution."""
    chart_data = pd.DataFrame(
        {"sentiment": list(probabilities), "probability": list(probabilities.values())}
    )
    figure = px.bar(
        chart_data,
        x="probability",
        y="sentiment",
        orientation="h",
        color="sentiment",
        color_discrete_map=SENTIMENT_COLORS,
        text=chart_data["probability"].map(lambda value: f"{value:.1%}"),
        labels={"probability": probability_label, "sentiment": ""},
    )
    apply_plotly_theme(figure)
    figure.update_xaxes(tickformat=".0%", range=[0, 1])
    st.plotly_chart(figure, use_container_width=True)
