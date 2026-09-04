from aiohttp import web

from app.config import HOST, PORT
from app.database import init_db, get_session, SessionLocal
from app.models import Source, Article
from app.seed import seed_sources


async def lifespan(app):
    init_db()
    session = SessionLocal()
    try:
        seed_sources(session)
    finally:
        session.close()
    yield


def json_error(message: str, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status)


@web.middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except Exception as e:
        return json_error(str(e), status=500)


def get_db_session():
    return SessionLocal()


# --- Articles ---


async def list_articles(request: web.Request) -> web.Response:
    session = get_db_session()
    try:
        query = session.query(Article).join(Source)

        source_id = request.query.get("source_id")
        if source_id:
            try:
                query = query.filter(Article.source_id == int(source_id))
            except ValueError:
                return json_error("Invalid source_id", 400)

        search = request.query.get("search")
        if search:
            query = query.filter(
                Article.title.ilike(f"%{search}%") | Article.summary.ilike(f"%{search}%")
            )

        total = query.count()

        try:
            limit = min(int(request.query.get("limit", 20)), 100)
            offset = int(request.query.get("offset", 0))
        except ValueError:
            return json_error("Invalid limit or offset", 400)

        articles = query.order_by(Article.published_at.desc().nullslast()).offset(offset).limit(limit).all()

        data = [
            {
                "id": a.id,
                "source_id": a.source_id,
                "source_name": a.source.name,
                "title": a.title,
                "link": a.link,
                "summary": a.summary,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "fetched_at": a.fetched_at.isoformat() if a.fetched_at else None,
            }
            for a in articles
        ]
        return web.json_response({"articles": data, "total": total})
    finally:
        session.close()


async def get_article(request: web.Request) -> web.Response:
    try:
        article_id = int(request.match_info["id"])
    except ValueError:
        return json_error("Invalid article id", 400)
    session = get_db_session()
    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            return json_error("Article not found", 404)
        return web.json_response({
            "id": article.id,
            "source_id": article.source_id,
            "source_name": article.source.name,
            "title": article.title,
            "link": article.link,
            "summary": article.summary,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "fetched_at": article.fetched_at.isoformat() if article.fetched_at else None,
        })
    finally:
        session.close()


# --- Sources ---


async def list_sources(request: web.Request) -> web.Response:
    session = get_db_session()
    try:
        sources = session.query(Source).all()
        data = [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "is_active": s.is_active,
                "last_fetched_at": s.last_fetched_at.isoformat() if s.last_fetched_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sources
        ]
        return web.json_response({"sources": data})
    finally:
        session.close()


async def create_source(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        return json_error("Invalid JSON", 400)

    name = body.get("name")
    url = body.get("url")
    if not name or not url:
        return json_error("name and url are required", 400)

    session = get_db_session()
    try:
        source = Source(name=name, url=url, is_active=True)
        session.add(source)
        session.commit()
        session.refresh(source)
        return web.json_response({
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "is_active": source.is_active,
            "created_at": source.created_at.isoformat() if source.created_at else None,
        }, status=201)
    finally:
        session.close()


async def delete_source(request: web.Request) -> web.Response:
    try:
        source_id = int(request.match_info["id"])
    except ValueError:
        return json_error("Invalid source id", 400)
    session = get_db_session()
    try:
        source = session.query(Source).filter(Source.id == source_id).first()
        if not source:
            return json_error("Source not found", 404)
        session.delete(source)
        session.commit()
        return web.json_response({"status": "deleted"})
    finally:
        session.close()


# --- Fetch ---


async def trigger_fetch(request: web.Request) -> web.Response:
    from worker.tasks import fetch_news

    task = fetch_news.delay()
    return web.json_response({"status": "started", "task_id": task.id})


def create_app() -> web.Application:
    app = web.Application(middlewares=[error_middleware])
    app.router.add_get("/api/articles", list_articles)
    app.router.add_get("/api/articles/{id}", get_article)
    app.router.add_get("/api/sources", list_sources)
    app.router.add_post("/api/sources", create_source)
    app.router.add_delete("/api/sources/{id}", delete_source)
    app.router.add_post("/api/fetch", trigger_fetch)
    app.cleanup_ctx.append(lifespan)
    return app


def main():
    app = create_app()
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
