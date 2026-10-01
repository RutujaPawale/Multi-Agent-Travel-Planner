import os
import asyncio
import json
import urllib.request
import urllib.error
import websockets
from websockets.exceptions import ConnectionClosed

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8080")
AGENT_WS_BASE = os.getenv("AGENT_WS_BASE", "ws://localhost:8000")
AGENT_HTTP_BASE = os.getenv("AGENT_HTTP_BASE", "http://localhost:8000")

def http_json(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode("utf-8")
        return resp.status, json.loads(content) if content else None

async def test_case_1_no_token(trip_id):
    print("\n--- Test 1: No token provided ---")
    uri = f"{AGENT_WS_BASE}/ws/trip/{trip_id}"
    try:
        async with websockets.connect(uri) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            print(f"FAILED: Connected without token! Received: {msg}")
            return False
    except ConnectionClosed as e:
        print(f"SUCCESS: Connection rejected/closed by server. Code: {e.rcvd.code}, Reason: '{e.rcvd.reason}'")
        assert e.rcvd.code == 1008, f"Expected close code 1008, got {e.rcvd.code}"
        return True
    except Exception as e:
        print(f"SUCCESS: Handshake rejected with error: {e}")
        return True

async def test_case_2_invalid_token(trip_id):
    print("\n--- Test 2: Invalid/garbage token ---")
    uri = f"{AGENT_WS_BASE}/ws/trip/{trip_id}?token=invalid.jwt.signature"
    try:
        async with websockets.connect(uri) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            print(f"FAILED: Connected with invalid token! Received: {msg}")
            return False
    except ConnectionClosed as e:
        print(f"SUCCESS: Connection rejected/closed by server. Code: {e.rcvd.code}, Reason: '{e.rcvd.reason}'")
        assert e.rcvd.code == 1008, f"Expected close code 1008, got {e.rcvd.code}"
        return True
    except Exception as e:
        print(f"SUCCESS: Handshake rejected with error: {e}")
        return True

async def test_case_3_unauthorized_user(trip_id, bob_token):
    print("\n--- Test 3: Valid token, but user does NOT own trip (Bob connecting to Alice's trip) ---")
    uri = f"{AGENT_WS_BASE}/ws/trip/{trip_id}?token={bob_token}"
    try:
        async with websockets.connect(uri) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            print(f"FAILED: Bob was able to connect to Alice's trip! Received: {msg}")
            return False
    except ConnectionClosed as e:
        print(f"SUCCESS: Bob correctly rejected/closed. Code: {e.rcvd.code}, Reason: '{e.rcvd.reason}'")
        assert e.rcvd.code == 1008, f"Expected close code 1008, got {e.rcvd.code}"
        return True
    except Exception as e:
        print(f"SUCCESS: Handshake rejected with error: {e}")
        return True

async def test_case_4_owner_query_param(trip_id, alice_token):
    print("\n--- Test 4: Valid token, owner connects via ?token= query param ---")
    uri = f"{AGENT_WS_BASE}/ws/trip/{trip_id}?token={alice_token}"
    async with websockets.connect(uri) as ws:
        print("SUCCESS: Alice connected to her trip via query param!")
        # Drain any replayed events, then send ping
        await ws.send("ping")
        got_pong = False
        while True:
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            if resp == "pong":
                got_pong = True
                print("Received pong response from agent-service!")
                break
            else:
                event = json.loads(resp)
                print(f"Received replayed event: {event.get('agent')} -> {event.get('status')}")
        assert got_pong, "Expected pong response"
    return True

async def test_case_5_owner_subprotocol(trip_id, alice_token):
    print("\n--- Test 5: Valid token, owner connects via subprotocol header ---")
    uri = f"{AGENT_WS_BASE}/ws/trip/{trip_id}"
    async with websockets.connect(uri, subprotocols=[alice_token]) as ws:
        print("SUCCESS: Alice connected to her trip via subprotocol!")
        await ws.send("ping")
        got_pong = False
        while True:
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            if resp == "pong":
                got_pong = True
                print("Received pong response from agent-service!")
                break
            else:
                event = json.loads(resp)
                print(f"Received replayed event: {event.get('agent')} -> {event.get('status')}")
        assert got_pong, "Expected pong response"
    return True

def test_case_6_rest_fallback(trip_id, alice_token, bob_token):
    print("\n--- Test 6: Fallback REST endpoint GET /ws/trip/{trip_id}/events ---")
    # 6a. No token
    try:
        http_json(f"{AGENT_HTTP_BASE}/ws/trip/{trip_id}/events")
        print("FAILED: REST fallback returned 200 without token!")
        assert False
    except urllib.error.HTTPError as e:
        print(f"SUCCESS: Missing token returned expected HTTP {e.code} Unauthorized")
        assert e.code == 401

    # 6b. Bob's token (Forbidden)
    try:
        http_json(f"{AGENT_HTTP_BASE}/ws/trip/{trip_id}/events", token=bob_token)
        print("FAILED: REST fallback returned 200 for unauthorized user Bob!")
        assert False
    except urllib.error.HTTPError as e:
        print(f"SUCCESS: Bob received expected HTTP {e.code} Forbidden")
        assert e.code == 403

    # 6c. Alice's token (Authorized)
    status, data = http_json(f"{AGENT_HTTP_BASE}/ws/trip/{trip_id}/events", token=alice_token)
    print(f"SUCCESS: Alice received HTTP {status} with {len(data.get('events', []))} events")
    assert status == 200

async def main():
    print("================================================================")
    print("   WEBSOCKET JWT & TRIP OWNERSHIP VERIFICATION TEST SUITE       ")
    print("================================================================")

    # 1. Log in Alice and Bob
    _, alice_auth = http_json(f"{API_BASE}/api/auth/login", method="POST", data={"email": "alice@example.com", "password": "password123"})
    alice_token = alice_auth["token"]
    alice_user = alice_auth["user"]
    print(f"Alice logged in: {alice_user['name']} (ID: {alice_user['id']})")

    _, bob_auth = http_json(f"{API_BASE}/api/auth/login", method="POST", data={"email": "bob@example.com", "password": "password123"})
    bob_token = bob_auth["token"]
    bob_user = bob_auth["user"]
    print(f"Bob logged in: {bob_user['name']} (ID: {bob_user['id']})")

    # 2. Get an existing trip belonging to Alice, or create one if none exist
    _, alice_trips = http_json(f"{API_BASE}/api/trips", token=alice_token)
    if not alice_trips:
        print("No existing trips found for Alice. Submitting new trip to test against...")
        _, new_trip = http_json(f"{API_BASE}/api/trips", method="POST", token=alice_token, data={
            "origin": "JFK",
            "destination": "LHR",
            "startDate": "2026-11-01",
            "endDate": "2026-11-06",
            "budget": 3500.0,
            "preferences": "museums"
        })
        alice_trip_id = new_trip["id"]
    else:
        alice_trip_id = alice_trips[0]["id"]
    print(f"Testing against Alice's trip: {alice_trip_id}")

    # Run tests
    await test_case_1_no_token(alice_trip_id)
    await test_case_2_invalid_token(alice_trip_id)
    await test_case_3_unauthorized_user(alice_trip_id, bob_token)
    await test_case_4_owner_query_param(alice_trip_id, alice_token)
    await test_case_5_owner_subprotocol(alice_trip_id, alice_token)
    test_case_6_rest_fallback(alice_trip_id, alice_token, bob_token)

    print("\n================================================================")
    print("   ALL 6 WEBSOCKET JWT & OWNERSHIP VALIDATION TESTS PASSED!     ")
    print("================================================================")

if __name__ == "__main__":
    asyncio.run(main())
