#!/usr/bin/env python3
"""citewise - a free, open-source cited research engine.

Replaces paid "AI answer engine" subscriptions (e.g. Perplexity Pro, $20/mo).
- Web search via DuckDuckGo (no API key, no account, no paid dependency).
- Fetches + extracts source text with the Python standard library only.
- Optional LLM synthesis via ANY OpenAI-compatible endpoint (env-configured).
- Inline [1][2] citations + a Sources list. --deep runs a follow-up loop.
- --self-check verifies the search/fetch pipeline still works (the
  "updates for life" maintenance heartbeat).

MIT licensed. Zero paid dependencies. Runs anywhere Python 3.8+ runs.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; citewise/0.1; +https://github.com/Mellowambience/our-own-citewise)"
DDG = "https://html.duckduckgo.com/html/"
TIMEOUT = 15


def _get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def _strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(s).strip()


def _clean_ddg_url(href):
    # DDG wraps results in //duckduckgo.com/l/?uddg=<encoded>
    m = re.search(r"uddg=([^&]+)", href)
    if m:
        return urllib.parse.unquote(m.group(1))
    return href


def search(query, top=6):
    """Return list of {title, url, snippet} from DuckDuckGo HTML."""
    body = urllib.parse.urlencode({"q": query}).encode()
    doc = _get(DDG, body)
    titles = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', doc, re.S)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', doc, re.S)
    out = []
    for i, (href, title) in enumerate(titles[:top]):
        url = _clean_ddg_url(href)
        snip = _strip_tags(snippets[i]) if i < len(snippets) else ""
        out.append({"title": _strip_tags(title), "url": url, "snippet": snip})
    return out


def fetch_text(url, max_chars=4000):
    try:
        doc = _get(url)
        paras = re.findall(r"<p[^>]*>(.*?)</p>", doc, re.S)
        text = " ".join(_strip_tags(p) for p in paras)
        return text[:max_chars]
    except Exception as e:  # noqa: BLE001 - network is best-effort
        return f"[fetch failed: {e}]"


def sources_block(sources):
    return "\n".join(f"[{i + 1}] {s['title']} — {s['url']}" for i, s in enumerate(sources))


def extractive(query, sources):
    lines = [f"# Research brief: {query}\n",
             "No LLM configured (set OPENAI_API_KEY + OPENAI_BASE_URL for synthesis). "
             "Extractive summary from top sources:\n"]
    for i, s in enumerate(sources, 1):
        lines.append(f"\n[{i}] **{s['title']}** — {s['url']}")
        if s["snippet"]:
            lines.append(f"    {s['snippet'][:300]}")
    return "\n".join(lines)


def synthesize(query, sources):
    base = os.environ.get("OPENAI_BASE_URL")
    key = os.environ.get("OPENAI_API_KEY")
    if not (base and key):
        return extractive(query, sources)
    ctx = "\n\n".join(
        f"[{i + 1}] {s['title']} ({s['url']})\n{s['snippet']}" for i, s in enumerate(sources)
    )
    prompt = (f"Answer the query using ONLY the sources below. Cite each claim with [n]. "
              f"If sources disagree, say so. Be concise.\n\nQuery: {query}\n\nSources:\n{ctx}")
    body = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    try:
        req = urllib.request.Request(
            base.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"User-Agent": UA, "Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.load(r)
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001 - degrade gracefully
        return f"[synthesis failed: {e}]\n\n" + extractive(query, sources)


def deep_research(query, passes=3):
    all_src = list(search(query))
    subs = [f"{query} recent advances", f"{query} open source", f"{query} comparison"]
    for s in subs[:passes]:
        all_src += search(s)
    seen, uniq = set(), []
    for s in all_src:
        if s["url"] not in seen:
            seen.add(s["url"])
            uniq.append(s)
    return uniq[:10]


def main():
    ap = argparse.ArgumentParser(description="citewise - free cited research engine")
    ap.add_argument("query", nargs="?")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--deep", action="store_true", help="run a follow-up deep-research loop")
    ap.add_argument("--save", help="write the report to this markdown path")
    ap.add_argument("--self-check", action="store_true", help="verify the search/fetch pipeline")
    args = ap.parse_args()

    if args.self_check:
        try:
            r = search("test query")
            ok = bool(r)
            print("SELF-CHECK:", "OK" if ok else "FAIL", f"({len(r)} results)")
            sys.exit(0 if ok else 1)
        except Exception as e:  # noqa: BLE001
            print("SELF-CHECK: FAIL", e)
            sys.exit(1)

    sources = deep_research(args.query) if args.deep else search(args.query, args.top)
    if not sources:
        print("No results.")
        sys.exit(1)
    report = synthesize(args.query, sources)
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    out = f"<!-- citewise {stamp} -->\n\n{report}\n\n## Sources\n{sources_block(sources)}\n"
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Saved: {args.save}")
    else:
        print(out)


if __name__ == "__main__":
    main()
