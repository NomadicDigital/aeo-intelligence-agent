from unittest.mock import MagicMock

from firecrawl.v2.types import Document, DocumentMetadata

from agents import research as research_module
from agents.research import research


def _scrape_response(markdown="content", raw_html="<html></html>", status_code=200, title="Biz", description="desc"):
    resp = MagicMock()
    resp.metadata.status_code = status_code
    resp.metadata.title = title
    resp.metadata.description = description
    resp.markdown = markdown
    resp.raw_html = raw_html
    return resp


def _document(status_code=200):
    """
    A real Firecrawl Document rather than a MagicMock, so the code under test
    can only use attributes the SDK actually provides.
    """
    return Document(
        markdown="content",
        raw_html="<html></html>",
        metadata=DocumentMetadata(status_code=status_code, title="Biz", description="desc"),
    )


def _stub_sleep(monkeypatch):
    delays = []
    monkeypatch.setattr(research_module.time, "sleep", delays.append)
    return delays


def _stub_crawler(monkeypatch, scrape=None):
    crawler = MagicMock()
    crawler.scrape = scrape or MagicMock(return_value=_scrape_response())
    monkeypatch.setattr(research_module, "get_crawler_app", lambda: crawler)
    return crawler


def _stub_llm(monkeypatch, extraction=None, side_effect=None):
    structured_llm = MagicMock()
    if side_effect:
        structured_llm.invoke.side_effect = side_effect
    else:
        structured_llm.invoke.return_value = extraction
    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm
    monkeypatch.setattr(research_module, "ChatAnthropic", MagicMock(return_value=llm))


def test_research_success_returns_extracted_fields(monkeypatch):
    _stub_crawler(monkeypatch)
    extraction = MagicMock(
        business_name="Acme Co",
        description="A widget maker",
        competitors=["Widget Corp"],
        core_queries=["best widget maker"],
    )
    _stub_llm(monkeypatch, extraction=extraction)

    result = research({"input_url": "https://example.com"})

    assert result["business_name"] == "Acme Co"
    assert result["competitors"] == ["Widget Corp"]
    assert result["raw_html"] == "<html></html>"
    assert "errors" not in result


def test_research_returns_error_when_scrape_raises(monkeypatch):
    _stub_crawler(monkeypatch, scrape=MagicMock(side_effect=ConnectionError("network unreachable")))

    result = research({"input_url": "https://example.com"})

    assert "errors" in result
    assert "network unreachable" in result["errors"][0]


def test_research_returns_error_on_system_error_status(monkeypatch):
    _stub_crawler(monkeypatch, scrape=MagicMock(return_value=_scrape_response(status_code=401)))

    result = research({"input_url": "https://example.com"})

    assert "errors" in result
    assert "401" in result["errors"][0]


def test_research_returns_error_when_scrape_returns_none(monkeypatch):
    _stub_crawler(monkeypatch, scrape=MagicMock(return_value=_scrape_response(status_code=404)))

    result = research({"input_url": "https://example.com"})

    assert "errors" in result
    assert "Could not scrape" in result["errors"][0]


def test_research_returns_error_when_llm_fails(monkeypatch):
    _stub_crawler(monkeypatch)
    _stub_llm(monkeypatch, side_effect=RuntimeError("llm down"))

    result = research({"input_url": "https://example.com"})

    assert "errors" in result
    assert "llm down" in result["errors"][0]


def test_research_retries_retryable_status_with_backoff(monkeypatch):
    crawler = _stub_crawler(
        monkeypatch,
        scrape=MagicMock(side_effect=[_document(503), _document(503), _document(200)]),
    )
    delays = _stub_sleep(monkeypatch)
    _stub_llm(monkeypatch, extraction=MagicMock(
        business_name="Acme Co",
        description="A widget maker",
        competitors=["Widget Corp"],
        core_queries=["best widget maker"],
    ))

    result = research({"input_url": "https://example.com"})

    assert "errors" not in result
    assert result["business_name"] == "Acme Co"
    assert crawler.scrape.call_count == 3
    assert len(delays) == 2
    assert delays[0] < delays[1]


def test_research_gives_up_after_max_retries(monkeypatch):
    crawler = _stub_crawler(monkeypatch, scrape=MagicMock(return_value=_document(503)))
    delays = _stub_sleep(monkeypatch)

    result = research({"input_url": "https://example.com"})

    assert "Could not scrape" in result["errors"][0]
    assert crawler.scrape.call_count == 1 + research_module.MAX_SCRAPE_RETRIES
    assert len(delays) == research_module.MAX_SCRAPE_RETRIES
