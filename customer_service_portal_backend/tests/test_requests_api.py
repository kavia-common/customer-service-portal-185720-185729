from datetime import datetime, timedelta, date
from typing import List

from fastapi.testclient import TestClient


def create_request(client: TestClient, title: str, description: str | None = None) -> dict:
    """Helper to create a request and return the response JSON."""
    payload = {"title": title}
    if description is not None:
        payload["description"] = description
    resp = client.post("/requests", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # sanity checks on basic shape
    assert data["title"] == title
    assert data["status"] == "new"
    assert "id" in data
    assert "created_at" in data and "updated_at" in data
    return data


def test_create_request_sets_defaults_and_timestamps(client: TestClient):
    resp = client.post("/requests", json={"title": "Printer issue", "description": "Paper jam"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Printer issue"
    assert data["description"] == "Paper jam"
    assert data["status"] == "new"
    # timestamps present and ISO-8601 format
    created_at = data["created_at"]
    updated_at = data["updated_at"]
    assert isinstance(created_at, str) and isinstance(updated_at, str)
    # Ensure created_at <= updated_at on creation (they may be equal)
    c_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    u_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    assert c_dt <= u_dt


def test_get_request_by_id_matches_created_entity(client: TestClient):
    created = create_request(client, "Network down", "Office 3rd floor")
    req_id = created["id"]

    resp = client.get(f"/requests/{req_id}")
    assert resp.status_code == 200
    fetched = resp.json()
    # Fields should match
    assert fetched["id"] == req_id
    assert fetched["title"] == "Network down"
    assert fetched["description"] == "Office 3rd floor"
    assert fetched["status"] == "new"
    assert fetched["created_at"] <= fetched["updated_at"]


def test_list_requests_supports_filters_pagination_and_desc_order(client: TestClient):
    # Create three requests with slightly different titles to test search and order
    r1 = create_request(client, "Email issue", "Cannot send emails")
    r2 = create_request(client, "Login failure", "Forgot password")
    r3 = create_request(client, "App crash", "Happens on startup")

    # Verify default list returns all items and is ordered by created_at desc
    resp_all = client.get("/requests")
    assert resp_all.status_code == 200
    body = resp_all.json()
    assert body["total"] == 3
    items: List[dict] = body["items"]
    assert len(items) == 3
    # Confirm ordering by created_at desc (r3 should be first, then r2, then r1)
    ids_in_order = [item["id"] for item in items]
    assert ids_in_order == [r3["id"], r2["id"], r1["id"]]

    # Pagination: page_size=2 -> first page returns 2 items, second returns 1
    resp_page1 = client.get("/requests", params={"page": 1, "page_size": 2})
    resp_page2 = client.get("/requests", params={"page": 2, "page_size": 2})
    assert resp_page1.status_code == 200 and resp_page2.status_code == 200
    page1 = resp_page1.json()
    page2 = resp_page2.json()
    assert page1["total"] == 3
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 1
    # Order preserved within pagination
    assert [i["id"] for i in page1["items"]] == [r3["id"], r2["id"]]
    assert [i["id"] for i in page2["items"]] == [r1["id"]]

    # Free-text filter q should match titles/descriptions (e.g., "login")
    resp_q = client.get("/requests", params={"q": "login"})
    assert resp_q.status_code == 200
    q_body = resp_q.json()
    assert q_body["total"] == 1
    assert q_body["items"][0]["id"] == r2["id"]

    # Status filter: update one to in_progress, list only in_progress
    _ = client.patch(f"/requests/{r2['id']}/status", json={"status": "in_progress"})
    resp_status = client.get("/requests", params={"status": "in_progress"})
    assert resp_status.status_code == 200
    status_body = resp_status.json()
    assert status_body["total"] == 1
    assert status_body["items"][0]["id"] == r2["id"]

    # Date range filter created_from/created_to
    # Compute today's date for inclusive filtering
    today = date.today()
    resp_date = client.get("/requests", params={"created_from": today.isoformat()})
    assert resp_date.status_code == 200
    assert resp_date.json()["total"] == 3

    # created_to before created_from should raise validation error (422)
    earlier = (today - timedelta(days=1)).isoformat()
    later = (today + timedelta(days=1)).isoformat()
    bad = client.get("/requests", params={"created_from": later, "created_to": earlier})
    assert bad.status_code == 422


def test_update_status_valid_transitions_and_history_recording(client: TestClient):
    created = create_request(client, "VPN setup")
    req_id = created["id"]

    # new -> in_progress
    resp1 = client.patch(f"/requests/{req_id}/status", json={"status": "in_progress", "note": "Started work"})
    assert resp1.status_code == 200
    body1 = resp1.json()
    assert body1["status"] == "in_progress"

    # in_progress -> resolved
    resp2 = client.patch(f"/requests/{req_id}/status", json={"status": "resolved", "note": "Fixed"})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "resolved"

    # resolved -> in_progress (reopen)
    resp3 = client.patch(f"/requests/{req_id}/status", json={"status": "in_progress", "note": "Reopen"})
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "in_progress"

    # in_progress -> closed
    resp4 = client.patch(f"/requests/{req_id}/status", json={"status": "closed"})
    assert resp4.status_code == 200
    assert resp4.json()["status"] == "closed"

    # History retrieval: should include initial 'new' plus each update in chronological order
    hist = client.get(f"/requests/{req_id}/history")
    assert hist.status_code == 200
    hdata = hist.json()
    assert hdata["id"] == req_id
    entries = hdata["history"]
    # Expect at least 5 entries: new (creation) + 4 updates
    assert len(entries) >= 5
    # Verify chronological order by timestamps
    timestamps = [e["at"] for e in entries]
    parsed = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in timestamps]
    assert parsed == sorted(parsed)
    # Confirm notes are present where provided
    notes = [e.get("note") for e in entries]
    assert "Started work" in notes
    assert "Fixed" in notes
    assert "Reopen" in notes


def test_invalid_status_transition_returns_http_error(client: TestClient):
    created = create_request(client, "Monitor setup")
    req_id = created["id"]

    # Invalid transition: in_progress -> new (need to get to in_progress first)
    resp1 = client.patch(f"/requests/{req_id}/status", json={"status": "in_progress"})
    assert resp1.status_code == 200
    # Now attempt invalid transition to new
    resp_bad = client.patch(f"/requests/{req_id}/status", json={"status": "new"})
    # Business rule maps InvalidTransitionError to HTTP 400
    assert resp_bad.status_code == 400
    detail = resp_bad.json().get("detail", "")
    assert "Invalid status transition" in detail
