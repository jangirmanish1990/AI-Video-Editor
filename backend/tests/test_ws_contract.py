"""Verifies the /ws/{job_id} event stream matches the schema the frontend's
useJobSocket hook consumes (see specs/api.md). This is the backend<->frontend
contract; if it drifts, the UI silently breaks, so we lock it with a test.
"""
from starlette.websockets import WebSocketDisconnect

from fastapi.testclient import TestClient

from backend.jobs import store
from backend.main import app

client = TestClient(app)


def test_ws_streams_expected_contract():
    job = store.create_job(filename="clip.mp4")

    started = client.post("/edit", json={"job_id": job.job_id, "command": "trim to 30s"})
    assert started.status_code == 202

    types_seen = []
    plan_payload = None
    result_payload = None

    with client.websocket_connect(f"/ws/{job.job_id}") as ws:
        try:
            while True:
                msg = ws.receive_json()
                types_seen.append(msg["type"])
                if msg["type"] == "plan":
                    plan_payload = msg["plan"]
                if msg["type"] == "result":
                    result_payload = msg
        except WebSocketDisconnect:
            pass  # server closes after the final 'done' status

    # Every event type the frontend switches on must appear.
    assert {"status", "plan", "progress", "result"}.issubset(set(types_seen))

    # plan is a list of {op, params}; result carries an output_url.
    assert isinstance(plan_payload, list) and "op" in plan_payload[0]
    assert "output_url" in result_payload


def test_ws_unknown_job_reports_error():
    with client.websocket_connect("/ws/nonexistent") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
