import asyncio
from datetime import datetime
from time import struct_time
from typing import Optional

import aiohttp
import feedparser


class NewsParser:
    @staticmethod
    async def fetch_feed(session: aiohttp.ClientSession, url: str) -> Optional[str]:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return text[:1_000_000]
        except Exception:
            pass
        return None

    @staticmethod
    def parse_feed(raw_xml: str) -> list[dict]:
        if not raw_xml:
            return []

        parsed = feedparser.parse(raw_xml)
        articles = []

        for entry in parsed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                t = entry.published_parsed
                published = datetime(*t[:6]) if isinstance(t, struct_time) else None

            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:2000] if entry.get("summary") else None,
                "published_at": published,
            })

        return articles

    @classmethod
    async def fetch_all_sources(
        cls, sources: list[tuple[int, str]]
    ) -> dict[int, list[dict]]:
        result = {}

        connector = aiohttp.TCPConnector(ssl=True, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [(source_id, cls.fetch_feed(session, url)) for source_id, url in sources]
            fetched = await asyncio.gather(*[t[1] for t in tasks])

            for (source_id, _), raw_xml in zip(tasks, fetched):
                result[source_id] = cls.parse_feed(raw_xml) if raw_xml else []

        return result
