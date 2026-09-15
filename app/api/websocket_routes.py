import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.cv.pose_engine import PoseEngine
from app.database.redis_cache import session_cache
from app.database.mongo_db import mongo_service

router = APIRouter()

# Active WebSocket Connection Manager for load tracking (100+ concurrent connections KPI)
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    def count(self) -> int:
        return len(self.active_connections)

manager = ConnectionManager()

@router.websocket("/ws/kinematics/{session_id}")
async def websocket_kinematics_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket)
    pose_engine = PoseEngine()

    try:
        while True:
            # Receive raw JSON packet from client camera / MediaPipe JS
            data_str = await websocket.receive_text()
            packet = json.loads(data_str)

            exercise = packet.get("exercise", "bicep_curl")
            landmarks = packet.get("landmarks", [])

            if pose_engine.current_exercise != exercise:
                pose_engine.set_exercise(exercise)

            # Perform sub-30ms Vector Math & Phase Classification
            result = pose_engine.process_landmarks(landmarks)
            result["session_id"] = session_id
            result["active_ws_connections"] = manager.count()

            # Cache active telemetry in Redis
            session_cache.cache_session_telemetry(session_id, result)

            # Send real-time analysis back over WebSocket
            await websocket.send_text(json.dumps(result))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Log completed session telemetry to MongoDB
        last_telemetry = session_cache.get_session_telemetry(session_id)
        if last_telemetry:
            await mongo_service.log_workout_session(last_telemetry)
    except Exception as e:
        import traceback
        print(f"WebSocket Exception: {e}", flush=True)
        traceback.print_exc()
        manager.disconnect(websocket)
