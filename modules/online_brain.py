"""Простейший онлайн-модуль: поиск и извлечение текста с нескольких сайтов."""

import re
import textwrap
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup  # pip install beautifulsoup4


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str


class OnlineBrain:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    # ====== Внешний интерфейс ======

    def answer(self, query: str) -> str:
        """
        Попробовать найти ответ онлайн и вернуть короткий конспект.
        Сейчас: гугл-поиск + извлечение текста с первой подходящей страницы.
        """
        try:
            results = self.search_google(query)
            if not results:
                return "Я попробовал поискать в сети, но ничего полезного не нашёл."

            best = results[0]
            text = self.fetch_and_summarize(best.url)

            if not text:
                return f"Нашёл что-то по запросу: {best.title} ({best.url}), но не смог аккуратно извлечь текст."

            return text
        except Exception:
            # В проде логировать, здесь просто fallback
            return "Во время онлайн-поиска произошла ошибка. Давай попробуем сформулировать вопрос иначе?"

    # ====== Google-поиск (упрощённо) ======

    def search_google(self, query: str, num: int = 3) -> List[SearchResult]:
        """
        Очень простой поиск через HTML Google.
        Для серьёзного проекта лучше использовать оф. API.
        """
        params = {"q": query, "hl": "ru"}
        resp = self.session.get("https://www.google.com/search", params=params, timeout=self.timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[SearchResult] = []

        for g in soup.select("div.g"):
            a = g.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            url = a["href"]

            # фильтрация по доменам, которые ты перечислил
            if not self._allowed_domain(url):
                continue

            snippet_el = g.find("span", class_="aCOpRe") or g.find("div", class_="VwiC3b")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            results.append(SearchResult(url=url, title=title, snippet=snippet))

            if len(results) >= num:
                break

        return results

    def _allowed_domain(self, url: str) -> bool:
        allowed = [
            "github.com",
            "stackoverflow.com",
            "royallib.com",
            "bookscafe.net",
            "arxiv.org",
            "researchgate.net",
            "edx.org",
            "developer.mozilla.org",
            "w3schools.com",
            "devdocs.io",
            "proofwiki.org",
            "mathworld.wolfram.com",
            "engineeringtoolbox.com",
            "allaboutcircuits.com",
        ]
        return any(domain in url for domain in allowed)

    # ====== Извлечение текста и краткий конспект ======

    def fetch_and_summarize(self, url: str, max_chars: int = 600) -> Optional[str]:
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Убираем скрипты/стили
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Простой текст из параграфов
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = " ".join(paragraphs)
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return None

        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        wrapped = textwrap.fill(text, width=80)
        return f"Вот кратко из сети:\n{wrapped}\n\nИсточник: {url}"
