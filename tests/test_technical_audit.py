from unittest.mock import MagicMock, patch

from agents.technical_audit import (
    check_for_schema,
    check_llm_files,
    check_robots_txt,
    technical_audit,
)

ROBOTS_TXT_WITH_EXPLICIT_RULES = """User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Allow: /

User-agent: *
Allow: /
"""

ROBOTS_TXT_WILDCARD_ONLY = """User-agent: *
Disallow: /private
"""


def _mock_response(status_code=200, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


@patch("agents.technical_audit.requests.get")
def test_check_robots_txt_classifies_explicit_and_wildcard_rules(mock_get):
    mock_get.return_value = _mock_response(200, ROBOTS_TXT_WITH_EXPLICIT_RULES)

    result = check_robots_txt("https://example.com")

    robots_txt = result["robots_txt"]
    assert robots_txt["exists"] is True
    assert "GPTBot" in robots_txt["blocked_ai_crawlers"]
    assert "ClaudeBot" in robots_txt["allowed_ai_crawlers"]
    # Crawlers not explicitly named fall back to the wildcard rule
    assert "PerplexityBot" in robots_txt["allowed_ai_crawlers"]


@patch("agents.technical_audit.requests.get")
def test_check_robots_txt_missing_returns_not_exists(mock_get):
    mock_get.return_value = _mock_response(404)

    result = check_robots_txt("https://example.com")

    assert result == {"robots_txt": {"exists": False}}


@patch("agents.technical_audit.requests.get")
def test_check_robots_txt_server_error_captures_error(mock_get):
    mock_get.return_value = _mock_response(500)

    result = check_robots_txt("https://example.com")

    assert result["robots_txt"]["exists"] is False
    assert "errors" in result


@patch("agents.technical_audit.requests.get")
def test_check_llm_files_exists(mock_get):
    mock_get.return_value = _mock_response(200, "# LLMs.txt content")

    result = check_llm_files("https://example.com", "llms.txt", "llms_txt")

    assert result["llms_txt"]["exists"] is True
    assert result["llms_txt"]["raw_content"] == "# LLMs.txt content"


def test_check_for_schema_detects_single_type():
    html = """
    <html><head>
    <script type="application/ld+json">{"@type": "Organization", "name": "Acme"}</script>
    </head></html>
    """

    result = check_for_schema(html)

    assert result["schema"]["exists"] is True
    assert result["schema"]["schema_type"] == ["Organization"]


def test_check_for_schema_handles_graph_pattern():
    html = """
    <script type="application/ld+json">
    {"@graph": [{"@type": "WebSite"}, {"@type": "Organization"}]}
    </script>
    """

    result = check_for_schema(html)

    assert set(result["schema"]["schema_type"]) == {"WebSite", "Organization"}


def test_check_for_schema_returns_not_exists_when_absent():
    result = check_for_schema("<html><head></head></html>")

    assert result == {"schema": {"exists": False}}


@patch("agents.technical_audit.check_for_schema")
@patch("agents.technical_audit.check_llm_files")
@patch("agents.technical_audit.check_robots_txt")
def test_technical_audit_merges_results_from_all_checks(mock_robots, mock_llms, mock_schema):
    mock_robots.return_value = {"robots_txt": {"exists": True}}
    mock_llms.side_effect = [
        {"llms_txt": {"exists": False}},
        {"llms_full_txt": {"exists": False}},
    ]
    mock_schema.return_value = {"schema": {"exists": True, "schema_type": ["Organization"]}}

    state = {"input_url": "https://example.com", "raw_html": "<html></html>"}
    result = technical_audit(state)

    assert result["robots_txt"]["exists"] is True
    assert result["schema"]["schema_type"] == ["Organization"]
    assert "errors" not in result


@patch("agents.technical_audit.check_for_schema")
@patch("agents.technical_audit.check_llm_files")
@patch("agents.technical_audit.check_robots_txt")
def test_technical_audit_collects_errors_from_all_checks(mock_robots, mock_llms, mock_schema):
    mock_robots.return_value = {"robots_txt": {"exists": False}, "errors": ["robots failed"]}
    mock_llms.side_effect = [
        {"llms_txt": {"exists": False}},
        {"llms_full_txt": {"exists": False}, "errors": ["llms-full timed out"]},
    ]
    mock_schema.return_value = {"schema": {"exists": False}}

    state = {"input_url": "https://example.com", "raw_html": "<html></html>"}
    result = technical_audit(state)

    assert result["errors"] == ["robots failed", "llms-full timed out"]
