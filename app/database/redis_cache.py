import json
import time
from typing import Dict, Any, Optional
from app.config import settings

class RedisSessionCache:
    """
    Stateful Redis session cache for live workout telemetry.
    Supports in-memory fallback if Redis server is unreachable.
    """
    def __init__(self):
        self.redis_client = None
        self._in_memory_store: Dict[str, Dict[str, Any]] = {}
        
        try:
            import redis
            self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            print("Connected to Redis datastore successfully.")
        except Exception as e:
            print(f"Redis not available ({e}). Using stateful in-memory cache fallback.")
            self.redis_client = None

    def cache_session_telemetry(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        data['cached_at'] = time.time()
        if self.redis_client:
            try:
                self.redis_client.setex(f"session:{session_id}", ttl, json.dumps(data))
                return
            except Exception:
                pass
        self._in_memory_store[session_id] = data

    def get_session_telemetry(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.redis_client:
            try:
                raw = self.redis_client.get(f"session:{session_id}")
                if raw:
                    return json.loads(raw)
            except Exception:
                pass
        return self._in_memory_store.get(session_id)

session_cache = RedisSessionCache()
