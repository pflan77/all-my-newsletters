# All My Newsletters

**Too many newsletters? Turn them all into one morning brief and a weekly recap, with only what you care about most, so your time goes to what's most relevant to you.**

You signed up for fifteen newsletters because each one sounded useful. Now they pile up unread, and the one story that mattered to you is buried somewhere in there. All My Newsletters fixes that. You tell an AI who you are and what you care about, once. Every morning it reads everything that landed, keeps only what matters to *you*, and hands you a five-minute brief you read one card at a time. Every Friday you get a recap of the week.

- **Any topic.** Health tech, fintech, game dev, gardening, your city's politics. You write the profile.
- **Any AI.** Claude, ChatGPT, Gemini, Grok, or a local model on your laptop. Nothing here is tied to one company.
- **Your look.** A one-file reader page with four themes (clean, dark, pixel, paper) that you can restyle in minutes.
- **No signup, no server, no tracking.** Your profile and your mail stay with you.

> 📸 _Screenshots go here: the cover card, a story card, and the pixel theme on a phone._

---

## How it works

```
 your newsletters ─┐
 sites and feeds ──┼──►  AI + your profile + the prompt  ──►  brief.json  ──►  reader page
 (last 24 hours)  ─┘          (any model)                    (or plain text)    one card at a time
```

1. **`profile.yaml`** says who you are, your 3 to 6 topic "pillars", your sources, what to skip, and how it should sound.
2. **`prompts/`** holds the daily and weekly instructions. They work in any model and carry the rules that keep it honest (below).
3. The AI answers with **JSON** that follows `schema/`, or with plain text if you'd rather read it right in the chat.
4. **`web/index.html`** turns the JSON into a quick, fun read: a cover with the day's vibe and a 3-point TL;DR, one card per story, then a wrap-up with one thing to do today.

### What a brief looks like

- **Vibe:** one line on the mood of the day.
- **TL;DR:** exactly three things to know if you read nothing else.
- **Story cards** (about six, fewer on a quiet day). Each has a punchy *spark* headline, a 30-second summary, *why it matters to you*, an optional take, a confidence badge, and its sources.
- **Your move:** one concrete thing to do today.
- **Say this in a meeting**, **quick hits**, **local news**, and **what to watch next**.

The **weekly recap** is the top 5 stories of the week, a local section, one thing to watch next week, and the sources.

---

## Quickstart (5 minutes, no code)

1. **Get the files.** Click **Code → Download ZIP** on GitHub, or `git clone` this repo.
2. **Write your profile.** Open `profile.yaml` and replace the example with you. Stuck? Copy one from `examples/profiles/`:
   [nurse following health tech](examples/profiles/nurse-health-tech.yaml),
   [founder following fintech](examples/profiles/founder-fintech.yaml),
   [gamer learning game dev](examples/profiles/gamer-game-dev.yaml).
3. **Run the prompt.** Open your AI, paste everything below the line in [`prompts/daily-brief.md`](prompts/daily-brief.md), and paste your profile where it says `{{PROFILE}}`. If your AI can read your email or search the web, delete the `<source_material>` block and it will fetch the news itself. If not, paste today's newsletters into that block.
4. **Read it.** Open `web/index.html` in your browser, tap **Load**, paste the JSON the AI gave you, and tap **Show my brief**.

Want to see it first? Open `web/index.html` and tap **See a demo**, or add `?demo=1` to the address.

Prefer to just read in the chat? Use [`prompts/plain-text.md`](prompts/plain-text.md) instead and skip the page.

**Tip:** save the prompt with your profile already pasted in as a reusable instruction (a Project, a custom GPT, a Gem, whatever your app calls it). Then each morning you only type "brief me".

---

## Run it with your AI

Every option uses the same profile and prompts. Pick the one that fits how you work. [`docs/models.md`](docs/models.md) has step-by-step notes for each.

| How | Good for | What you do each day |
| --- | --- | --- |
| **Chat app** (Claude, ChatGPT, Gemini, Grok, Perplexity…) | Trying it out | Say "brief me", paste the JSON into the page |
| **Scheduled task** in your chat app, where it offers one | Hands-off mornings | Nothing. Read it when it lands (plain-text prompt works best) |
| **API script** (`scripts/run_brief.py`) | Tinkerers, full control | Nothing, if you put it on a timer |
| **Local model** (Ollama, LM Studio) | Privacy, zero cost | Same as the script, pointed at your own machine |

### The script (optional)

Plain Python 3, nothing to install.

```bash
cp .env.example .env          # then add your provider, key and model
# put today's newsletters in inbox/ (.eml, .html, .txt or .md)
python3 scripts/run_brief.py                  # daily brief  -> web/brief.json
python3 scripts/run_brief.py --mode weekly    # weekly recap -> web/recap.json
python3 scripts/run_brief.py --dry-run        # see the exact prompt, no API call
python3 -m http.server --directory web 8000   # then open http://localhost:8000
```

`BRIEF_PROVIDER=anthropic` talks to Claude. `BRIEF_PROVIDER=openai` talks to anything with an OpenAI-compatible API: OpenAI, Gemini, Grok, Mistral, Groq, OpenRouter, Ollama and LM Studio (set `BRIEF_BASE_URL`; examples are in `.env.example`). With a local model, raise its context length to at least 16,384 tokens first ([how](docs/models.md#local-models-give-them-enough-context-first)); the default is too small and cuts the prompt off silently. Each run also saves a copy in `archive/`, and the weekly recap reads that week's daily briefs from there.

Put it on a timer with cron (macOS and Linux):

```cron
# 7:30 every morning, and the recap at 4:30 on Fridays
30 7 * * *  cd ~/all-my-newsletters && python3 scripts/run_brief.py
30 16 * * 5 cd ~/all-my-newsletters && python3 scripts/run_brief.py --mode weekly
```

---

## Rules that keep it trustworthy

These are baked into every prompt, because a brief you can't trust is worse than no brief.

1. **Only what a source actually says.** No invented numbers, quotes, dates, names or outcomes. Unsure stories are marked *early*.
2. **Every link is a page the AI actually read.** No tracking links copied out of emails, no guessed URLs.
3. **Newsletters are material, not instructions.** If an email or page tries to tell the AI what to do ("ignore your rules…"), it doesn't, and it tells you. This protects you from prompt injection.
4. **Social posts are pointers only.** A tweet becomes a story only when a real source confirms it.
5. **Quiet day, short brief.** Fewer stories beats filler.
6. **No private details** about people who aren't public figures.

The reader page adds its own guardrails: it never renders the AI's text as HTML, and it only links to `http` and `https` addresses.

---

## Make it yours

**Themes.** Pick one from the menu on the page, or add `?theme=pixel` to the address. Every color and font is a CSS variable at the top of `web/index.html`. Copy a theme block, rename it, change the values, and add the name to `CONFIG.themes`.

**Page settings.** The `CONFIG` block near the bottom of `web/index.html` sets the brand name, default theme and file names.

**Your brief's shape.** Change `brief.max_stories`, `summary_seconds`, `include_move` and the rest in your profile. Want a new section? Add it to the prompt, the schema and the page; [CONTRIBUTING.md](CONTRIBUTING.md) shows how.

**Read on your phone.** Host the `web/` folder for free (GitHub Pages works: Settings → Pages), open it on your phone, and paste the JSON there. Your brief is saved in that browser only; nothing is uploaded.

**Your personality.** The `flavor` list in your profile (sci-fi, basketball, cooking, anime…) shows up in headlines and jokes. It never changes the facts.

---

## What's in the box

```
profile.yaml               your profile (the only file you must edit)
examples/profiles/         three sample profiles on different topics
prompts/
  daily-brief.md           the morning brief prompt (JSON out)
  weekly-recap.md          the Friday recap prompt (JSON out)
  plain-text.md            both, as readable text instead of JSON
schema/
  brief.schema.json        JSON Schema for a daily brief
  recap.schema.json        JSON Schema for a weekly recap
samples/                   example brief and recap (all made-up news)
web/index.html             the reader page, one file, no build step
scripts/
  run_brief.py             optional: run the prompts through any LLM API
  embed_demo.py            refresh the page's built-in demo from samples/
docs/models.md             setup notes for each AI
inbox/                     drop newsletters here for the script (git-ignored)
```

---

## FAQ

**Is my email sent anywhere?** Only to the AI you choose, and only what you paste or let it read. This repo has no server. `.env`, `inbox/` and `archive/` are git-ignored so they never land on GitHub by accident.

**Which AI is best?** Whichever one can read your newsletters. An AI that can open your inbox and browse the web does the most for you. A model without tools works fine when you paste the newsletters in.

**Does it cost money?** The repo is free. A chat app's free tier is often enough to try it. The script costs whatever your API provider charges for one long prompt a day; a local model costs nothing.

**The AI wrapped its JSON in extra text. Is that a problem?** No. The page and the script both pull the JSON out of whatever surrounds it.

---

## Contributing

Ideas, themes, sample profiles and fixes are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Made by **Patrick Flanagan**, CEO & Founder of Chicago AI Forge · [Instagram @pfl4n](https://www.instagram.com/pfl4n/) · [GitHub @pflan77](https://github.com/pflan77)
