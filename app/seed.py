DEFAULT_SOURCES = [
    {"name": "Habr", "url": "https://habr.com/ru/rss/best/daily/"},
    {"name": "Lenta.ru", "url": "https://lenta.ru/rss/news"},
    {"name": "RBC Tech", "url": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"},
]


def seed_sources(session):
    from app.models import Source

    count = session.query(Source).count()
    if count > 0:
        return

    for item in DEFAULT_SOURCES:
        source = Source(name=item["name"], url=item["url"], is_active=True)
        session.add(source)
    session.commit()
