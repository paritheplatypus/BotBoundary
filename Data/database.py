"""
database.py
CacheMeOutside - DynamoDB interface layer

Tables:
- Users            : partition key = userId (String)
- Sessions         : partition key = sessionId (String), sort key = userId (String)
- BehavioralEvents : partition key = sessionId (String), sort key = timestamp (Number)

Required GSI:
- Sessions table: status-createdAt-index (partition: status, sort: createdAt)
"""

import boto3
import uuid
import time
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

users_table             = dynamodb.Table('Users')
sessions_table          = dynamodb.Table('Sessions')
behavioral_events_table = dynamodb.Table('BehavioralEvents')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean(obj):
    """Recursively convert Decimal to float for JSON serialization."""
    if isinstance(obj, list):
        return [_clean(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def _to_dynamo(obj):
    """Recursively convert Python floats into DynamoDB-safe Decimals."""
    if isinstance(obj, list):
        return [_to_dynamo(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _to_dynamo(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(username: str, password_hash: str) -> dict:
    user_id   = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)

    item = {
        'userId':          user_id,
        'username':        username,
        'passwordHash':    password_hash,
        'createdAt':       timestamp,
        'behaviorProfile': {},
    }

    try:
        users_table.put_item(Item=item)
        print(f"[DB] User created: {user_id}")
        return item
    except ClientError as e:
        print(f"[DB ERROR] create_user: {e.response['Error']['Message']}")
        return None


def get_user(user_id: str) -> dict:
    try:
        response = users_table.get_item(Key={'userId': user_id})
        return _clean(response.get('Item'))
    except ClientError as e:
        print(f"[DB ERROR] get_user: {e.response['Error']['Message']}")
        return None


def get_user_by_username(username: str) -> dict:
    try:
        response = users_table.scan(
            FilterExpression=Key('username').eq(username)
        )
        items = response.get('Items', [])
        return _clean(items[0]) if items else None
    except ClientError as e:
        print(f"[DB ERROR] get_user_by_username: {e.response['Error']['Message']}")
        return None


def update_behavior_profile(user_id: str, profile_data: dict) -> bool:
    try:
        users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression="SET behaviorProfile = :profile, updatedAt = :ts",
            ExpressionAttributeValues={
                ':profile': _to_dynamo(profile_data),
                ':ts':      int(time.time() * 1000),
            }
        )
        return True
    except ClientError as e:
        print(f"[DB ERROR] update_behavior_profile: {e.response['Error']['Message']}")
        return False


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(user_id: str) -> dict:
    session_id = str(uuid.uuid4())
    timestamp  = int(time.time() * 1000)

    item = {
        'sessionId': session_id,
        'userId':    user_id,
        'createdAt': timestamp,
        'status':    'in_progress',
        # not set until model runs — omitted to avoid DynamoDB None rejection
    }

    try:
        sessions_table.put_item(Item=item)
        print(f"[DB] Session created: {session_id}")
        return item
    except ClientError as e:
        print(f"[DB ERROR] create_session: {e.response['Error']['Message']}")
        return None


def get_session(session_id: str, user_id: str = None) -> dict:
    """
    Fetch a session by sessionId.
    user_id is optional — if omitted we scan for the session.
    """
    try:
        if user_id:
            response = sessions_table.get_item(
                Key={'sessionId': session_id, 'userId': user_id}
            )
            return _clean(response.get('Item'))
        else:
            # scan for the session without knowing userId
            response = sessions_table.scan(
                FilterExpression=Key('sessionId').eq(session_id)
            )
            items = response.get('Items', [])
            return _clean(items[0]) if items else None
    except ClientError as e:
        print(f"[DB ERROR] get_session: {e.response['Error']['Message']}")
        return None


def update_session_result(
    session_id: str,
    user_id: str,
    ml_score: float,
    is_bot: bool,
    is_owner: bool = None
) -> bool:
    try:
        update_expr = "SET mlScore = :score, isBot = :bot, #s = :status, completedAt = :ts"
        expr_values = {
            ':score':  Decimal(str(ml_score)),
            ':bot':    is_bot,
            ':status': 'completed',
            ':ts':     int(time.time() * 1000),
        }

        # Only set isOwner if we have a value (avoids storing null)
        if is_owner is not None:
            update_expr += ", isOwner = :owner"
            expr_values[':owner'] = is_owner

        sessions_table.update_item(
            Key={'sessionId': session_id, 'userId': user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues=expr_values,
        )
        return True
    except ClientError as e:
        print(f"[DB ERROR] update_session_result: {e.response['Error']['Message']}")
        return False


def get_recent_sessions(limit: int = 20) -> list:
    """
    Return the most recent completed sessions across all users.
    Uses the status-createdAt-index GSI.
    """
    try:
        response = sessions_table.query(
            IndexName='status-createdAt-index',
            KeyConditionExpression=Key('status').eq('completed'),
            ScanIndexForward=False,  # descending — newest first
            Limit=limit,
        )
        return _clean(response.get('Items', []))
    except ClientError as e:
        print(f"[DB ERROR] get_recent_sessions: {e.response['Error']['Message']}")
        # Fallback: full scan if GSI not set up yet
        try:
            response = sessions_table.scan()
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
            return _clean(items[:limit])
        except Exception:
            return []


def get_user_sessions(user_id: str) -> list:
    try:
        response = sessions_table.query(
            IndexName='userId-index',
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        return _clean(response.get('Items', []))
    except ClientError as e:
        print(f"[DB ERROR] get_user_sessions: {e.response['Error']['Message']}")
        return []


def save_behavior_payload(session_id: str, user_id: str, behavior: dict) -> bool:
    """
    Save the full behavior payload to the session record so the
    session detail page can display real behavioral data.
    """
    try:
        sessions_table.update_item(
            Key={'sessionId': session_id, 'userId': user_id},
            UpdateExpression="SET behaviorPayload = :b",
            ExpressionAttributeValues={':b': _to_dynamo(behavior)},
        )
        return True
    except ClientError as e:
        print(f"[DB ERROR] save_behavior_payload: {e.response['Error']['Message']}")
        return False


# ── Behavioral Events ─────────────────────────────────────────────────────────

def log_behavioral_event(session_id: str, event_type: str, event_data: dict) -> bool:
    timestamp = int(time.time() * 1000)
    item = {
        'sessionId': session_id,
        'timestamp': timestamp,
        'eventType': event_type,
        **_to_dynamo(event_data),
    }
    try:
        behavioral_events_table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"[DB ERROR] log_behavioral_event: {e.response['Error']['Message']}")
        return False


def get_session_events(session_id: str) -> list:
    try:
        response = behavioral_events_table.query(
            KeyConditionExpression=Key('sessionId').eq(session_id)
        )
        return _clean(response.get('Items', []))
    except ClientError as e:
        print(f"[DB ERROR] get_session_events: {e.response['Error']['Message']}")
        return []


def delete_session_events(session_id: str) -> bool:
    try:
        events = get_session_events(session_id)
        with behavioral_events_table.batch_writer() as batch:
            for event in events:
                batch.delete_item(Key={
                    'sessionId': event['sessionId'],
                    'timestamp': event['timestamp'],
                })
        return True
    except ClientError as e:
        print(f"[DB ERROR] delete_session_events: {e.response['Error']['Message']}")
        return False
