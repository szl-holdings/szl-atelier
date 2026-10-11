"""The closed publication map must deliver the exact native projection."""
from __future__ import annotations

import base64
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "frontier/atelier_v3"


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))


def test_embedded_assets_match_immutable_native_provenance():
    manifest = json.loads((ROOT / "docs/NATIVE_PRESENTATION.json").read_text())
    assets = {item["name"]: item for item in manifest["assets"]}
    css = (FRONT / "static/styles.css").read_bytes()
    token_bytes = css.split(b"/* SZL-NATIVE-TOKENS:START */\n", 1)[1].split(b"/* SZL-NATIVE-TOKENS:END */", 1)[0]
    assert hashlib.sha256(token_bytes).hexdigest() == assets["kanchay-tokens"]["sha256"]
    parser = Images()
    parser.feed((FRONT / "static/index.html").read_text())
    assert len(parser.images) == 1
    image = parser.images[0]
    assert image["width"] == image["height"] == "32"
    assert image["alt"] == ""  # Adjacent literal identity owns the accessible name.
    data = base64.b64decode(image["src"].removeprefix("data:image/svg+xml;base64,"), validate=True)
    assert hashlib.sha256(data).hexdigest() == assets["orbit-v2-icon-32"]["sha256"]
    assert b'padding: 8px' in css


def test_native_projection_needs_no_new_publication_slot_or_external_dependency():
    publication = json.loads((FRONT / "PUBLICATION.json").read_text())
    serialized = json.dumps(publication)
    for path in ("static/index.html", "static/styles.css", "static/app.js"):
        assert path in serialized
    html = (FRONT / "static/index.html").read_text()
    assert not re.search(r"https?://", html)
    assert '<ul class="constellation"' in html
    assert '<noscript>' in html and 'href="/api/catalog"' in html
    assert 'href="/api/source"' in html


def test_existing_asset_routes_are_versioned_by_the_exact_shipped_bytes():
    html = (FRONT / "static/index.html").read_text()
    for filename, attribute in (("styles.css", "href"), ("app.js", "src")):
        urls = re.findall(rf'{attribute}="(/{re.escape(filename)}[^\"]*)"', html)
        assert len(urls) == 1
        url = urlsplit(urls[0])
        assert url.path == f"/{filename}" and not url.netloc and not url.fragment
        assert parse_qs(url.query) == {
            "v": [hashlib.sha256((FRONT / "static" / filename).read_bytes()).hexdigest()]
        }
