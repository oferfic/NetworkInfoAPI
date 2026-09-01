"""Minimal HTML-to-plain-text conversion, stdlib only.

Job boards (Greenhouse, Lever, ...) return posting content as HTML. We only
need readable plain text out of it -- not a faithful render -- so a small
``html.parser.HTMLParser`` subclass is enough and keeps this project free of
a heavy HTML-parsing dependency.
"""

from __future__ import annotations

from html.parser import HTMLParser

_BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "table",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")
        if tag == "li":
            self._chunks.append("- ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        lines = [line.strip() for line in raw.splitlines()]
        # Collapse runs of blank lines down to a single blank line.
        out: list[str] = []
        blank = False
        for line in lines:
            if line:
                out.append(line)
                blank = False
            elif not blank:
                out.append("")
                blank = True
        return "\n".join(out).strip()


def html_to_text(html: str | None) -> str:
    """Strip HTML tags and return readable plain text."""
    if not html:
        return ""
    extractor = _TextExtractor()
    extractor.feed(html)
    extractor.close()
    return extractor.text()
