#!/usr/bin/env python3
"""Make today's brief (or this week's recap) with any LLM API.

No packages to install: this uses only Python's standard library.

Quick start
    1. Put newsletter text in inbox/ (paste emails into .txt or .md files,
       or save them as .eml or .html).
    2. Pick a provider and set its key (see .env.example):
           export BRIEF_PROVIDER=anthropic      # or: openai
           export BRIEF_API_KEY=...             # your key, never commit it
           export BRIEF_MODEL=...               # see docs/models.md
    3. Run:
           python3 scripts/run_brief.py                 # daily brief
           python3 scripts/run_brief.py --mode weekly   # weekly recap
    4. Open web/index.html (see README for the one-line local server).

Providers
    anthropic  Claude, through the Anthropic Messages API.
    openai     Anything with an OpenAI-compatible /chat/completions endpoint:
               OpenAI, Google Gemini, xAI Grok, Mistral, Groq, OpenRouter,
               and local models through Ollama or LM Studio.
               Set BRIEF_BASE_URL for anything that isn't OpenAI itself.
"""
import argparse
import datetime as dt
import email
import email.policy
import html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED = {"daily": ["schema_version", "type", "date", "vibe", "tldr", "stories"],
            "weekly": ["schema_version", "type", "date", "week_of", "vibe", "tldr", "stories"]}
PROMPTS = {"daily": "prompts/daily-brief.md", "weekly": "prompts/weekly-recap.md", "plain": "prompts/plain-text.md"}
DEFAULT_MODELS = {"anthropic": "claude-opus-5-5"}  # other providers: set BRIEF_MODEL
SOURCE_WARN_CHARS = 400_000
OLLAMA_ANSWER_ROOM = 4000  # tokens to leave free for the brief itself (and any "thinking")


def die(msg):
    sys.exit("error: " + msg)


def load_dotenv(path):
    """Read KEY=value lines from .env without overriding real env vars."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def prompt_body(path):
    """The prompt file has setup notes above a '---' line; the model gets what's below it."""
    text = (ROOT / path).read_text(encoding="utf-8")
    parts = re.split(r"^---\s*$", text, maxsplit=1, flags=re.M)
    return parts[1].strip() if len(parts) == 2 else text


def html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"[ \t]+", " ", html.unescape(raw))


def read_eml(path):
    msg = email.message_from_bytes(path.read_bytes(), policy=email.policy.default)
    head = "From: %s\nSubject: %s\nDate: %s\n" % (msg.get("from", ""), msg.get("subject", ""), msg.get("date", ""))
    body = msg.get_body(preferencelist=("plain", "html"))
    text = body.get_content() if body else ""
    if body is not None and body.get_content_type() == "text/html":
        text = html_to_text(text)
    return head + "\n" + text


def gather_inbox(folder, since_days, only=None):
    """Collect newsletter text from the inbox folder, newest first."""
    if not folder.exists():
        return []
    cutoff = dt.datetime.now().timestamp() - since_days * 86400
    items = []
    for p in sorted(folder.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
        if not p.is_file() or p.name.startswith(".") or p.name.lower() == "readme.md" or p.stat().st_mtime < cutoff:
            continue
        if only and not p.name.endswith(only):
            continue
        ext = p.suffix.lower()
        try:
            if ext == ".eml":
                text = read_eml(p)
            elif ext in (".html", ".htm"):
                text = html_to_text(p.read_text(encoding="utf-8", errors="replace"))
            elif ext in (".txt", ".md", ".json"):
                text = p.read_text(encoding="utf-8", errors="replace")
            else:
                continue
        except Exception as e:  # one unreadable file shouldn't stop the brief
            print("skipped %s (%s)" % (p.name, e), file=sys.stderr)
            continue
        items.append((p.name, text.strip()))
    return items


def source_block(items):
    # Each item is fenced, and any closing tag inside it is broken up, so a
    # newsletter can't end the <source_material> block early.
    out = []
    for name, text in items:
        text = re.sub(r"(?i)</?\s*source_material\s*>", "[tag removed]", text)
        out.append('<document name="%s">\n%s\n</document>' % (html.escape(name), text))
    return "\n\n".join(out)


def build_prompt(mode, profile_text, source_text, today):
    body = prompt_body(PROMPTS["plain" if mode.startswith("plain") else mode])
    body = body.replace("{{PROFILE}}", profile_text.strip())
    body = body.replace("{{TODAY}}", today)
    body = body.replace("{{MODE}}", mode.replace("plain-", ""))
    return body.replace("{{SOURCE_MATERIAL}}", source_text or "(none provided: use your own tools if you have them)")


def post(url, headers, payload, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"content-type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:800]
        die("the API said %s: %s" % (e.code, detail))
    except urllib.error.URLError as e:
        die("could not reach %s (%s)" % (url, e.reason))


def call_anthropic(prompt, model, key, timeout):
    base = os.environ.get("BRIEF_BASE_URL", "https://api.anthropic.com").rstrip("/")
    data = post(base + "/v1/messages",
                {"x-api-key": key, "anthropic-version": "2023-06-01"},
                {"model": model, "max_tokens": 16000,
                 "messages": [{"role": "user", "content": prompt}]}, timeout)
    if data.get("stop_reason") == "refusal":
        die("the model declined this request. Check the source material for anything unusual.")
    if data.get("stop_reason") == "max_tokens":
        print("warning: the answer hit the length limit and may be cut off", file=sys.stderr)
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def call_openai_compatible(prompt, model, key, timeout):
    base = os.environ.get("BRIEF_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    headers = {"authorization": "Bearer " + key} if key else {}
    data = post(base + "/chat/completions", headers,
                {"model": model, "messages": [{"role": "user", "content": prompt}]}, timeout)
    try:
        answer = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        die("unexpected answer shape from %s: %s" % (base, json.dumps(data)[:500]))
    check_ollama_context(base, model, (data.get("usage") or {}).get("prompt_tokens"))
    return answer


def check_ollama_context(base, model, prompt_tokens):
    """Ollama gives models a small context window by default (4,096 tokens on
    many machines) and quietly cuts anything longer, so warn when it's too small."""
    if not prompt_tokens or not (":11434" in base or "ollama" in base.lower()):
        return
    root = re.sub(r"/v1/?$", "", base)
    try:
        with urllib.request.urlopen(root + "/api/ps", timeout=5) as r:
            loaded = json.loads(r.read().decode("utf-8")).get("models", [])
    except Exception:  # not Ollama after all, or an older version: nothing to check
        return
    for m in loaded:
        ctx = m.get("context_length")
        if m.get("name") in (model, model + ":latest") and ctx and ctx < prompt_tokens + OLLAMA_ANSWER_ROOM:
            print("\nwarning: Ollama ran %s with a %d-token context window, but the prompt alone was %d tokens\n"
                  "and the answer needs about %d more. Ollama cuts the rest without telling you, so\n"
                  "newsletters (and the rules) were probably dropped. Fix: quit Ollama and start it with\n"
                  "    OLLAMA_CONTEXT_LENGTH=%d ollama serve\n"
                  "or raise \"Context length\" in the Ollama app's settings. See docs/models.md.\n"
                  % (model, ctx, prompt_tokens, OLLAMA_ANSWER_ROOM, suggest_context(prompt_tokens)), file=sys.stderr)


def suggest_context(prompt_tokens):
    size = 8192
    while size < prompt_tokens + OLLAMA_ANSWER_ROOM:
        size *= 2
    return max(size, 16384)


def extract_json(text):
    """Pull the JSON object out even if the model added fences or a sentence."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in the answer")
    return json.loads(text[start:end + 1])


def check(data, mode):
    missing = [k for k in REQUIRED[mode] if k not in data]
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))
    if data.get("type") != mode:
        raise ValueError('expected type "%s", got "%s"' % (mode, data.get("type")))
    if len(data.get("tldr", [])) != 3:
        print("warning: tldr should have exactly 3 items", file=sys.stderr)
    try:  # full schema check only if the optional jsonschema package is around
        import jsonschema
        schema = json.loads((ROOT / "schema" / ("brief" if mode == "daily" else "recap")).with_suffix(".schema.json").read_text())
        jsonschema.validate(data, schema)
    except ImportError:
        pass
    except Exception as e:
        print("warning: schema check: %s" % str(e).splitlines()[0], file=sys.stderr)
    return data


def main():
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser(description="Turn your newsletters into one brief with any LLM.")
    ap.add_argument("--mode", choices=["daily", "weekly", "plain-daily", "plain-weekly"], default="daily")
    ap.add_argument("--profile", default=str(ROOT / "profile.yaml"))
    ap.add_argument("--inbox", default=str(ROOT / "inbox"), help="folder of newsletter text")
    ap.add_argument("--out", help="where to write the JSON (default web/brief.json or web/recap.json)")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true", help="print the prompt and stop; no API call")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    profile = pathlib.Path(args.profile)
    if not profile.exists():
        die("no profile at %s. Copy profile.yaml or an example from examples/profiles/." % profile)
    weekly = args.mode.endswith("weekly")
    items = gather_inbox(pathlib.Path(args.inbox), 7 if weekly else 1.5)
    if weekly:  # this week's daily briefs make great recap input
        items += gather_inbox(ROOT / "archive", 7, only="-daily.json")
    src = source_block(items)
    if len(src) > SOURCE_WARN_CHARS:
        print("warning: %d characters of source material. If the API rejects it as too long, "
              "move older files out of inbox/." % len(src), file=sys.stderr)
    prompt = build_prompt(args.mode, profile.read_text(encoding="utf-8"), src, args.date)

    if args.dry_run:
        print(prompt)
        print("\n--- %d source files, %d characters of prompt ---" % (len(items), len(prompt)), file=sys.stderr)
        return

    provider = os.environ.get("BRIEF_PROVIDER", "anthropic").lower()
    if provider not in ("anthropic", "openai"):
        die('BRIEF_PROVIDER must be "anthropic" or "openai"')
    key = os.environ.get("BRIEF_API_KEY", "")
    model = os.environ.get("BRIEF_MODEL") or DEFAULT_MODELS.get(provider)
    if not model:
        die("set BRIEF_MODEL to the model name from your provider (see docs/models.md)")
    if provider == "anthropic":
        if not key:
            die("set BRIEF_API_KEY to your Anthropic API key")
        answer = call_anthropic(prompt, model, key, args.timeout)
    elif provider == "openai":
        answer = call_openai_compatible(prompt, model, key, args.timeout)
    else:
        die('BRIEF_PROVIDER must be "anthropic" or "openai"')

    if args.mode.startswith("plain"):
        print(answer)
        return
    try:
        data = check(extract_json(answer), args.mode)
    except ValueError as e:
        bad = ROOT / "archive" / ("failed-%s.txt" % args.date)
        bad.parent.mkdir(exist_ok=True)
        bad.write_text(answer, encoding="utf-8")
        die("%s. The raw answer is saved at %s" % (e, bad.relative_to(ROOT)))

    out = pathlib.Path(args.out) if args.out else ROOT / "web" / ("recap.json" if weekly else "brief.json")
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    arch = ROOT / "archive" / ("%s-%s.json" % (args.date, args.mode))
    arch.parent.mkdir(exist_ok=True)
    arch.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote %s (%d stories) and %s" % (out.relative_to(ROOT) if out.is_relative_to(ROOT) else out,
                                            len(data.get("stories", [])), arch.relative_to(ROOT)))


if __name__ == "__main__":
    main()
