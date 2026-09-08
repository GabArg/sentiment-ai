"""Reusable Streamlit presentation helpers for Sentiment AI."""

from .charts import (
    render_confidence_context_chart,
    render_probability_chart,
    render_pareto_priority_chart,
    render_sentiment_distribution_chart,
)
from .batch_view import (
    prepare_batch_display,
    preview_column_config,
    render_batch_file_summary,
    render_batch_stepper,
    selectable_text_columns,
)
from .dashboard import (
    build_dashboard_view_model,
    build_traceability_text,
    render_attention_panel,
    render_dashboard_kpis,
    render_dataset_reading,
    render_panel_heading,
)
from .components import (
    render_batch_csv_preview,
    render_batch_kpi_cards,
    render_batch_results_header,
    render_batch_summary_band,
    render_batch_upload_empty,
    render_product_header,
    render_result_card,
    render_sidebar_footer,
)
from .styles import load_global_styles
from .pareto_view import (
    build_pareto_view_model,
    render_pareto_detail_table,
    render_pareto_methodology,
    render_pareto_summary,
    render_priority_ranking,
)
from .individual import (
    render_individual_empty_state,
    render_individual_intro,
    render_individual_result_heading,
)
from .report_view import (
    parse_report_sections,
    render_ai_report_intro,
    render_deterministic_brief,
)
from .shell import (
    format_navigation_label,
    render_dataset_context,
    render_page_header,
    render_sidebar_brand,
    render_sidebar_signature,
    render_workspace_empty_state,
)

__all__ = [
    "load_global_styles",
    "format_navigation_label",
    "build_dashboard_view_model",
    "build_traceability_text",
    "build_pareto_view_model",
    "parse_report_sections",
    "prepare_batch_display",
    "preview_column_config",
    "render_batch_csv_preview",
    "render_batch_file_summary",
    "render_batch_kpi_cards",
    "render_batch_results_header",
    "render_batch_summary_band",
    "render_batch_upload_empty",
    "render_batch_stepper",
    "render_attention_panel",
    "render_ai_report_intro",
    "render_confidence_context_chart",
    "render_dashboard_kpis",
    "render_dataset_reading",
    "render_deterministic_brief",
    "render_individual_empty_state",
    "render_individual_intro",
    "render_individual_result_heading",
    "render_panel_heading",
    "render_pareto_detail_table",
    "render_pareto_methodology",
    "render_pareto_priority_chart",
    "render_pareto_summary",
    "render_probability_chart",
    "render_priority_ranking",
    "render_sentiment_distribution_chart",
    "render_product_header",
    "render_dataset_context",
    "render_page_header",
    "render_result_card",
    "render_sidebar_brand",
    "render_sidebar_footer",
    "render_sidebar_signature",
    "render_workspace_empty_state",
    "selectable_text_columns",
]
