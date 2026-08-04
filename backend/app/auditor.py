import asyncio
import json
import re
from collections.abc import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from .config import settings
from .models import (
    AgentRule,
    AuditResponse,
    JavaScriptReport,
    LLMsFileReport,
    LLMsReport,
    RobotsReport,
    SchemaReport,
)
from .security import validate_public_url

AI_AGENTS = ("OAI-SearchBot", "PerplexityBot", "ClaudeBot", "GPTBot", "ChatGPT-User")
KEY_ENTITIES = ("Organization", "WebSite", "Article", "Product")


def _site_root(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/", "", ""))


def _body_word_count(html: str) -> int:
    body = BeautifulSoup(html, "html.parser").body
    return len(re.findall(r"\b[\w'-]+\b", body.get_text(" ", strip=True) if body else ""))


async def _get_text(client: httpx.AsyncClient, url: str) -> tuple[httpx.Response, str]:
    response = await client.get(url)
    response.raise_for_status()
    content = response.content[: settings.max_response_bytes]
    return response, content.decode(response.encoding or "utf-8", errors="replace")


async def check_robots(client: httpx.AsyncClient, root: str) -> RobotsReport:
    url = urljoin(root, "robots.txt")
    try:
        _, text = await _get_text(client, url)
        parser = RobotFileParser()
        parser.set_url(url)
        parser.parse(text.splitlines())
        agents = [
            AgentRule(agent=agent, status="allowed" if parser.can_fetch(agent, root) else "blocked")
            for agent in AI_AGENTS
        ]
        return RobotsReport(url=url, found=True, passed=all(a.status == "allowed" for a in agents), agents=agents)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            agents = [AgentRule(agent=agent, status="allowed") for agent in AI_AGENTS]
            return RobotsReport(url=url, found=False, passed=True, agents=agents)
        return RobotsReport(url=url, found=False, passed=False, agents=[AgentRule(agent=a, status="unknown") for a in AI_AGENTS], error=f"HTTP {exc.response.status_code}")
    except httpx.HTTPError as exc:
        return RobotsReport(url=url, found=False, passed=False, agents=[AgentRule(agent=a, status="unknown") for a in AI_AGENTS], error=str(exc))


async def check_llms_file(client: httpx.AsyncClient, url: str) -> LLMsFileReport:
    try:
        _, text = await _get_text(client, url)
        tokens = MarkdownIt().parse(text)
        has_h1 = any(token.type == "heading_open" and token.tag == "h1" for token in tokens)
        return LLMsFileReport(url=url, found=True, valid_markdown=has_h1, has_h1=has_h1)
    except httpx.HTTPStatusError as exc:
        return LLMsFileReport(url=url, found=False, valid_markdown=False, has_h1=False, error=f"HTTP {exc.response.status_code}")
    except httpx.HTTPError as exc:
        return LLMsFileReport(url=url, found=False, valid_markdown=False, has_h1=False, error=str(exc))


def _walk_types(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        item_type = value.get("@type")
        if isinstance(item_type, str):
            yield item_type
        elif isinstance(item_type, list):
            yield from (item for item in item_type if isinstance(item, str))
        for child in value.values():
            yield from _walk_types(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_types(child)


def extract_schema(html: str) -> SchemaReport:
    scripts = BeautifulSoup(html, "html.parser").find_all("script", type="application/ld+json")
    types: set[str] = set()
    invalid = 0
    for script in scripts:
        try:
            types.update(_walk_types(json.loads(script.string or script.get_text())))
        except (json.JSONDecodeError, TypeError):
            invalid += 1
    return SchemaReport(script_count=len(scripts), types=sorted(types), key_entities={name: name in types for name in KEY_ENTITIES}, invalid_script_count=invalid)


async def render_html(url: str) -> str:
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=settings.browser_timeout_ms)
                return await page.content()
            finally:
                await browser.close()
    except PlaywrightTimeoutError as exc:
        raise RuntimeError("The browser timed out while rendering the page") from exc


async def run_audit(url: str) -> AuditResponse:
    await validate_public_url(url)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers={"User-Agent": settings.user_agent}) as client:
        raw_response, raw_html = await _get_text(client, url)
        final_url = str(raw_response.url)
        await validate_public_url(final_url)
        root = _site_root(final_url)
        robots_task = check_robots(client, root)
        llms_tasks = [check_llms_file(client, urljoin(root, name)) for name in ("llms.txt", "llms-full.txt")]
        rendered_task = render_html(final_url)
        robots, *rest = await asyncio.gather(robots_task, *llms_tasks, rendered_task)

    llms_files = rest[:-1]
    rendered_html = rest[-1]
    raw_words, rendered_words = _body_word_count(raw_html), _body_word_count(rendered_html)
    ratio = raw_words / rendered_words if rendered_words else 1.0
    return AuditResponse(
        requested_url=url,
        final_url=final_url,
        robots=robots,
        llms=LLMsReport(passed=any(item.valid_markdown for item in llms_files), files=llms_files),
        javascript=JavaScriptReport(raw_word_count=raw_words, rendered_word_count=rendered_words, raw_to_rendered_ratio=round(ratio, 3), js_reliant=rendered_words > 0 and ratio < 0.2),
        schema=extract_schema(raw_html),
    )
