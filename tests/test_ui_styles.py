"""Regression tests for global presentation styles."""

from unittest.mock import patch

from src.ui.styles import load_global_styles


def test_primary_button_styles_cover_actions_and_accessible_states() -> None:
    with patch("src.ui.styles.st.markdown") as markdown:
        load_global_styles()

    css = markdown.call_args.args[0]
    assert ".stButton, .stFormSubmitButton" in css
    assert 'button[kind="primary"] :is(p, span)' in css
    assert ":hover:not(:disabled)" in css
    assert ":active:not(:disabled)" in css
    assert ":focus-visible" in css
    assert 'button[kind="primary"]:disabled' in css
    assert "color:#FFF" in css
    assert "opacity:1" in css
