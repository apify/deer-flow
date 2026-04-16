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


class TestApifyActorTool:
    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_calls_actor_with_parsed_input(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_tool

        apify_actor_tool.invoke({"actor_id": "apify/instagram-scraper", "run_input": '{"username": "apify"}'})

        mock_apify_cls.return_value.actor.assert_called_once_with("apify/instagram-scraper")
        mock_apify_cls.return_value.actor.return_value.call.assert_called_once_with(
            run_input={"username": "apify"},
            timeout_secs=120,
        )

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_dataset_items_as_json(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ])

        from deerflow.community.apify.tools import apify_actor_tool

        result = apify_actor_tool.invoke({"actor_id": "some/actor", "run_input": "{}"})

        assert json.loads(result) == [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_caps_items_at_max_items(self, mock_get_app_config, mock_apify_cls):
        actor_config = MagicMock()
        actor_config.model_extra = {"max_items": 3, "timeout_secs": 60}
        mock_get_app_config.return_value.get_tool_config.return_value = actor_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_tool

        apify_actor_tool.invoke({"actor_id": "some/actor", "run_input": "{}"})

        mock_apify_cls.return_value.dataset.return_value.iterate_items.assert_called_once_with(limit=3)

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_invalid_json_run_input(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        from deerflow.community.apify.tools import apify_actor_tool

        result = apify_actor_tool.invoke({"actor_id": "some/actor", "run_input": "not json {"})

        assert result.startswith("Error: run_input is not valid JSON")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_timeout_secs_from_config(self, mock_get_app_config, mock_apify_cls):
        actor_config = MagicMock()
        actor_config.model_extra = {"max_items": 50, "timeout_secs": 60}
        mock_get_app_config.return_value.get_tool_config.return_value = actor_config

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_tool

        apify_actor_tool.invoke({"actor_id": "some/actor", "run_input": "{}"})

        mock_apify_cls.return_value.actor.return_value.call.assert_called_once_with(
            run_input={},
            timeout_secs=60,
        )

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_string_on_exception(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.call.side_effect = RuntimeError("actor failed")

        from deerflow.community.apify.tools import apify_actor_tool

        result = apify_actor_tool.invoke({"actor_id": "some/actor", "run_input": "{}"})

        assert result.startswith("Error:")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_defaults_when_config_is_none(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        mock_run = {"defaultDatasetId": "dataset-123"}
        mock_apify_cls.return_value.actor.return_value.call.return_value = mock_run
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_tool

        apify_actor_tool.invoke({"actor_id": "some/actor", "run_input": "{}"})

        mock_apify_cls.return_value.actor.return_value.call.assert_called_once_with(
            run_input={},
            timeout_secs=120,
        )
        mock_apify_cls.return_value.dataset.return_value.iterate_items.assert_called_once_with(limit=50)


class TestApifyActorDiscoverTool:
    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_store_search_returns_actor_list(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_result = MagicMock()
        mock_result.items = [
            {"username": "apify", "name": "instagram-scraper", "title": "Instagram Scraper", "description": "Scrapes Instagram"},
        ]
        mock_apify_cls.return_value.store.return_value.list.return_value = mock_result

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = json.loads(apify_actor_discover_tool.invoke({"query": "instagram"}))

        assert result["action"] == "store_search"
        assert result["count"] == 1
        assert result["actors"][0]["actorId"] == "apify/instagram-scraper"
        mock_apify_cls.return_value.store.return_value.list.assert_called_once_with(search="instagram", limit=10)

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_store_search_filters_actors_with_missing_fields(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_result = MagicMock()
        mock_result.items = [
            {"username": "", "name": "test", "title": "T", "description": "D"},
            {"username": "apify", "name": "", "title": "T", "description": "D"},
            {"username": "apify", "name": "valid", "title": "Valid", "description": "OK"},
        ]
        mock_apify_cls.return_value.store.return_value.list.return_value = mock_result

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = json.loads(apify_actor_discover_tool.invoke({"query": "test"}))

        assert result["count"] == 1
        assert result["actors"][0]["actorId"] == "apify/valid"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_actor_schema_returns_input_schema(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.get.return_value = {"title": "My Actor", "description": "Desc"}
        mock_versions = MagicMock()
        mock_versions.items = [{"versionNumber": "0.0", "inputSchema": '{"type":"object"}'}]
        mock_apify_cls.return_value.actor.return_value.versions.return_value.list.return_value = mock_versions

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = json.loads(apify_actor_discover_tool.invoke({"actor_id": "apify/my-actor"}))

        assert result["action"] == "actor_schema"
        assert result["inputSchema"] == '{"type":"object"}'

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_actor_schema_returns_none_when_versions_raises(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.get.return_value = {"title": "My Actor", "description": "Desc"}
        mock_apify_cls.return_value.actor.return_value.versions.return_value.list.side_effect = RuntimeError("API error")

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = json.loads(apify_actor_discover_tool.invoke({"actor_id": "apify/my-actor"}))

        assert result["action"] == "actor_schema"
        assert result["inputSchema"] is None

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_when_actor_not_found(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.get.return_value = None

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = apify_actor_discover_tool.invoke({"actor_id": "apify/nonexistent"})

        assert "Error" in result and "not found" in result

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_when_neither_provided(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = apify_actor_discover_tool.invoke({"query": "", "actor_id": ""})

        assert result.startswith("Error:")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_when_both_provided(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = apify_actor_discover_tool.invoke({"query": "instagram", "actor_id": "apify/test"})

        assert result.startswith("Error:")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_string_on_exception(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.store.return_value.list.side_effect = RuntimeError("network error")

        from deerflow.community.apify.tools import apify_actor_discover_tool

        result = apify_actor_discover_tool.invoke({"query": "test"})

        assert result.startswith("Error:")


class TestApifyActorStartTool:
    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_run_reference_in_array(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.start.return_value = {
            "id": "run-123", "defaultDatasetId": "ds-456", "status": "RUNNING"
        }

        from deerflow.community.apify.tools import apify_actor_start_tool

        result = json.loads(apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "{}"}))

        assert result["action"] == "start"
        assert isinstance(result["runs"], list)
        assert len(result["runs"]) == 1
        ref = result["runs"][0]
        assert ref["runId"] == "run-123"
        assert ref["actorId"] == "apify/test"
        assert ref["datasetId"] == "ds-456"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_label_included_when_provided(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.start.return_value = {
            "id": "run-123", "defaultDatasetId": "ds-456", "status": "RUNNING"
        }

        from deerflow.community.apify.tools import apify_actor_start_tool

        result = json.loads(apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "{}", "label": "my-run"}))

        assert result["runs"][0]["label"] == "my-run"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_label_absent_when_not_provided(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.start.return_value = {
            "id": "run-123", "defaultDatasetId": "ds-456", "status": "RUNNING"
        }

        from deerflow.community.apify.tools import apify_actor_start_tool

        result = json.loads(apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "{}"}))

        assert "label" not in result["runs"][0]

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_calls_start_not_call(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.start.return_value = {
            "id": "run-123", "defaultDatasetId": "ds-456", "status": "RUNNING"
        }

        from deerflow.community.apify.tools import apify_actor_start_tool

        apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "{}"})

        mock_apify_cls.return_value.actor.return_value.start.assert_called_once()
        mock_apify_cls.return_value.actor.return_value.call.assert_not_called()

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_timeout_secs_from_config(self, mock_get_app_config, mock_apify_cls):
        cfg = MagicMock()
        cfg.model_extra = {"timeout_secs": 60}
        mock_get_app_config.return_value.get_tool_config.return_value = cfg
        mock_apify_cls.return_value.actor.return_value.start.return_value = {
            "id": "run-123", "defaultDatasetId": "ds-456", "status": "RUNNING"
        }

        from deerflow.community.apify.tools import apify_actor_start_tool

        apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "{}"})

        mock_apify_cls.return_value.actor.return_value.start.assert_called_once_with(run_input={}, timeout_secs=60)

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_no_timeout_when_not_in_config(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.start.return_value = {
            "id": "run-123", "defaultDatasetId": "ds-456", "status": "RUNNING"
        }

        from deerflow.community.apify.tools import apify_actor_start_tool

        apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "{}"})

        mock_apify_cls.return_value.actor.return_value.start.assert_called_once_with(run_input={})

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_for_empty_actor_id(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        from deerflow.community.apify.tools import apify_actor_start_tool

        result = apify_actor_start_tool.invoke({"actor_id": "", "run_input": "{}"})

        assert result.startswith("Error:")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_invalid_json_run_input(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        from deerflow.community.apify.tools import apify_actor_start_tool

        result = apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "not json"})

        assert "Error: run_input is not valid JSON" in result

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_string_on_exception(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.actor.return_value.start.side_effect = RuntimeError("API error")

        from deerflow.community.apify.tools import apify_actor_start_tool

        result = apify_actor_start_tool.invoke({"actor_id": "apify/test", "run_input": "{}"})

        assert result.startswith("Error:")


class TestApifyActorCollectTool:
    def _make_run_ref(self, run_id="run-123", actor_id="apify/test", dataset_id="ds-456", label=None):
        ref = {"runId": run_id, "actorId": actor_id, "datasetId": dataset_id}
        if label:
            ref["label"] = label
        return ref

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_completed_when_succeeded(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "SUCCEEDED", "defaultDatasetId": "ds-456"
        }
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([{"item": 1}])

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert result["allDone"] is True
        assert len(result["completed"]) == 1
        assert result["completed"][0]["status"] == "SUCCEEDED"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_results_is_list_not_string(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "SUCCEEDED", "defaultDatasetId": "ds-456"
        }
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([{"item": 1}])

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert isinstance(result["completed"][0]["results"], list)

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_pending_when_running(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "RUNNING", "defaultDatasetId": "ds-456"
        }

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert result["allDone"] is False
        assert len(result["pending"]) == 1
        assert result["pending"][0]["pending"] is True

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_when_failed(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "FAILED", "defaultDatasetId": "ds-456"
        }

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert result["allDone"] is True
        assert len(result["errors"]) == 1

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_returns_error_when_aborted(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "ABORTED", "defaultDatasetId": "ds-456"
        }

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert len(result["errors"]) == 1

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_all_done_true_when_all_succeeded(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "SUCCEEDED", "defaultDatasetId": "ds-456"
        }
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref("r1"), self._make_run_ref("r2")])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert result["allDone"] is True

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_message_includes_error_count(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        def run_get(run_id=None):
            m = MagicMock()
            m.get.return_value = {"status": "FAILED", "defaultDatasetId": "ds"}
            return m

        mock_apify_cls.return_value.run.side_effect = run_get

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert "failed" in result["message"]

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_polls_multiple_runs(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "RUNNING", "defaultDatasetId": "ds"
        }

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref("r1"), self._make_run_ref("r2"), self._make_run_ref("r3")])
        apify_actor_collect_tool.invoke({"runs": runs})

        assert mock_apify_cls.return_value.run.call_count == 3

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_dataset_id_from_fresh_run_object(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "SUCCEEDED", "defaultDatasetId": "fresh-ds-id"
        }
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref(dataset_id="stale-ds-id")])
        apify_actor_collect_tool.invoke({"runs": runs})

        mock_apify_cls.return_value.dataset.assert_called_once_with("fresh-ds-id")

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_partial_failure_returns_partial_results(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        call_count = {"n": 0}

        def run_side_effect(run_id):
            call_count["n"] += 1
            m = MagicMock()
            if call_count["n"] == 1:
                m.get.side_effect = RuntimeError("network failure")
            else:
                m.get.return_value = {"status": "SUCCEEDED", "defaultDatasetId": "ds"}
            return m

        mock_apify_cls.return_value.run.side_effect = run_side_effect
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref("r1"), self._make_run_ref("r2")])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert len(result["errors"]) == 1
        assert len(result["completed"]) == 1

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_run_not_found_goes_to_errors(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = None

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert len(result["errors"]) == 1
        assert result["errors"][0]["error"] == "Run not found"

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_uses_max_items_from_config(self, mock_get_app_config, mock_apify_cls):
        cfg = MagicMock()
        cfg.model_extra = {"max_items": 5}
        mock_get_app_config.return_value.get_tool_config.return_value = cfg
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "SUCCEEDED", "defaultDatasetId": "ds"
        }
        mock_apify_cls.return_value.dataset.return_value.iterate_items.return_value = iter([])

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        apify_actor_collect_tool.invoke({"runs": runs})

        mock_apify_cls.return_value.dataset.return_value.iterate_items.assert_called_once_with(limit=5)

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_categories_are_mutually_exclusive(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None
        mock_apify_cls.return_value.run.return_value.get.return_value = {
            "status": "FAILED", "defaultDatasetId": "ds"
        }

        from deerflow.community.apify.tools import apify_actor_collect_tool

        runs = json.dumps([self._make_run_ref()])
        result = json.loads(apify_actor_collect_tool.invoke({"runs": runs}))

        assert len(result["errors"]) == 1
        assert len(result["completed"]) == 0
        assert "pending" not in result

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_invalid_json_runs(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        from deerflow.community.apify.tools import apify_actor_collect_tool

        result = apify_actor_collect_tool.invoke({"runs": "not json"})

        assert "Error: runs is not valid JSON" in result

    @patch("deerflow.community.apify.tools.ApifyClient")
    @patch("deerflow.community.apify.tools.get_app_config")
    def test_empty_array_runs(self, mock_get_app_config, mock_apify_cls):
        mock_get_app_config.return_value.get_tool_config.return_value = None

        from deerflow.community.apify.tools import apify_actor_collect_tool

        result = apify_actor_collect_tool.invoke({"runs": "[]"})

        assert result.startswith("Error:")
