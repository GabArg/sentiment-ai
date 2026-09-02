"""Plotly chart builders shared by the Streamlit views."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


SENTIMENT_COLORS = {"Negativo": "#D92D20", "Neutro": "#475467", "Positivo": "#078A61"}


def apply_plotly_theme(figure, *, height: int = 280, top_margin: int = 10):
    """Apply the current compact chart layout without changing its data."""
    figure.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=0, r=10, t=top_margin, b=0),
    )
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
