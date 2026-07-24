import asyncio
import uuid

from app.core.cache import Cache
from app.models import Movie
from app.services.movies import MovieService


class InMemoryCacheBackend:
    def __init__(self):
        self._store = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value, ttl_seconds: int | None = None):
        self._store[key] = value

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def delete_pattern(self, pattern: str):
        keys_to_delete = [key for key in self._store if key.startswith(pattern)]
        for key in keys_to_delete:
            self._store.pop(key, None)


def test_cache_round_trip():
    async def run():
        cache = Cache(backend=InMemoryCacheBackend(), ttl_seconds=30)
        assert await cache.get("demo") is None
        await cache.set("demo", {"value": 1})
        assert await cache.get("demo") == {"value": 1}

    asyncio.run(run())


def test_movie_service_uses_cache_when_available():
    async def run():
        cache = Cache(backend=InMemoryCacheBackend(), ttl_seconds=60)
        movie_id = uuid.uuid4()
        payload = {
            "items": [
                {
                    "id": str(movie_id),
                    "title": "Inception",
                    "description": "A mind-bending thriller",
                    "duration_minutes": 148,
                    "poster_url": None,
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        await cache.set("movies:list::1:20:title:asc", payload)

        service = MovieService(db=None, cache=cache)
        items, total = await service.list_movies(None, 1, 20, "title", "asc")

        assert total == 1
        assert len(items) == 1
        assert isinstance(items[0], Movie)
        assert items[0].title == "Inception"

    asyncio.run(run())
