#!/usr/bin/env python3
"""Copy the sample briefs into web/index.html as its built-in demo.

Run this after you edit samples/brief.sample.json or samples/recap.sample.json:

    python3 scripts/embed_demo.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "web" / "index.html"


def compact(path):
    data = json.loads((ROOT / path).read_text(encoding="utf-8"))
    # "</" is escaped so the JSON can never close the <script> tag early.
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


html = PAGE.read_text(encoding="utf-8")
for tag, sample in (("demo-daily", "samples/brief.sample.json"), ("demo-weekly", "samples/recap.sample.json")):
    pattern = re.compile(r'(<script type="application/json" id="%s">)(.*?)(</script>)' % tag, re.S)
    if not pattern.search(html):
        raise SystemExit("Could not find the %s block in web/index.html" % tag)
    html = pattern.sub(lambda m: m.group(1) + compact(sample) + m.group(3), html, count=1)
PAGE.write_text(html, encoding="utf-8")
print("Demo data updated in", PAGE.relative_to(ROOT))
