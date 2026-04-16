"""Unit tests for the Apify community tools."""

import json
from unittest.mock import MagicMock, patch


class TestWebSearchTool:
    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_normalized_json(self, mock_get_app_config, mock_apify_cls):
        search_config = MagicMock()
        search_config.model_extra = {"api_key": "test-key", "max_results": 3}
        mock_get_app_config.return_value.get_tool_config.return_value = search_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"organicResults": [{"title": "T", "url": "https://example.com", "description": "S"}]}
        ])

        from deerflow.community.apify.tools import web_search_tool

        result = web_search_tool.invoke({"query": "test"})

        assert json.loads(result) == [{"title": "T", "url": "https://example.com", "snippet": "S"}]

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_max_results_from_config(self, mock_get_app_config, mock_apify_cls):
        search_config = MagicMock()
        search_config.model_extra = {"api_key": "test-key", "max_results": 7}
        mock_get_app_config.return_value.get_tool_config.return_value = search_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"organicResults": []}
        ])

        from deerflow.community.apify.tools import web_search_tool

        web_search_tool.invoke({"query": "test"})

        mock_apify_cls.return_value.actor.return_value.call.assert_called_once_with(
            run_input={"queries": "test", "maxPagesPerQuery": 1, "resultsPerPage": 7}
        )

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_api_key_from_config(self, mock_get_app_config, mock_apify_cls):
        search_config = MagicMock()
        search_config.model_extra = {"api_key": "my-apify-key", "max_results": 5}
        mock_get_app_config.return_value.get_tool_config.return_value = search_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"organicResults": []}
        ])

        from deerflow.community.apify.tools import web_search_tool

        web_search_tool.invoke({"query": "test"})

        mock_apify_cls.assert_called_with("my-apify-key")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_string_on_exception(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.call.side_effect = RuntimeError("actor failed")

        from deerflow.community.apify.tools import web_search_tool

        result = web_search_tool.invoke({"query": "test"})

        assert result.startswith("Error:")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_caps_results_at_max_results(self, mock_get_app_config, mock_apify_cls):
        search_config = MagicMock()
        search_config.model_extra = {"api_key": "test-key", "max_results": 2}
        mock_get_app_config.return_value.get_tool_config.return_value = search_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        organic = [{"title": f"T{i}", "url": f"https://example.com/{i}", "description": "S"} for i in range(5)]
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"organicResults": organic}
        ])

        from deerflow.community.apify.tools import web_search_tool

        result = web_search_tool.invoke({"query": "test"})

        assert len(json.loads(result)) == 2

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_defaults_when_config_is_none(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"organicResults": []}
        ])

        from deerflow.community.apify.tools import web_search_tool

        web_search_tool.invoke({"query": "test"})

        mock_apify_cls.return_value.actor.return_value.call.assert_called_once_with(
            run_input={"queries": "test", "maxPagesPerQuery": 1, "resultsPerPage": 5}
        )


class TestWebFetchTool:
    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_markdown_with_title(self, mock_get_app_config, mock_apify_cls):
        fetch_config = MagicMock()
        fetch_config.model_extra = {"api_key": "test-key", "crawler_type": "cheerio"}
        mock_get_app_config.return_value.get_tool_config.return_value = fetch_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"title": "My Page", "markdown": "Hello world", "text": ""}
        ])

        from deerflow.community.apify.tools import web_fetch_tool

        result = web_fetch_tool.invoke({"url": "https://example.com"})

        assert result == "# My Page\n\nHello world"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_crawler_type_from_config(self, mock_get_app_config, mock_apify_cls):
        fetch_config = MagicMock()
        fetch_config.model_extra = {"api_key": "test-key", "crawler_type": "playwright:firefox"}
        mock_get_app_config.return_value.get_tool_config.return_value = fetch_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"title": "Page", "markdown": "content", "text": ""}
        ])

        from deerflow.community.apify.tools import web_fetch_tool

        web_fetch_tool.invoke({"url": "https://example.com"})

        mock_apify_cls.return_value.actor.return_value.call.assert_called_once_with(
            run_input={"startUrls": [{"url": "https://example.com"}], "maxCrawlPages": 1, "crawlerType": "playwright:firefox"}
        )

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_falls_back_to_text_when_no_markdown(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"title": "Page", "markdown": "", "text": "plain text fallback"}
        ])

        from deerflow.community.apify.tools import web_fetch_tool

        result = web_fetch_tool.invoke({"url": "https://example.com"})

        assert result == "# Page\n\nplain text fallback"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_when_no_items(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import web_fetch_tool

        result = web_fetch_tool.invoke({"url": "https://example.com"})

        assert result == "Error: No content found"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_truncates_content_to_4096(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        long_content = "x" * 5000
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"title": "Page", "markdown": long_content, "text": ""}
        ])

        from deerflow.community.apify.tools import web_fetch_tool

        result = web_fetch_tool.invoke({"url": "https://example.com"})

        assert result.endswith("\n\n[Content truncated]")
        # content portion is exactly 4096 chars
        assert len(result) == len("# Page\n\n") + 4096 + len("\n\n[Content truncated]")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_no_truncation_marker_when_short(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"title": "Page", "markdown": "short content", "text": ""}
        ])

        from deerflow.community.apify.tools import web_fetch_tool

        result = web_fetch_tool.invoke({"url": "https://example.com"})

        assert "[Content truncated]" not in result

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_string_on_exception(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.call.side_effect = RuntimeError("network error")

        from deerflow.community.apify.tools import web_fetch_tool

        result = web_fetch_tool.invoke({"url": "https://example.com"})

        assert result.startswith("Error:")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_defaults_when_config_is_none(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"title": "Page", "markdown": "content", "text": ""}
        ])

        from deerflow.community.apify.tools import web_fetch_tool

        web_fetch_tool.invoke({"url": "https://example.com"})

        mock_apify_cls.return_value.actor.return_value.call.assert_called_once_with(
            run_input={"startUrls": [{"url": "https://example.com"}], "maxCrawlPages": 1, "crawlerType": "cheerio"}
        )
