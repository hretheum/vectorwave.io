#!/usr/bin/env python3
import os
import sys
import json
import time
import getpass
import hashlib
import argparse
from typing import Dict, Any, List, Optional
import urllib.parse
import requests

VIKUNJA_BASE = os.environ.get("VIKUNJA_BASE_URL", "http://localhost:3456/api/v1")
VIKUNJA_TOKEN = os.environ.get("VIKUNJA_TOKEN", "")
WEKAN_BASE = os.environ.get("WEKAN_BASE_URL", "http://localhost:8090")
WEKAN_TOKEN_ENV = os.environ.get("WEKAN_TOKEN")
WEKAN_USER_ID_ENV = os.environ.get("WEKAN_USER_ID")

PROJECT_ID = int(os.environ.get("VIKUNJA_PROJECT_ID", "2"))
VIEW_ID = int(os.environ.get("VIKUNJA_VIEW_ID", "8"))

session = requests.Session()


def vikunja_get(path: str) -> Any:
    url = f"{VIKUNJA_BASE}{path}"
    resp = session.get(url, headers={"Authorization": f"Bearer {VIKUNJA_TOKEN}"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def wekan_login(username: str, password: str) -> Dict[str, str]:
    """Attempt multiple known Meteor/Wekan login payloads, return token+user_id."""
    digest = hashlib.sha256(password.encode()).hexdigest()
    candidates = [
        ({"user": {"username": username}, "password": {"digest": digest, "algorithm": "sha-256"}}, "json"),
        ({"user": {"email": username}, "password": {"digest": digest, "algorithm": "sha-256"}}, "json"),
        ({"username": username, "password": password}, "json"),
    ]
    for body, kind in candidates:
        try:
            resp = session.post(f"{WEKAN_BASE}/users/login", json=body, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("authToken") or (data.get("data") or {}).get("authToken")
                user_id = data.get("userId") or (data.get("data") or {}).get("userId")
                if token and user_id:
                    return {"token": token, "user_id": user_id}
        except Exception:
            pass
    # Final fallback: form-encoded
    try:
        resp = session.post(
            f"{WEKAN_BASE}/users/login",
            data=urllib.parse.urlencode({"username": username, "password": password}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("authToken") or (data.get("data") or {}).get("authToken")
            user_id = data.get("userId") or (data.get("data") or {}).get("userId")
            if token and user_id:
                return {"token": token, "user_id": user_id}
    except Exception:
        pass
    raise RuntimeError("Wekan login failed with all known payloads. Try providing WEKAN_TOKEN and WEKAN_USER_ID env.")


def wekan_headers(token: str, user_id: str) -> Dict[str, str]:
    return {"X-Auth-Token": token, "X-User-Id": user_id, "Content-Type": "application/json"}


def wekan_get(path: str, token: str, user_id: str) -> Any:
    resp = session.get(f"{WEKAN_BASE}{path}", headers=wekan_headers(token, user_id), timeout=30)
    resp.raise_for_status()
    return resp.json()


def wekan_post(path: str, token: str, user_id: str, body: Dict[str, Any]) -> Any:
    resp = session.post(f"{WEKAN_BASE}{path}", headers=wekan_headers(token, user_id), json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def wekan_put(path: str, token: str, user_id: str, body: Dict[str, Any]) -> Any:
    resp = session.put(f"{WEKAN_BASE}{path}", headers=wekan_headers(token, user_id), json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def ensure_board(board_title: str, token: str, user_id: str) -> str:
    boards = wekan_get("/api/boards", token, user_id)
    for b in boards if isinstance(boards, list) else []:
        if b.get("title") == board_title:
            return b.get("_id")
    created = wekan_post("/api/boards", token, user_id, {"title": board_title})
    return created.get("_id")


def ensure_list(board_id: str, title: str, token: str, user_id: str) -> str:
    lists = wekan_get(f"/api/boards/{board_id}/lists", token, user_id)
    for l in lists if isinstance(lists, list) else []:
        if l.get("title") == title:
            return l.get("_id")
    created = wekan_post(f"/api/boards/{board_id}/lists", token, user_id, {"title": title})
    return created.get("_id")


def create_card(board_id: str, list_id: str, title: str, description: Optional[str], token: str, user_id: str) -> str:
    body = {"title": title}
    if description:
        body["description"] = description
    created = wekan_post(f"/api/boards/{board_id}/lists/{list_id}/cards", token, user_id, body)
    return created.get("_id")


def add_comment(board_id: str, list_id: str, card_id: str, text: str, token: str, user_id: str) -> None:
    wekan_post(f"/api/boards/{board_id}/lists/{list_id}/cards/{card_id}/comments", token, user_id, {"text": text})


def move_card(board_id: str, from_list: str, card_id: str, to_list: str, token: str, user_id: str) -> None:
    wekan_put(f"/api/boards/{board_id}/lists/{from_list}/cards/{card_id}", token, user_id, {"listId": to_list, "position": 0})


def main():
    parser = argparse.ArgumentParser(description="Migrate tasks from Vikunja to Wekan")
    parser.add_argument("--board", default="vector-wave")
    parser.add_argument("--project", type=int, default=PROJECT_ID)
    parser.add_argument("--view", type=int, default=VIEW_ID)
    parser.add_argument("--wekan-user", default=os.environ.get("WEKAN_USER", "hretheum"))
    args = parser.parse_args()

    if not VIKUNJA_TOKEN:
        print("Set VIKUNJA_TOKEN env.")
        sys.exit(1)

    # Prefer existing session token from env to avoid interactive login
    if WEKAN_TOKEN_ENV and WEKAN_USER_ID_ENV:
        print("Using WEKAN_TOKEN/WEKAN_USER_ID from env.")
        token = WEKAN_TOKEN_ENV
        user_id = WEKAN_USER_ID_ENV
    else:
        print("Logging to Wekan...")
        pw = getpass.getpass(f"Password for Wekan user {args.wekan_user}: ")
        auth = wekan_login(args.wekan_user, pw)
        token = auth["token"]; user_id = auth["user_id"]

    print("Ensuring Wekan board and lists...")
    board_id = ensure_board(args.board, token, user_id)
    list_map = {
        "Todo": ensure_list(board_id, "Todo", token, user_id),
        "In-Progress": ensure_list(board_id, "In-Progress", token, user_id),
        "Blocked": ensure_list(board_id, "Blocked", token, user_id),
        "Done": ensure_list(board_id, "Done", token, user_id),
    }

    print("Fetching Vikunja view buckets...")
    view = vikunja_get(f"/projects/{args.project}/views/{args.view}")
    bucket_config = view.get("bucket_configuration") or {}
    bucket_titles: Dict[int, str] = {}
    if isinstance(bucket_config, dict):
        for b in bucket_config.get("buckets", []):
            bucket_titles[b.get("id")] = b.get("title")

    print("Fetching Vikunja tasks in view...")
    tasks = vikunja_get(f"/projects/{args.project}/views/{args.view}/tasks")
    if not isinstance(tasks, list):
        print("No tasks found or unexpected response.")
        sys.exit(1)

    created_count = 0
    for t in tasks:
        title = t.get("title") or "(no title)"
        desc = t.get("description") or None
        bucket_id = t.get("bucket_id") or 0
        bucket_title = bucket_titles.get(bucket_id, "Todo")
        target_list = list_map.get(bucket_title, list_map["Todo"])
        card_id = create_card(board_id, target_list, title, desc, token, user_id)
        created_count += 1
        # Optional: comment with original meta
        note = {
            "vikunja_id": t.get("id"),
            "priority": t.get("priority"),
            "labels": [lbl.get("title") for lbl in (t.get("labels") or [])],
            "done": t.get("done"),
        }
        try:
            add_comment(board_id, target_list, card_id, f"Imported from Vikunja: {json.dumps(note, ensure_ascii=False)}", token, user_id)
        except Exception:
            pass
        # Move to Done if done
        if t.get("done"):
            try:
                move_card(board_id, target_list, card_id, list_map["Done"], token, user_id)
            except Exception:
                pass

    print(f"Created {created_count} cards on Wekan board '{args.board}'.")

if __name__ == "__main__":
    main()
