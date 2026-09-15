import asyncio
import json
import websockets
import pytest

async def test_websocket_kinematics_stream():
    url = "ws://localhost:8000/ws/kinematics/test_session_1"
    
    async with websockets.connect(url) as ws:
        landmarks = [{'x': 0.5, 'y': 0.5, 'z': 0.0} for _ in range(33)]
        landmarks[11] = {'x': 0.4, 'y': 0.3, 'z': 0.0} # Shoulder
        landmarks[13] = {'x': 0.38, 'y': 0.55, 'z': 0.0} # Elbow
        landmarks[15] = {'x': 0.38, 'y': 0.85, 'z': 0.0} # Wrist (Extended > 160 deg)

        # 1. Send extended frame -> STAGE: DOWN
        packet = {"exercise": "bicep_curl", "landmarks": landmarks}
        await ws.send(json.dumps(packet))
        response_str = await ws.recv()
        data = json.loads(response_str)

        assert data["valid"] is True
        assert data["phase"] == "DOWN"
        assert data["rep_count"] == 0

        # 2. Send curled frame -> STAGE: UP & REP + 1
        landmarks[15] = {'x': 0.38, 'y': 0.35, 'z': 0.0}
        packet = {"exercise": "bicep_curl", "landmarks": landmarks}
        await ws.send(json.dumps(packet))
        response_str = await ws.recv()
        data = json.loads(response_str)

        assert data["phase"] == "UP"
        assert data["rep_count"] == 1
        assert data["rep_completed"] is True

if __name__ == "__main__":
    asyncio.run(test_websocket_kinematics_stream())
    print("WebSocket Reference Mechanics Integration Test Passed Successfully!")
