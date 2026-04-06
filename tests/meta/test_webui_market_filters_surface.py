from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_market_filters_script_is_wired_before_market_page_script() -> None:
    market_html = (REPO_ROOT / "sharelife" / "webui" / "market.html").read_text(encoding="utf-8")
    assert '<script src="/market_filters.js"></script>' in market_html
    assert '<script src="/market_facet_view.js"></script>' in market_html
    assert '<script src="/market_event_bindings.js"></script>' in market_html
    assert '<script src="/market_status_view.js"></script>' in market_html
    assert '<script src="/market_auth_view.js"></script>' in market_html
    assert market_html.index('<script src="/market_filters.js"></script>') < market_html.index(
        '<script src="/market_facet_view.js"></script>'
    )
    assert market_html.index('<script src="/market_facet_view.js"></script>') < market_html.index(
        '<script src="/market_event_bindings.js"></script>'
    )
    assert market_html.index('<script src="/market_event_bindings.js"></script>') < market_html.index(
        '<script src="/market_status_view.js"></script>'
    )
    assert market_html.index('<script src="/market_status_view.js"></script>') < market_html.index(
        '<script src="/market_auth_view.js"></script>'
    )
    assert market_html.index('<script src="/market_auth_view.js"></script>') < market_html.index(
        '<script src="/market_page.js"></script>'
    )
