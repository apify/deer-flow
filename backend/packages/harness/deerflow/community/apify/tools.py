import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor

from apify_client import ApifyClient
from langchain.tools import tool
from langgraph.config import get_stream_writer

from deerflow.config import get_app_config

TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


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


@tool("apify_actor_discover", parse_docstring=True)
def apify_actor_discover_tool(query: str = "", actor_id: str = "") -> str:
    """Search the Apify Store for actors, or fetch an actor's input schema.
    Use before apify_actor_start on an unfamiliar actor to learn what input it expects.
    Provide query to search the store, or actor_id to fetch a specific actor's schema. Not both.

    Args:
        query: Search term to find actors in the Apify Store. E.g. 'instagram scraper'.
        actor_id: Full actor ID to fetch its input schema. E.g. 'apify/instagram-scraper'.
    """
    if not query and not actor_id:
        return "Error: provide either query or actor_id, not neither"
    if query and actor_id:
        return "Error: provide either query or actor_id, not both"

    try:
        config = get_app_config().get_tool_config("apify_actor_discover")
        limit = 10
        if config is not None:
            limit = config.model_extra.get("max_results", limit)

        client = _get_apify_client("apify_actor_discover")

        if query:
            result = client.store().list(search=query, limit=limit)
            actors = []
            for a in result.items:
                username = a.get("username") or ""
                name = a.get("name") or ""
                if not username or not name:
                    continue
                actors.append({
                    "actorId": f"{username}/{name}",
                    "title": a.get("title") or "",
                    "description": (a.get("description") or "")[:200],
                })
            return json.dumps(
                {"action": "store_search", "query": query, "count": len(actors), "actors": actors},
                indent=2,
                ensure_ascii=False,
            )

        if not actor_id:
            return "Error: actor_id must not be empty"

        actor = client.actor(actor_id).get()
        if not actor:
            return f"Error: actor '{actor_id}' not found"

        input_schema = None
        try:
            versions = client.actor(actor_id).versions().list()
            if versions.items:
                latest = versions.items[-1]
                input_schema = latest.get("inputSchema")
        except Exception:
            pass  # input schema is best-effort

        return json.dumps(
            {
                "action": "actor_schema",
                "actorId": actor_id,
                "title": actor.get("title") or "",
                "description": (actor.get("description") or "")[:500],
                "inputSchema": input_schema,
            },
            indent=2,
            ensure_ascii=False,
        )
    except Exception as e:
        return f"Error: {str(e)}"


@tool("apify_actor_start", parse_docstring=True)
def apify_actor_start_tool(actor_id: str, run_input: str, label: str = "") -> str:
    """Start an Apify actor run asynchronously and return a run reference immediately.
    The actor runs in the background — use apify_actor_await with the returned runId and datasetId to wait for results.
    To run multiple actors in parallel, call this tool once per actor, then call apify_actor_await for each run.
    You MUST call this tool directly when asked to start an actor — do not ask for clarification.

    Args:
        actor_id: The Apify actor ID, e.g. 'apify/instagram-scraper'. Must not be empty.
        run_input: The actor input as a JSON-encoded string. Use "{}" for no input. E.g. '{"query": "test"}'.
        label: Optional label to identify this run when collecting results from multiple runs.
    """
    if not actor_id:
        return "Error: actor_id must not be empty"

    try:
        parsed_input = json.loads(run_input)
    except json.JSONDecodeError as e:
        return f"Error: run_input is not valid JSON — {str(e)}"

    try:
        config = get_app_config().get_tool_config("apify_actor_start")
        timeout_secs = None
        memory_mbytes = None
        if config is not None:
            timeout_secs = config.model_extra.get("timeout_secs")
            memory_mbytes = config.model_extra.get("memory_mbytes")

        client = _get_apify_client("apify_actor_start")

        start_kwargs: dict = {"run_input": parsed_input}
        if timeout_secs is not None:
            start_kwargs["timeout_secs"] = timeout_secs
        if memory_mbytes is not None:
            start_kwargs["memory_mbytes"] = memory_mbytes

        run = client.actor(actor_id).start(**start_kwargs)
        ref: dict = {
            "runId": run["id"],
            "actorId": actor_id,
            "datasetId": run["defaultDatasetId"],
            "status": run["status"],
        }
        if label:
            ref["label"] = label
        return json.dumps({"action": "start", "runs": [ref]}, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"


@tool("apify_actor_collect", parse_docstring=True)
def apify_actor_collect_tool(runs: str) -> str:
    """Check the status of previously started Apify actor runs and retrieve results for completed ones.
    Pass the run references exactly as returned by apify_actor_start (the runs array).
    Runs still in progress are returned with pending=true — call this tool again with those refs later.
    All runs are polled in parallel.

    Args:
        runs: JSON string of an array of run references from apify_actor_start. E.g. '[{"runId":"...","actorId":"...","datasetId":"..."}]'.
    """
    try:
        run_refs = json.loads(runs)
    except json.JSONDecodeError as e:
        return f"Error: runs is not valid JSON — {str(e)}"

    if not isinstance(run_refs, list) or not run_refs:
        return "Error: runs must be a non-empty JSON array of run references"

    try:
        config = get_app_config().get_tool_config("apify_actor_collect")
        max_items = 50
        if config is not None:
            max_items = config.model_extra.get("max_items", max_items)

        client = _get_apify_client("apify_actor_collect")

        def _fetch_run(ref: dict) -> dict:
            run_id = ref.get("runId", "")
            actor_id = ref.get("actorId", "")
            label = ref.get("label")

            try:
                run = client.run(run_id).get()
                if not run:
                    entry: dict = {"runId": run_id, "actorId": actor_id, "error": "Run not found"}
                    if label:
                        entry["label"] = label
                    return entry

                status = run.get("status", "")

                if status not in TERMINAL_STATUSES:
                    entry = {"runId": run_id, "actorId": actor_id, "status": status, "pending": True}
                    if label:
                        entry["label"] = label
                    return entry

                if status != "SUCCEEDED":
                    entry = {"runId": run_id, "actorId": actor_id, "status": status, "error": f"Run {status.lower()}"}
                    if label:
                        entry["label"] = label
                    return entry

                dataset_id = run.get("defaultDatasetId", "")
                items = list(client.dataset(dataset_id).iterate_items(limit=max_items))
                entry = {
                    "runId": run_id,
                    "actorId": actor_id,
                    "datasetId": dataset_id,
                    "status": "SUCCEEDED",
                    "resultCount": len(items),
                    "results": items,
                }
                if label:
                    entry["label"] = label
                return entry

            except Exception as exc:
                entry = {"runId": run_id, "actorId": actor_id, "error": str(exc)}
                if label:
                    entry["label"] = label
                return entry

        max_workers = min(len(run_refs), 10)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_fetch_run, run_refs))

        errors = [r for r in results if "error" in r]
        pending = [r for r in results if r.get("pending") and "error" not in r]
        completed = [r for r in results if r.get("status") == "SUCCEEDED" and "error" not in r]
        all_done = len(pending) == 0

        parts = []
        if completed:
            parts.append(f"{len(completed)} completed")
        if pending:
            parts.append(f"{len(pending)} still running")
        if errors:
            parts.append(f"{len(errors)} failed")
        message = ", ".join(parts) + "." if parts else "No runs processed."

        response: dict = {"action": "collect", "allDone": all_done, "message": message, "completed": completed}
        if pending:
            response["pending"] = pending
        if errors:
            response["errors"] = errors

        return json.dumps(response, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"


@tool("apify_actor_await", parse_docstring=True)
async def apify_actor_await_tool(run_id: str, dataset_id: str, label: str = "") -> str:
    """Wait for a previously started Apify actor run to complete and return its results.
    Use this instead of calling apify_actor_collect in a loop — a single call waits
    internally without repeated tool invocations, so loop detection never fires.

    Args:
        run_id: The run ID returned by apify_actor_start.
        dataset_id: The dataset ID returned by apify_actor_start.
        label: Optional label to include in the response for identification.
    """
    if not run_id:
        return "Error: run_id must not be empty"

    config = get_app_config().get_tool_config("apify_actor_await")
    poll_interval_secs = 5
    timeout_secs = 300
    max_items = 50
    if config is not None:
        poll_interval_secs = config.model_extra.get("poll_interval_secs", poll_interval_secs)
        timeout_secs = config.model_extra.get("timeout_secs", timeout_secs)
        max_items = config.model_extra.get("max_items", max_items)

    client = _get_apify_client("apify_actor_await")
    writer = get_stream_writer()

    loop = asyncio.get_event_loop()
    start_time = loop.time()
    deadline = start_time + timeout_secs

    writer({"type": "apify_run_polling", "runId": run_id, "status": "WAITING", "elapsed_secs": 0})

    try:
        while loop.time() < deadline:
            run = client.run(run_id).get()
            if not run:
                return json.dumps({"runId": run_id, "error": "Run not found"}, ensure_ascii=False)

            status = run.get("status", "")
            elapsed = int(loop.time() - start_time)

            if status in TERMINAL_STATUSES:
                if status != "SUCCEEDED":
                    writer({"type": "apify_run_failed", "runId": run_id, "status": status, "elapsed_secs": elapsed})
                    entry: dict = {"runId": run_id, "status": status, "error": f"Run {status.lower()}"}
                    if label:
                        entry["label"] = label
                    return json.dumps(entry, indent=2, ensure_ascii=False)

                # Use the fresh run's dataset ID in case it differs from the one passed in
                resolved_dataset_id = run.get("defaultDatasetId") or dataset_id
                items = list(client.dataset(resolved_dataset_id).iterate_items(limit=max_items))
                writer({"type": "apify_run_completed", "runId": run_id, "status": "SUCCEEDED", "elapsed_secs": elapsed, "resultCount": len(items)})
                entry = {"runId": run_id, "status": "SUCCEEDED", "resultCount": len(items), "results": items}
                if label:
                    entry["label"] = label
                return json.dumps(entry, indent=2, ensure_ascii=False)

            writer({"type": "apify_run_polling", "runId": run_id, "status": status, "elapsed_secs": elapsed})
            await asyncio.sleep(poll_interval_secs)

    except asyncio.CancelledError:
        writer({"type": "apify_run_cancelled", "runId": run_id})
        raise

    elapsed = int(loop.time() - start_time)
    entry = {"runId": run_id, "error": f"Run did not complete within {timeout_secs}s", "status": "TIMED_OUT"}
    if label:
        entry["label"] = label
    return json.dumps(entry, indent=2, ensure_ascii=False)
