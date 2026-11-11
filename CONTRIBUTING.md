# Contributing

Thanks for helping make newsletters less overwhelming. Small, focused changes
are easiest to review.

## Good first contributions

- **A sample profile** for a new topic in `examples/profiles/` (teachers,
  lawyers, climbers, local politics…). Keep it fictional: no real people.
- **A theme** for `web/index.html`: one CSS variable block plus its name in
  `CONFIG.themes`. Check that text is readable in it and that it works at phone
  width.
- **Setup notes** for an AI app in `docs/models.md`.
- **Translations** of the prompts.

## Bigger ideas we'd love

- Fetching RSS feeds and sites from the profile in `scripts/run_brief.py`
  (standard library only, please).
- Reading newsletters straight from an IMAP inbox, read-only.
- An archive view in the reader page.

## Changing the brief's shape

The prompt, the schema and the page have to agree. If you add or rename a
field:

1. Update both prompts in `prompts/` (the JSON example and the instructions).
2. Update `schema/brief.schema.json` and/or `schema/recap.schema.json`.
3. Update `samples/`, then run `python3 scripts/embed_demo.py` so the page's
   built-in demo matches.
4. Teach `web/index.html` to show it, using the `el()` helper so text is never
   inserted as HTML.
5. Bump `schema_version` if old briefs would no longer load.

Check your samples against the schema:

```bash
python3 -m pip install jsonschema
python3 -c "import json,jsonschema; jsonschema.validate(json.load(open('samples/brief.sample.json')), json.load(open('schema/brief.schema.json'))); print('ok')"
```

## Ground rules

- **The honesty rules in the prompts stay.** Changes that make the brief more
  fun are welcome; changes that loosen "only report what a source says" or the
  prompt-injection rule are not.
- **No personal data** in issues, pull requests, samples or screenshots. Blur
  your inbox.
- **No new dependencies** for the page or the script unless there's no other way.
- Be kind in reviews.
