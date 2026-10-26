"""Release-notes digest agent: read the changelogs so you don't have to.

Companion code for the Visual Studio Learn post and video
"I Built an AI Agent That Reads Release Notes So I Don't Have To".

Once a run, the agent fetches the latest GitHub release of each project
in PROJECTS below, asks Gemini to summarise the release notes in three
bullets and flag anything breaking, and writes one Markdown digest
(digest.md) with a breaking-changes section at the top.

Requires: Python 3.10 or newer, the packages in requirements.txt, and a
Gemini API key in the GEMINI_API_KEY environment variable. See README.md.
"""

import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser

import requests
from google import genai

logger = logging.getLogger("digest_agent")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

MODEL = "gemini-3.6-flash"

# The projects to watch: (display name, GitHub "owner/repo"). Add or
# remove lines here — nothing else in the file needs to change.
PROJECTS = [
    ("CPython", "python/cpython"),
    ("FastAPI", "tiangolo/fastapi"),
    ("Azure CLI", "Azure/azure-cli"),
]

FEED_URL = "https://github.com/{repo}/releases.atom"
USER_AGENT = "release-digest-agent/1.0 (Visual Studio Learn tutorial)"
FETCH_TIMEOUT_SECONDS = 30
MAX_NOTES_CHARS = 12_000  # truncate very long notes before the model call

# Published pay-as-you-go rates for gemini-3.6-flash, US$ per 1M tokens.
INPUT_RATE_PER_MILLION = 0.75
OUTPUT_RATE_PER_MILLION = 3.75

OUTPUT_FILE = "digest.md"

ATOM = {"a": "http://www.w3.org/2005/Atom"}
# Tags that mean "new line" when release-note HTML is flattened to text.
BLOCK_TAGS = {"p", "br", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "pre", "tr"}


@dataclass
class Release:
    """The latest release of one project, as published in its feed."""

    project: str
    title: str  # feed title, e.g. "v3.13.18" or "Azure CLI 2.91.0"
    published: str  # ISO date from the feed, e.g. "2026-10-25"
    url: str
    notes: str  # release notes as plain text (HTML already stripped)


@dataclass
class Summary:
    """Gemini's reading of one release, plus what the call cost."""

    bullets: list[str] = field(default_factory=list)
    breaking: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class _TextExtractor(HTMLParser):
    """Minimal HTML-to-text: keep the words, drop the markup."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(html: str) -> str:
    """Flatten release-note HTML to readable plain text."""
    extractor = _TextExtractor()
    extractor.feed(html)
    lines = (line.strip() for line in "".join(extractor.parts).splitlines())
    return "\n".join(line for line in lines if line)


def fetch_latest_release(project: str, repo: str) -> Release:
    """Fetch the newest entry of a project's GitHub releases Atom feed.

    The feed lists the 10 most recently published releases; the first
    entry is the newest. No GitHub account or token is needed — the
    feed is a public web page, not the rate-limited REST API.
    """
    url = FEED_URL.format(repo=repo)
    logger.info("Fetching %s", url)
    response = requests.get(
        url, headers={"User-Agent": USER_AGENT}, timeout=FETCH_TIMEOUT_SECONDS
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    entry = root.find("a:entry", ATOM)
    if entry is None:
        raise ValueError(f"{repo}: the releases feed has no entries")

    title = entry.findtext("a:title", default="", namespaces=ATOM).strip()
    updated = entry.findtext("a:updated", default="", namespaces=ATOM)
    link = entry.find("a:link", ATOM)
    content = entry.find("a:content", ATOM)
    notes_html = content.text if content is not None and content.text else ""

    return Release(
        project=project,
        title=title,
        published=updated[:10],
        url=link.get("href", "") if link is not None else "",
        notes=html_to_text(notes_html),
    )


def summarize_release(client: genai.Client, release: Release) -> Summary:
    """Ask Gemini for three bullets and any breaking changes in a release.

    The model only ever sees the notes text fetched above — it is told
    to work from that text alone and to say so when the notes are thin.
    Its answer comes back as JSON and is parsed defensively.
    """
    if not release.notes.strip():
        # Nothing to summarise: don't spend a model call on an empty page.
        logger.info("%s: no release notes published — skipping the model call",
                    release.project)
        return Summary(bullets=["No release notes were published with this release."])

    prompt = f"""You are summarising a software release for a working developer.

Project: {release.project}
Release: {release.title} ({release.published})

Release notes (plain text, converted from the project's own feed):
---
{release.notes[:MAX_NOTES_CHARS]}
---

Answer with ONLY a JSON object, no markdown fences, in exactly this shape:
{{"summary": ["bullet", "bullet", "bullet"],
  "breaking": ["one line per breaking change, or empty list"]}}

Rules:
- "summary" is exactly 3 short bullets, based only on the notes above.
- If the notes contain no real change details, say that honestly in one
  bullet instead of inventing changes.
- "breaking" lists only changes that could break existing code, config,
  or command lines — behaviour changes count. Ignore download hashes,
  links, and housekeeping.
"""

    response = client.models.generate_content(model=MODEL, contents=prompt)
    usage = response.usage_metadata
    text = (response.text or "").strip()
    if text.startswith("```"):  # strip code fences if the model adds them
        text = text.strip("`")
        text = text[text.find("{"):]

    try:
        data = json.loads(text)
        bullets = [str(b) for b in data.get("summary", [])][:3]
        breaking = [str(b) for b in data.get("breaking", [])]
    except (json.JSONDecodeError, AttributeError):
        logger.warning("%s: model answer was not the expected JSON; "
                       "keeping the raw text as a single bullet", release.project)
        bullets = [text] if text else ["The model returned an empty answer."]
        breaking = []

    return Summary(
        bullets=bullets,
        breaking=breaking,
        input_tokens=usage.prompt_token_count or 0,
        output_tokens=usage.candidates_token_count or 0,
    )


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimated US$ cost of the run at the published per-token rates."""
    return (
        input_tokens * INPUT_RATE_PER_MILLION
        + output_tokens * OUTPUT_RATE_PER_MILLION
    ) / 1_000_000


def build_digest(entries: list[tuple[Release, Summary]]) -> str:
    """Assemble the one-page Markdown digest from all summaries."""
    today = date.today().strftime("%A, %B %d, %Y")
    total_in = sum(s.input_tokens for _, s in entries)
    total_out = sum(s.output_tokens for _, s in entries)

    lines = [f"# Release Digest — {today}", ""]

    breaking_lines = [
        f"- **{release.project} {release.title}** — {item}"
        for release, summary in entries
        for item in summary.breaking
    ]
    lines += ["## ⚠ Breaking changes", ""]
    lines += breaking_lines or ["None flagged in this run."]
    lines.append("")

    for release, summary in entries:
        lines += [
            f"## {release.project} — {release.title}",
            "",
            f"Released: {release.published} · [Release notes]({release.url})",
            "",
        ]
        lines += [f"- {bullet}" for bullet in summary.bullets]
        lines.append("")

    lines += [
        "---",
        f"*Generated by digest_agent.py · Model: {MODEL} · "
        f"Tokens: {total_in:,} in / {total_out:,} out · "
        f"Estimated cost: ${estimate_cost(total_in, total_out):.6f}*",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not set. Get a key in Google AI "
                     "Studio and set it in the environment — see README.md.")
        return 1

    client = genai.Client(api_key=api_key)
    entries: list[tuple[Release, Summary]] = []
    failures = 0
    for project, repo in PROJECTS:
        try:
            release = fetch_latest_release(project, repo)
            entries.append((release, summarize_release(client, release)))
            logger.info("%s: %s (%s)", project, release.title, release.published)
        except Exception:
            failures += 1
            logger.exception("%s: fetch or summary failed — continuing "
                             "with the remaining projects", project)

    if not entries:
        logger.error("Every project failed; no digest written.")
        return 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        fh.write(build_digest(entries))
    logger.info("Wrote %s (%d project(s), %d failure(s))",
                OUTPUT_FILE, len(entries), failures)
    return 0


if __name__ == "__main__":
    sys.exit(main())
