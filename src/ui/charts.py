"""Plotly chart builders shared by the Streamlit views."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


SENTIMENT_COLORS = {"Negativo": "#D55C47", "Neutro": "#AEB9BA", "Positivo": "#16856B"}


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
        font=dict(color="#10243E", family="Arial, sans-serif", size=12),
        colorway=["#16856B", "#D55C47", "#AEB9BA", "#4A7FA7"],
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#DFE5E5", font_color="#10243E"),
    )
    figure.update_xaxes(gridcolor="#E2E8F0", zeroline=False, linecolor="#E2E8F0")
    figure.update_yaxes(gridcolor="#E2E8F0", zeroline=False, linecolor="#E2E8F0")
    return figure


def render_sentiment_distribution_chart(distribution: pd.DataFrame, total: int) -> None:
    """Render an editorial donut using the existing distribution output."""
    figure = go.Figure(
        go.Pie(
            labels=distribution["sentiment"],
            values=distribution["count"],
            hole=0.68,
            sort=False,
            direction="clockwise",
            marker=dict(
                colors=[SENTIMENT_COLORS[label] for label in distribution["sentiment"]],
                line=dict(color="#FFFFFF", width=3),
            ),
            textinfo="percent",
            textposition="outside",
            textfont=dict(size=11, color="#50616C"),
            hovertemplate="%{label}<br>%{value:,} comentarios<br>%{percent}<extra></extra>",
        )
    )
    apply_plotly_theme(figure, height=300, top_margin=12, right_margin=20, showlegend=True)
    figure.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.13, xanchor="center", x=0.5),
        annotations=[
            dict(text=f"<b>{total:,}</b><br><span style='font-size:10px'>comentarios</span>", x=0.5, y=0.5, showarrow=False, font_size=18)
        ],
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    st.plotly_chart(figure, use_container_width=True)


def render_confidence_context_chart(results: pd.DataFrame) -> None:
    """Render mean local confidence by class as technical context."""
    order = ["Positivo", "Neutro", "Negativo"]
    confidence = results.groupby("sentiment")["confidence"].mean().reindex(order).dropna()
    figure = go.Figure(
        go.Bar(
            x=confidence.values,
            y=confidence.index,
            orientation="h",
            marker=dict(color=[SENTIMENT_COLORS[label] for label in confidence.index]),
            text=[f"{value:.1%}" for value in confidence.values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>Confianza local media: %{x:.1%}<extra></extra>",
        )
    )
    apply_plotly_theme(figure, height=250, top_margin=12, right_margin=42)
    figure.update_xaxes(range=[0, 1], tickformat=".0%", dtick=0.25, title=None)
    figure.update_yaxes(title=None, autorange="reversed")
    st.plotly_chart(figure, use_container_width=True)


def render_pareto_priority_chart(pareto: pd.DataFrame) -> None:
    """Render Pareto terms as readable horizontal priority bars."""
    chart = pareto.iloc[::-1]
    colors = ["#D55C47" if value else "#CBD4D4" for value in chart["within_80_percent"]]
    figure = go.Figure(
        go.Bar(
            x=chart["frequency"],
            y=chart["topic"],
            orientation="h",
            marker_color=colors,
            text=chart["frequency"].map(lambda value: f"{int(value):,}"),
            textposition="outside",
            cliponaxis=False,
            customdata=chart[["percentage", "cumulative_percentage", "within_80_percent"]],
            hovertemplate=(
                "<b>%{y}</b><br>Frecuencia: %{x:,}<br>Participación: %{customdata[0]:.1f}%"
                "<br>Acumulado: %{customdata[1]:.1f}%<extra></extra>"
            ),
        )
    )
    height = max(340, min(620, 58 + len(chart) * 29))
    apply_plotly_theme(figure, height=height, top_margin=12, right_margin=45)
    figure.update_xaxes(title="Menciones en comentarios negativos", rangemode="tozero", dtick=1)
    figure.update_yaxes(title=None, tickfont_size=11)
    figure.update_layout(bargap=0.32)
    st.plotly_chart(figure, use_container_width=True)


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
