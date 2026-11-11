# Running All My Newsletters with your AI

The profile and prompts are the same everywhere. What changes is how the AI
gets your newsletters and how the result reaches you. App features get renamed
often, so if a menu below has moved, look for words like *project*,
*instructions*, *connectors*, *apps*, *scheduled* or *tasks*.

## The one-time setup (any chat app)

1. Paste `prompts/daily-brief.md` (everything below the `---` line) into a new chat.
2. Replace `{{PROFILE}}` with your profile and `{{TODAY}}` with today's date.
3. If the AI can read your email or the web, delete the `<source_material>`
   block. If it can't, paste today's newsletters inside it.
4. Copy the JSON answer into `web/index.html` → **Load**.

Save steps 1 and 2 as reusable instructions so you don't repeat them. Most apps
have a place for this: a **Project** with instructions (Claude, ChatGPT), a
**custom GPT**, a **Gem** (Gemini), or a **Space** (Perplexity). In the
instructions, say "When I say *brief me*, follow the daily prompt for today's
date" and "When I say *recap*, follow the weekly prompt."

## Letting the AI read your newsletters

The brief is only as good as what the AI can read.

- **Email access.** Several apps can connect to Gmail or Outlook (look for
  connectors, apps or extensions). Once connected, the AI can search for your
  newsletters by name, as listed in `sources.newsletters`. Give it read access
  only; it never needs to send mail for this.
- **Web search.** Lets the AI read the sites in `sources.sites` and confirm
  stories it saw in a newsletter. Turn it on if your app has it.
- **Neither?** Paste the newsletters in. Many newsletters have a "view in
  browser" link; copying that page's text works well.
- **A dedicated inbox.** Some people forward newsletters to a separate address,
  or subscribe with one, so the AI only ever sees newsletters.

## Getting it every morning without asking

- **Scheduled tasks in a chat app.** Some apps (versions of this exist in
  ChatGPT, Gemini, Grok, Perplexity and Claude) can run a prompt on a schedule
  and notify you. Use `prompts/plain-text.md` with `{{MODE}}` set to `daily`,
  since a notification can't render the reader page. Schedule the recap for
  Friday afternoon with `{{MODE}}` set to `weekly`.
- **The script on a timer.** `scripts/run_brief.py` plus cron (macOS, Linux)
  or Task Scheduler (Windows). See the README.

## The script with each provider

Set these in `.env` (copy `.env.example`). Use the exact model name from your
provider's docs; model names change, so this guide doesn't list them.

| Provider | `BRIEF_PROVIDER` | `BRIEF_BASE_URL` | Key |
| --- | --- | --- | --- |
| Anthropic (Claude) | `anthropic` | leave empty | Anthropic Console API key. `BRIEF_MODEL` defaults to `claude-opus-5-5` |
| OpenAI | `openai` | leave empty | OpenAI API key |
| Google Gemini | `openai` | `https://generativelanguage.googleapis.com/v1beta/openai` | Google AI Studio key |
| xAI Grok | `openai` | `https://api.x.ai/v1` | xAI API key |
| OpenRouter (many models) | `openai` | `https://openrouter.ai/api/v1` | OpenRouter key |
| Ollama (local) | `openai` | `http://localhost:11434/v1` | leave empty |
| LM Studio (local) | `openai` | `http://localhost:1234/v1` | leave empty |

Check your provider's docs for its current OpenAI-compatible address if one of
these has moved.

### Local models: give them enough context first

Local apps give models a small working memory (the "context window") by
default, often 4,096 tokens. The prompt and your profile alone are about
2,500 tokens, so with a few newsletters added the end gets cut off **without
any error**, and the brief quietly misses stories and rules. Set it to at
least 16,384 tokens (32,768 if you paste a lot of newsletters):

- **Ollama:** quit Ollama, then start it with
  `OLLAMA_CONTEXT_LENGTH=16384 ollama serve`, or raise **Context length** in
  the Ollama app's settings. The script warns you if Ollama's window was too
  small for that run.
- **LM Studio:** set **Context Length** when you load the model (in the
  model's load settings), then reload it.

### Tips for smaller and local models

- Shorter is easier. Set `brief.max_stories` to 3 or 4.
- Trim `inbox/` to the newsletters that matter most; small models have small
  context windows.
- If the JSON keeps breaking, use `--mode plain-daily` and read it as text.
- Local models can't browse. Everything they know comes from `inbox/`.

## Accuracy check

Whatever model you use, spot-check the first few briefs: open two or three
source links and make sure the summary matches the page. If a model invents
details, try a larger model or paste the newsletters in rather than relying on
its tools.
