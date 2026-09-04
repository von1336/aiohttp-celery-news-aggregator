import asyncio
import logging
from datetime import datetime

from app.database import SessionLocal
from app.models import Source, Article
from app.parser import NewsParser

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def fetch_news():
    session = SessionLocal()
    try:
        sources = session.query(Source).filter(Source.is_active == True).all()
        if not sources:
            logger.info("No active sources to fetch")
            return {"fetched": 0, "sources": 0, "new_articles": 0}

        source_list = [(s.id, s.url) for s in sources]
        result = asyncio.run(NewsParser.fetch_all_sources(source_list))

        total_new = 0
        for source in sources:
            articles = result.get(source.id, [])
            new_count = 0
            for item in articles:
                existing = session.query(Article).filter(Article.link == item["link"]).first()
                if not existing:
                    article = Article(
                        source_id=source.id,
                        title=item["title"],
                        link=item["link"],
                        summary=item.get("summary"),
                        published_at=item.get("published_at"),
                    )
                    session.add(article)
                    new_count += 1
            source.last_fetched_at = datetime.utcnow()
            total_new += new_count
            logger.info("Source %s: fetched %d, new %d", source.name, len(articles), new_count)

        session.commit()
        logger.info("Fetch completed: %d new articles from %d sources", total_new, len(sources))
        return {"fetched": sum(len(result.get(s.id, [])) for s in sources), "sources": len(sources), "new_articles": total_new}
    except Exception as e:
        session.rollback()
        logger.exception("Fetch failed: %s", e)
        raise
    finally:
        session.close()
