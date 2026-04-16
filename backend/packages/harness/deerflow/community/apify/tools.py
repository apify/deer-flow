import json
import os

from apify_client import ApifyClient
from langchain.tools import tool

from deerflow.config import get_app_config


def _get_apify_client(tool_name: str) -> ApifyClient:
    config = get_app_config().get_tool_config(tool_name)
    api_key = None
    if config is not None and "api_key" in config.model_extra:
        api_key = config.model_extra.get("api_key")
    # Fall back to environment variable if not set in config
    if not api_key:
        api_key = os.environ.get("APIFY_API_TOKEN")
    return ApifyClient(api_key)


@tool("web_search", parse_docstring=True)
def web_search_tool(query: str) -> str:
    """Search the web.

    Args:
        query: The query to search for.
    """
    try:
        config = get_app_config().get_tool_config("web_search")
        max_results = 5
        if config is not None:
            max_results = config.model_extra.get("max_results", max_results)

        client = _get_apify_client("web_search")
        run = client.actor("apify/google-search-scraper").call(
            run_input={
                "queries": query,
                "maxPagesPerQuery": 1,
                "resultsPerPage": max_results,
            }
        )

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items(limit=1))
        organic = items[0].get("organicResults", []) if items else []

        normalized = [
            {
                "title": r.get("title", "") or "",
                "url": r.get("url", "") or "",
                "snippet": r.get("description", "") or "",
            }
            for r in organic[:max_results]
        ]
        return json.dumps(normalized, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"


@tool("web_fetch", parse_docstring=True)
def web_fetch_tool(url: str) -> str:
    """Fetch the contents of a web page at a given URL.
    Only fetch EXACT URLs that have been provided directly by the user or have been returned in results from the web_search and web_fetch tools.
    This tool can NOT access content that requires authentication, such as private Google Docs or pages behind login walls.
    Do NOT add www. to URLs that do NOT have them.
    URLs must include the schema: https://example.com is a valid URL while example.com is an invalid URL.

    Args:
        url: The URL to fetch the contents of.
    """
    try:
        config = get_app_config().get_tool_config("web_fetch")
        crawler_type = "cheerio"
        if config is not None:
            crawler_type = config.model_extra.get("crawler_type", crawler_type)

        client = _get_apify_client("web_fetch")
        run = client.actor("apify/website-content-crawler").call(
            run_input={
                "startUrls": [{"url": url}],
                "maxCrawlPages": 1,
                "crawlerType": crawler_type,
            }
        )

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items(limit=1))
        if not items:
            return "Error: No content found"

        item = items[0]
        title = item.get("title", "Untitled") or "Untitled"
        content = item.get("markdown", "") or item.get("text", "")

        if not content:
            return "Error: No content found"

        truncated = content[:4096]
        suffix = "\n\n[Content truncated]" if len(content) > 4096 else ""
        return f"# {title}\n\n{truncated}{suffix}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool("apify_run_actor", parse_docstring=True)
def apify_actor_tool(actor_id: str, run_input: str) -> str:
    """Run any Apify actor and return its dataset output as JSON.
    Use this for specialized data collection tasks: social media, e-commerce, maps,
    job listings, or any structured web data that requires a dedicated scraper.
    Only use actor IDs that are known to exist on the Apify platform.
    You MUST call this tool directly when asked to run an actor — do not ask for clarification.

    Args:
        actor_id: The Apify actor ID, e.g. 'apify/instagram-scraper'.
        run_input: The actor input as a JSON-encoded string. Use "{}" for empty input. Example: "{\"query\": \"test\"}".
    """
    try:
        parsed_input = json.loads(run_input)
    except json.JSONDecodeError as e:
        return f"Error: run_input is not valid JSON — {str(e)}"

    try:
        config = get_app_config().get_tool_config("apify_run_actor")
        max_items = 50
        timeout_secs = 120
        if config is not None:
            max_items = config.model_extra.get("max_items", max_items)
            timeout_secs = config.model_extra.get("timeout_secs", timeout_secs)

        client = _get_apify_client("apify_run_actor")
        run = client.actor(actor_id).call(
            run_input=parsed_input,
            timeout_secs=timeout_secs,
        )

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items(limit=max_items))
        return json.dumps(items, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"
