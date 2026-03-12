import json
from typing import Optional
from bs4 import BeautifulSoup


class HtmlParser:
    """HTML parser wrapper around BeautifulSoup."""

    def __init__(self, html: str, parser: str = "lxml"):
        try:
            self._soup = BeautifulSoup(html, parser)
        except Exception:
            self._soup = BeautifulSoup(html, "html.parser")

    def get_meta_content(self, property_name: str) -> Optional[str]:
        """Retrieve content of og: or name meta tags."""
        tag = self._soup.find("meta", {"property": property_name}) or \
              self._soup.find("meta", {"name": property_name})
        if tag and tag.get("content"):
            return tag["content"]
        return None

    def get_title(self) -> Optional[str]:
        """Retrieve the page <title> text."""
        tag = self._soup.find("title")
        return tag.get_text(strip=True) if tag else None

    def select_all(self, selector: str):
        """Return all elements matching a CSS selector."""
        return self._soup.select(selector)

    def select_one(self, selector: str):
        """Return the first element matching a CSS selector."""
        return self._soup.select_one(selector)

    def get_all_links(self) -> list:
        """Return all href values from anchor tags."""
        return [
            a["href"]
            for a in self._soup.find_all("a", href=True)
        ]

    def get_text_content(self) -> str:
        """Return all visible text content."""
        return self._soup.get_text(separator=" ", strip=True)

    def find_json_ld(self) -> Optional[dict]:
        """Find and parse the first JSON-LD structured data block."""
        for script in self._soup.find_all("script", type="application/ld+json"):
            try:
                return json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
        return None
