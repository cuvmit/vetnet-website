#!/usr/bin/env python3
"""Check the built site in output/ (standard library plus the project's data loader).

Fails with a readable list when:
  - an internal link or asset doesn't resolve, or an #anchor has no matching id
  - a page lacks <title>, exactly one <h1>, or <html lang>
  - a page has href="#", a "[bracketed]" placeholder outside class="placeholder",
    or loads CSS, JS, fonts or images from another host
  - the Home stats don't match the YAML data
Run with: make check
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"

sys.path.insert(0, str(ROOT / "plugins"))

SKIP_SCHEMES = ("http:", "https:", "mailto:", "tel:", "javascript:", "data:")
VOID = {"meta", "link", "img", "input", "br", "hr", "source", "area", "base", "col", "embed", "param", "track", "wbr"}
TEXT_SKIP_TAGS = {"script", "style", "code", "pre", "title"}

errors = []


def fail(page, message):
    errors.append(f"{page}: {message}")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = set()
        self.links = []  # (kind, url)
        self.external_assets = []
        self.h1 = 0
        self.has_title = False
        self.title_text = ""
        self.html_lang = None
        self.bare_hash = 0
        self.bracket_text = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag not in VOID:
            self.stack.append((tag, classes))
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag == "title":
            self.has_title = True
            self._in_title = True
        if tag == "h1":
            self.h1 += 1
        if tag == "a" and "href" in a:
            if a["href"] == "#":
                self.bare_hash += 1
            self.links.append(("href", a["href"]))
        if tag == "link" and a.get("href"):
            self.links.append(("asset", a["href"]))
            if a["href"].startswith(("http://", "https://")) and a.get("rel") not in ("canonical",):
                self.external_assets.append(a["href"])
        if tag in ("script", "img", "source") and a.get("src"):
            self.links.append(("asset", a["src"]))
            if a["src"].startswith(("http://", "https://")):
                self.external_assets.append(a["src"])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._in_title:
            self.title_text += data
        if "[" not in data:
            return
        for tag, classes in self.stack:
            if tag in TEXT_SKIP_TAGS or "placeholder" in classes:
                return
        self.bracket_text.append(data.strip())


def resolve(page_file, url):
    """Return the file an internal URL points to, or None if it can't be found."""
    path = unquote(urlparse(url).path)
    if not path:
        return page_file
    base = OUTPUT if path.startswith("/") else page_file.parent
    target = (base / path.lstrip("/")).resolve() if path.startswith("/") else (base / path).resolve()
    if target.is_dir() or path.endswith("/"):
        target = target / "index.html"
    return target if target.is_file() else None


def check_pages():
    pages = sorted(OUTPUT.rglob("*.html"))
    parsed = {}
    for f in pages:
        p = PageParser()
        p.feed(f.read_text(encoding="utf-8"))
        parsed[f.resolve()] = p

    for f in pages:
        rel = f.relative_to(OUTPUT).as_posix()
        p = parsed[f.resolve()]
        if not p.has_title or not p.title_text.strip():
            fail(rel, "missing <title>")
        if p.h1 != 1:
            fail(rel, f"expected exactly one <h1>, found {p.h1}")
        if not p.html_lang:
            fail(rel, "<html> has no lang attribute")
        if p.bare_hash:
            fail(rel, f'{p.bare_hash} link(s) with href="#"')
        for text in p.bracket_text:
            fail(rel, f'bracketed text outside class="placeholder": "{text[:60]}"')
        for url in p.external_assets:
            fail(rel, f"loads an external resource: {url}")

        for kind, url in p.links:
            if url.startswith(SKIP_SCHEMES):
                continue
            target = resolve(f, url)
            if target is None:
                fail(rel, f"broken {kind}: {url}")
                continue
            fragment = urlparse(url).fragment
            if fragment and kind == "href":
                other = parsed.get(target)
                if other is None or fragment not in other.ids:
                    fail(rel, f"anchor not found: {url}")


def check_css():
    for css in sorted(OUTPUT.rglob("*.css")):
        text = css.read_text(encoding="utf-8")
        for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)", text):
            url = m.group(1)
            if url.startswith("data:"):
                continue
            rel = css.relative_to(OUTPUT).as_posix()
            if url.startswith(("http://", "https://", "//")):
                fail(rel, f"loads an external resource: {url}")
            elif not (css.parent / url).resolve().is_file():
                fail(rel, f"missing file referenced by url(): {url}")


def check_files():
    for name in ("index.html", "sitemap.xml", "robots.txt", "favicon.svg"):
        if not (OUTPUT / name).is_file():
            fail("output", f"missing {name}")
    if (OUTPUT / "home").exists():
        fail("output", "unexpected home/ directory (home page should be index.html)")
    for name in ("portal", "members"):
        sitemap = OUTPUT / "sitemap.xml"
        if sitemap.is_file() and f"/{name}/" in sitemap.read_text(encoding="utf-8"):
            fail("sitemap.xml", f"preview page /{name}/ should not be listed")


def check_home_stats():
    from vetnet_data import DataError, load_data

    import os

    os.chdir(ROOT)
    try:
        stats = load_data()["stats"]
    except DataError as exc:
        fail("data", str(exc))
        return
    html = (OUTPUT / "index.html").read_text(encoding="utf-8")
    found = re.findall(r'<span class="stat-value">(.*?)</span><span class="stat-label">(.*?)</span>', html)
    values = {re.sub(r"<.*?>", "", label).split(" ·")[0].replace("&amp;", "&"): value for value, label in found}
    expected = {
        "Collaborators": str(stats["collaborators_total"]),
        "Partner universities": str(stats["universities"]),
        "Industry & other partners": str(stats["industry_other"]),
        "Datasets": str(stats["datasets"]) if stats["datasets"] else "—",
        "Publication": str(stats["publications"]),
    }
    for label, want in expected.items():
        key = label if label in values else label + "s"
        if values.get(key) != want:
            fail("index.html", f"stat '{label}' is {values.get(key)!r}, expected {want!r}")
    tiles = len(re.findall(r'class="partner-tile', html))
    if tiles != stats["organizations"]:
        fail("index.html", f"{tiles} partner tiles, expected {stats['organizations']}")
    people = (OUTPUT / "people" / "index.html").read_text(encoding="utf-8")
    cards = len(re.findall(r'<article class="person-card', people))
    pis = len(re.findall(r'<article class="pi-card', people))
    if cards != stats["collaborators"] or pis != stats["pis"]:
        fail("people/index.html", f"{cards} collaborator and {pis} PI cards, expected {stats['collaborators']} and {stats['pis']}")


def main():
    if not OUTPUT.is_dir():
        print("output/ not found. Run `make build` first.", file=sys.stderr)
        return 2
    check_files()
    check_pages()
    check_css()
    check_home_stats()
    count = len(list(OUTPUT.rglob("*.html")))
    if errors:
        print(f"Site check FAILED ({len(errors)} problem(s) in {count} pages):\n")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"Site check passed: {count} pages, no problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
