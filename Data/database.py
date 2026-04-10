"""
database.py
BotBoundary / CacheMeOutside - DynamoDB interface layer.

Tables:
- Users: partition key = userId (String)
- Sessions: partition key = sessionId (String), sort key = userId (String)
- BehavioralEvents: partition key = sessionId (String), sort key = timestamp (Number)

Recommended GSIs:
- Users table: username-index (partition: username)
- Sessions table: status-createdAt-index (partition: status, sort: createdAt)
- Sessions table: userId-index (partition: userId)
"""

from __future__ import annotations

import time
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
users_table = dynamodb.Table("Users")
sessions_table = dynamodb.Table("Sessions")
behavioral_events_table = dynamodb.Table("BehavioralEvents")


def _clean(obj):
    """Recursively convert Decimal values to JSON-safe Python types."""
    if isinstance(obj, list):
        return [_clean(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _clean(value) for key, value in obj.items()}
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    return obj


def _to_dynamo(obj):
    """Recursively convert Python floats into DynamoDB-safe Decimals."""
    if isinstance(obj, list):
        return [_to_dynamo(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _to_dynamo(value) for key, value in obj.items()}
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
    except ClientError as exc:
        print(f"[DB ERROR] create_user: {exc.response['Error']['Message']}")
        return None


def get_user(user_id: str) -> dict | None:
    try:
        response = users_table.get_item(Key={"userId": user_id})
        return _clean(response.get("Item"))
    except ClientError as exc:
        print(f"[DB ERROR] get_user: {exc.response['Error']['Message']}")
        return None


def get_user_by_username(username: str) -> dict | None:
    # Preferred path: query the username-index if it exists.
    try:
        response = users_table.query(
            IndexName="username-index",
            KeyConditionExpression=Key("username").eq(username),
            Limit=1,
        )
        items = response.get("Items", [])
        if items:
            return _clean(items[0])
    except ClientError as exc:
        error_code = exc.response["Error"].get("Code")
        if error_code != "ValidationException":
            print(f"[DB ERROR] get_user_by_username(query): {exc.response['Error']['Message']}")

    # Fallback for environments where the GSI has not been created yet.
    try:
        response = users_table.scan(
            FilterExpression=Attr("username").eq(username),
            Limit=1,
        )
        items = response.get("Items", [])
        return _clean(items[0]) if items else None
    except ClientError as exc:
        print(f"[DB ERROR] get_user_by_username(scan): {exc.response['Error']['Message']}")
        return None


def update_user_password_hash(user_id: str, password_hash: str) -> bool:
    try:
        users_table.update_item(
            Key={"userId": user_id},
            UpdateExpression="SET passwordHash = :password_hash, updatedAt = :ts",
            ExpressionAttributeValues={
                ":password_hash": password_hash,
                ":ts": int(time.time() * 1000),
            },
        )
        return True
    except ClientError as exc:
        print(f"[DB ERROR] update_user_password_hash: {exc.response['Error']['Message']}")
        return False


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
    except ClientError as exc:
        print(f"[DB ERROR] update_behavior_profile: {exc.response['Error']['Message']}")
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
    except ClientError as exc:
        print(f"[DB ERROR] create_session: {exc.response['Error']['Message']}")
        return None


def get_session(session_id: str, user_id: str | None = None) -> dict | None:
    """
    Fetch a session by sessionId.

    user_id is optional. If omitted, the function scans for the session.
    """
    try:
        if user_id:
            response = sessions_table.get_item(
                Key={"sessionId": session_id, "userId": user_id}
            )
            return _clean(response.get("Item"))

        response = sessions_table.scan(
            FilterExpression=Attr("sessionId").eq(session_id)
        )
        items = response.get("Items", [])
        return _clean(items[0]) if items else None
    except ClientError as exc:
        print(f"[DB ERROR] get_session: {exc.response['Error']['Message']}")
        return None


def update_session_result(
    session_id: str,
    user_id: str,
    ml_score: float,
    is_bot: bool,
    is_owner: bool | None = None,
) -> bool:
    try:
        update_expr = "SET mlScore = :score, isBot = :bot, #s = :status, completedAt = :ts"
        expr_values = {
            ":score": Decimal(str(ml_score)),
            ":bot": is_bot,
            ":status": "completed",
            ":ts": int(time.time() * 1000),
        }
        if is_owner is not None:
            update_expr += ", isOwner = :owner"
            expr_values[":owner"] = is_owner

        sessions_table.update_item(
            Key={"sessionId": session_id, "userId": user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=expr_values,
        )
        return True
    except ClientError as exc:
        print(f"[DB ERROR] update_session_result: {exc.response['Error']['Message']}")
        return False


def get_recent_sessions(limit: int = 20) -> list:
    """
    Return the most recent completed sessions across all users.
    Uses the status-createdAt-index GSI if available.
    """
    try:
        response = sessions_table.query(
            IndexName="status-createdAt-index",
            KeyConditionExpression=Key("status").eq("completed"),
            ScanIndexForward=False,
            Limit=limit,
        )
        return _clean(response.get("Items", []))
    except ClientError as exc:
        print(f"[DB ERROR] get_recent_sessions: {exc.response['Error']['Message']}")

    try:
        response = sessions_table.scan()
        items = response.get("Items", [])
        items.sort(key=lambda item: item.get("createdAt", 0), reverse=True)
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
    except ClientError as exc:
        print(f"[DB ERROR] get_user_sessions: {exc.response['Error']['Message']}")
        return []


def save_behavior_payload(session_id: str, user_id: str, behavior: dict) -> bool:
    """
    Save the full behavior payload to the session record so the session detail
    page can display real behavioral data.
    """
    try:
        sessions_table.update_item(
            Key={"sessionId": session_id, "userId": user_id},
            UpdateExpression="SET behaviorPayload = :behavior",
            ExpressionAttributeValues={":behavior": _to_dynamo(behavior)},
        )
        return True
    except ClientError as exc:
        print(f"[DB ERROR] save_behavior_payload: {exc.response['Error']['Message']}")
        return False


# ── Behavioral Events ─────────────────────────────────────────────────────────
def log_behavioral_event(session_id: str, event_type: str, event_data: dict) -> bool:
    timestamp = int(time.time() * 1000)
    item = {
        "sessionId": session_id,
        "timestamp": timestamp,
        "eventType": event_type,
        **_to_dynamo(event_data),
    }
    try:
        behavioral_events_table.put_item(Item=item)
        return True
    except ClientError as exc:
        print(f"[DB ERROR] log_behavioral_event: {exc.response['Error']['Message']}")
        return False


def get_session_events(session_id: str) -> list:
    try:
        response = behavioral_events_table.query(
            KeyConditionExpression=Key("sessionId").eq(session_id)
        )
        return _clean(response.get("Items", []))
    except ClientError as exc:
        print(f"[DB ERROR] get_session_events: {exc.response['Error']['Message']}")
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
    except ClientError as exc:
        print(f"[DB ERROR] delete_session_events: {exc.response['Error']['Message']}")
        return False
