"""
database.py
CacheMeOutside - DynamoDB interface layer

Tables:
- Users : partition key = userId (String)
- Sessions : partition key = sessionId (String), sort key = userId (String)
- BehavioralEvents : partition key = sessionId (String), sort key = timestamp (Number)

Recommended GSI:
- Sessions table: status-createdAt-index (partition: status, sort: createdAt)
- Sessions table: userId-index (partition: userId)
"""

from __future__ import annotations

import time
import uuid
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
users_table = dynamodb.Table("Users")
sessions_table = dynamodb.Table("Sessions")
behavioral_events_table = dynamodb.Table("BehavioralEvents")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _clean(obj: Any) -> Any:
    """Recursively convert Decimal to JSON-serializable Python values."""
    if isinstance(obj, list):
        return [_clean(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        # Keep integers as ints where possible.
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def _to_dynamo(obj: Any) -> Any:
    """Recursively convert Python floats into DynamoDB-safe Decimals."""
    if isinstance(obj, list):
        return [_to_dynamo(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _to_dynamo(v) for k, v in obj.items()}
    if isinstance(obj, float):
        return Decimal(str(obj))
    return obj


# ── Users ─────────────────────────────────────────────────────────────────────
def create_user(username: str, password_hash: str) -> dict | None:
    user_id = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)
    item = {
        "userId": user_id,
        "username": username,
        "passwordHash": password_hash,
        "createdAt": timestamp,
        "behaviorProfile": {},
    }
    try:
        users_table.put_item(Item=item)
        print(f"[DB] User created: {user_id}")
        return item
    except ClientError as e:
        print(f"[DB ERROR] create_user: {e.response['Error']['Message']}")
        return None



def get_user(user_id: str) -> dict | None:
    try:
        response = users_table.get_item(Key={"userId": user_id})
        return _clean(response.get("Item"))
    except ClientError as e:
        print(f"[DB ERROR] get_user: {e.response['Error']['Message']}")
        return None



def get_user_by_username(username: str) -> dict | None:
    """Lookup by username.

    Note: this uses a scan because the current table schema does not define a
    username GSI. If a username-index exists later, this can be upgraded to a
    query.
    """
    try:
        response = users_table.scan(FilterExpression=Attr("username").eq(username))
        items = response.get("Items", [])
        return _clean(items[0]) if items else None
    except ClientError as e:
        print(f"[DB ERROR] get_user_by_username: {e.response['Error']['Message']}")
        return None



def update_behavior_profile(user_id: str, profile_data: dict) -> bool:
    try:
        users_table.update_item(
            Key={"userId": user_id},
            UpdateExpression="SET behaviorProfile = :profile, updatedAt = :ts",
            ExpressionAttributeValues={
                ":profile": _to_dynamo(profile_data),
                ":ts": int(time.time() * 1000),
            },
        )
        return True
    except ClientError as e:
        print(f"[DB ERROR] update_behavior_profile: {e.response['Error']['Message']}")
        return False


# ── Sessions ──────────────────────────────────────────────────────────────────
def create_session(user_id: str) -> dict | None:
    session_id = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)
    item = {
        "sessionId": session_id,
        "userId": user_id,
        "createdAt": timestamp,
        "status": "in_progress",
    }
    try:
        sessions_table.put_item(Item=item)
        print(f"[DB] Session created: {session_id}")
        return item
    except ClientError as e:
        print(f"[DB ERROR] create_session: {e.response['Error']['Message']}")
        return None



def get_session(session_id: str, user_id: str | None = None) -> dict | None:
    """Fetch a session by sessionId.

    user_id is optional — if omitted we scan for the session.
    """
    try:
        if user_id:
            response = sessions_table.get_item(Key={"sessionId": session_id, "userId": user_id})
            return _clean(response.get("Item"))

        response = sessions_table.scan(FilterExpression=Attr("sessionId").eq(session_id))
        items = response.get("Items", [])
        return _clean(items[0]) if items else None
    except ClientError as e:
        print(f"[DB ERROR] get_session: {e.response['Error']['Message']}")
        return None



def update_session_result(
    session_id: str,
    user_id: str,
    ml_score: float,
    is_bot: bool,
    is_owner: bool | None = None,
    model_name: str | None = None,
    threshold: float | None = None,
) -> bool:
    try:
        update_expr = "SET mlScore = :score, isBot = :bot, #s = :status, completedAt = :ts"
        expr_values: dict[str, Any] = {
            ":score": Decimal(str(ml_score)),
            ":bot": is_bot,
            ":status": "completed",
            ":ts": int(time.time() * 1000),
        }

        if is_owner is not None:
            update_expr += ", isOwner = :owner"
            expr_values[":owner"] = is_owner

        if model_name is not None:
            update_expr += ", model = :model"
            expr_values[":model"] = model_name

        if threshold is not None:
            update_expr += ", threshold = :threshold"
            expr_values[":threshold"] = Decimal(str(threshold))

        sessions_table.update_item(
            Key={"sessionId": session_id, "userId": user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=expr_values,
        )
        return True
    except ClientError as e:
        print(f"[DB ERROR] update_session_result: {e.response['Error']['Message']}")
        return False



def get_recent_sessions(limit: int = 20) -> list:
    """Return the most recent completed sessions across all users."""
    try:
        response = sessions_table.query(
            IndexName="status-createdAt-index",
            KeyConditionExpression=Key("status").eq("completed"),
            ScanIndexForward=False,
            Limit=limit,
        )
        return _clean(response.get("Items", []))
    except ClientError as e:
        print(f"[DB ERROR] get_recent_sessions: {e.response['Error']['Message']}")

    try:
        response = sessions_table.scan()
        items = response.get("Items", [])
        items.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
        return _clean(items[:limit])
    except Exception:
        return []



def get_user_sessions(user_id: str) -> list:
    try:
        response = sessions_table.query(
            IndexName="userId-index",
            KeyConditionExpression=Key("userId").eq(user_id),
        )
        return _clean(response.get("Items", []))
    except ClientError as e:
        print(f"[DB ERROR] get_user_sessions: {e.response['Error']['Message']}")
        return []



def save_behavior_payload(session_id: str, user_id: str, behavior: dict) -> bool:
    """Save the full behavior payload on the session row for fast lookup."""
    try:
        sessions_table.update_item(
            Key={"sessionId": session_id, "userId": user_id},
            UpdateExpression="SET behaviorPayload = :b",
            ExpressionAttributeValues={":b": _to_dynamo(behavior)},
        )
        return True
    except ClientError as e:
        print(f"[DB ERROR] save_behavior_payload: {e.response['Error']['Message']}")
        return False


# ── Behavioral Events ─────────────────────────────────────────────────────────
def log_behavioral_event(
    session_id: str,
    event_type: str,
    event_data: dict,
    *,
    user_id: str | None = None,
    timestamp: int | None = None,
) -> bool:
    """Write a single event row to BehavioralEvents."""
    event_ts = int(time.time() * 1000) if timestamp is None else int(timestamp)
    item = {
        "sessionId": session_id,
        "timestamp": event_ts,
        "eventType": event_type,
        "eventData": _to_dynamo(event_data),
    }
    if user_id is not None:
        item["userId"] = user_id

    try:
        behavioral_events_table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"[DB ERROR] log_behavioral_event: {e.response['Error']['Message']}")
        return False



def save_behavior_events(
    session_id: str,
    user_id: str,
    behavior: dict,
    inference: dict | None = None,
) -> bool:
    """Persist summarized behavior groups into BehavioralEvents.

    Why this exists:
    - The current frontend sends one summarized behavior payload at submit time.
    - The old backend only stored that payload on the Sessions row.
    - Nothing ever called log_behavioral_event(), so BehavioralEvents remained empty.

    This function writes one event per top-level behavior group (`mouse`,
    `keyboard`, `interaction`, `timing`, `environment`) plus an optional
    `inference_result` event.

    Timestamps are offset by +1 ms per event to guarantee unique composite keys
    for the same sessionId even when all writes happen in one request.
    """
    try:
        base_ts = int(time.time() * 1000)
        items: list[dict[str, Any]] = []

        ordered_groups = ["mouse", "keyboard", "interaction", "timing", "environment"]
        for idx, group in enumerate(ordered_groups):
            group_data = behavior.get(group)
            if isinstance(group_data, dict) and group_data:
                items.append(
                    {
                        "sessionId": session_id,
                        "timestamp": base_ts + idx,
                        "userId": user_id,
                        "eventType": group,
                        "eventData": _to_dynamo(group_data),
                    }
                )

        if inference:
            items.append(
                {
                    "sessionId": session_id,
                    "timestamp": base_ts + len(items),
                    "userId": user_id,
                    "eventType": "inference_result",
                    "eventData": _to_dynamo(inference),
                }
            )

        if not items:
            return True

        with behavioral_events_table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)

        return True
    except ClientError as e:
        print(f"[DB ERROR] save_behavior_events: {e.response['Error']['Message']}")
        return False



def get_session_events(session_id: str) -> list:
    try:
        response = behavioral_events_table.query(
            KeyConditionExpression=Key("sessionId").eq(session_id),
            ScanIndexForward=True,
        )
        return _clean(response.get("Items", []))
    except ClientError as e:
        print(f"[DB ERROR] get_session_events: {e.response['Error']['Message']}")
        return []



def delete_session_events(session_id: str) -> bool:
    try:
        events = get_session_events(session_id)
        with behavioral_events_table.batch_writer() as batch:
            for event in events:
                batch.delete_item(
                    Key={
                        "sessionId": event["sessionId"],
                        "timestamp": event["timestamp"],
                    }
                )
        return True
    except ClientError as e:
        print(f"[DB ERROR] delete_session_events: {e.response['Error']['Message']}")
        return False
