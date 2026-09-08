"""Regression tests for global presentation styles."""

from unittest.mock import patch

from src.ui.styles import load_global_styles


def test_primary_button_styles_cover_actions_and_accessible_states() -> None:
    with patch("src.ui.styles.st.markdown") as markdown:
        load_global_styles()

    css = markdown.call_args.args[0]
    assert '.stButton > button[kind="primary"]' in css
    assert '.stFormSubmitButton > button[kind="primaryFormSubmit"]' in css
    assert ") :is(p, span)" in css
    assert ":hover:not(:disabled)" in css
    assert ":active:not(:disabled)" in css
    assert ":focus-visible" in css
    assert "):disabled" in css
    assert "color:#FFF" in css
    assert "opacity:1" in css


def test_about_uses_readable_body_and_secondary_text_scales() -> None:
    with patch("src.ui.styles.st.markdown") as markdown:
        load_global_styles()

    css = markdown.call_args.args[0]
    assert ".about-team p { margin:0; color:var(--muted); font-size:.875rem" in css
    assert ".about-privacy p { margin:0 0 .65rem; color:#E0E7EA; font-size:.875rem" in css
    assert ".about-team-members span" in css and "font-size:.82rem" in css
    assert ".about-stages span" in css and "font-size:.78rem" in css
