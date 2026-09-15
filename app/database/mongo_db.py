import time
from typing import Dict, Any, List
from app.config import settings

class MongoDBService:
    """
    MongoDB Atlas time-series datastore for workout biometric data and nutrition logs.
    Includes in-memory document storage fallback when MongoDB cluster is offline.
    """
    def __init__(self):
        self.client = None
        self.db = None
        self._in_memory_logs: List[Dict[str, Any]] = []

        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            self.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
            self.db = self.client.get_database("visionary")
            print("MongoDB Atlas service initialized.")
        except Exception as e:
            print(f"MongoDB Atlas initialization notice ({e}). Utilizing fallback datastore.")
            self.client = None
            self.db = None

    async def log_workout_session(self, session_data: Dict[str, Any]) -> str:
        session_data["timestamp"] = time.time()
        if self.db is not None:
            try:
                res = await self.db["workout_logs"].insert_one(session_data)
                return str(res.inserted_id)
            except Exception:
                pass
        self._in_memory_logs.append(session_data)
        return f"mem_doc_{len(self._in_memory_logs)}"

    async def get_workout_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        if self.db is not None:
            try:
                cursor = self.db["workout_logs"].find().sort("timestamp", -1).limit(limit)
                logs = await cursor.to_list(length=limit)
                for log in logs:
                    if "_id" in log:
                        log["_id"] = str(log["_id"])
                return logs
            except Exception:
                pass
        return sorted(self._in_memory_logs, key=lambda x: x.get("timestamp", 0), reverse=True)[:limit]

mongo_service = MongoDBService()
