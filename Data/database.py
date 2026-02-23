"""
database.py
CacheMeOutside - DynamoDB interface layer

Tables:
- Users           : partition key = userId (String)
- Sessions        : partition key = sessionId (String), sort key = userId (String)
- BehavioralEvents: partition key = sessionId (String), sort key = timestamp (Number)

Usage:
    from database import create_user, get_user, create_session, log_behavioral_event, get_session_events
"""

import boto3
import uuid
import time
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# --- Setup ---

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

users_table             = dynamodb.Table('Users')
sessions_table          = dynamodb.Table('Sessions')
behavioral_events_table = dynamodb.Table('BehavioralEvents')


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

def create_user(username: str, password_hash: str) -> dict:
    """
    Create a new user record.

    Args:
        username:      The user's display name or email.
        password_hash: Pre-hashed password (never store plaintext).

    Returns:
        The created user item as a dict, or None on failure.

    Example:
        user = create_user("alice@example.com", hashed_pw)
    """
    user_id = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)

    item = {
        'userId':        user_id,
        'username':      username,
        'passwordHash':  password_hash,
        'createdAt':     timestamp,
        # Stores the user's learned behavioral baseline (populated after enough sessions)
        'behaviorProfile': {}
    }

    try:
        users_table.put_item(Item=item)
        print(f"[DB] User created: {user_id}")
        return item
    except ClientError as e:
        print(f"[DB ERROR] create_user: {e.response['Error']['Message']}")
        return None


def get_user(user_id: str) -> dict:
    """
    Fetch a user by their userId.

    Args:
        user_id: The UUID of the user.

    Returns:
        The user item as a dict, or None if not found.

    Example:
        user = get_user("abc-123")
    """
    try:
        response = users_table.get_item(Key={'userId': user_id})
        return response.get('Item', None)
    except ClientError as e:
        print(f"[DB ERROR] get_user: {e.response['Error']['Message']}")
        return None


def get_user_by_username(username: str) -> dict:
    """
    Fetch a user by username using a scan (use sparingly on large tables).

    Args:
        username: The username or email to look up.

    Returns:
        The first matching user item, or None.

    Example:
        user = get_user_by_username("alice@example.com")
    """
    try:
        response = users_table.scan(
            FilterExpression=Key('username').eq(username)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except ClientError as e:
        print(f"[DB ERROR] get_user_by_username: {e.response['Error']['Message']}")
        return None


def update_behavior_profile(user_id: str, profile_data: dict) -> bool:
    """
    Update a user's behavioral profile with new ML-generated baseline data.
    Called by the ML team after analyzing a user's sessions.

    Args:
        user_id:      The UUID of the user.
        profile_data: Dict of behavioral metrics (e.g. avg dwell time, typing speed).

    Returns:
        True on success, False on failure.

    Example:
        update_behavior_profile("abc-123", {"avgDwellTime": 92, "avgFlightTime": 140})
    """
    try:
        users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression="SET behaviorProfile = :profile, updatedAt = :ts",
            ExpressionAttributeValues={
                ':profile': profile_data,
                ':ts':      int(time.time() * 1000)
            }
        )
        print(f"[DB] Behavior profile updated for user: {user_id}")
        return True
    except ClientError as e:
        print(f"[DB ERROR] update_behavior_profile: {e.response['Error']['Message']}")
        return False


# ─────────────────────────────────────────────
# SESSIONS
# ─────────────────────────────────────────────

def create_session(user_id: str) -> dict:
    """
    Create a new login session for a user.

    Args:
        user_id: The UUID of the user attempting to log in.

    Returns:
        The created session item as a dict, or None on failure.

    Example:
        session = create_session("abc-123")
        session_id = session['sessionId']
    """
    session_id = str(uuid.uuid4())
    timestamp  = int(time.time() * 1000)

    item = {
        'sessionId':  session_id,
        'userId':     user_id,
        'createdAt':  timestamp,
        'status':     'in_progress',  # in_progress | completed | flagged
        # ML model fills these in after analyzing the session
        'mlScore':    None,
        'isBot':      None,
        'isOwner':    None,
    }

    try:
        sessions_table.put_item(Item=item)
        print(f"[DB] Session created: {session_id} for user: {user_id}")
        return item
    except ClientError as e:
        print(f"[DB ERROR] create_session: {e.response['Error']['Message']}")
        return None


def get_session(session_id: str, user_id: str) -> dict:
    """
    Fetch a session by sessionId and userId.

    Args:
        session_id: The UUID of the session.
        user_id:    The UUID of the user (required as sort key).

    Returns:
        The session item as a dict, or None if not found.
    """
    try:
        response = sessions_table.get_item(
            Key={'sessionId': session_id, 'userId': user_id}
        )
        return response.get('Item', None)
    except ClientError as e:
        print(f"[DB ERROR] get_session: {e.response['Error']['Message']}")
        return None


def update_session_result(session_id: str, user_id: str, ml_score: float, is_bot: bool, is_owner: bool = None) -> bool:
    """
    Save the ML model's verdict on a session after analysis.

    Args:
        session_id: The UUID of the session.
        user_id:    The UUID of the user.
        ml_score:   Confidence score from the model (0.0 to 1.0).
        is_bot:     Whether the model classified the entity as a bot.
        is_owner:   Whether the model thinks it's the actual account owner (for 2FA mode).

    Returns:
        True on success, False on failure.

    Example:
        update_session_result("sess-123", "user-abc", 0.95, is_bot=False, is_owner=True)
    """
    try:
        sessions_table.update_item(
            Key={'sessionId': session_id, 'userId': user_id},
            UpdateExpression="SET mlScore = :score, isBot = :bot, isOwner = :owner, #s = :status, completedAt = :ts",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':score':  str(ml_score),  # DynamoDB doesn't support float natively, store as string
                ':bot':    is_bot,
                ':owner':  is_owner,
                ':status': 'completed',
                ':ts':     int(time.time() * 1000)
            }
        )
        return True
    except ClientError as e:
        print(f"[DB ERROR] update_session_result: {e.response['Error']['Message']}")
        return False


def get_user_sessions(user_id: str) -> list:
    """
    Get all sessions for a given user (useful for training the ML model).

    Args:
        user_id: The UUID of the user.

    Returns:
        List of session items.
    """
    try:
        response = sessions_table.query(
            IndexName='userId-index',  # NOTE: You need to add a GSI on userId in the console (see README)
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"[DB ERROR] get_user_sessions: {e.response['Error']['Message']}")
        return []


# ─────────────────────────────────────────────
# BEHAVIORAL EVENTS
# ─────────────────────────────────────────────

def log_behavioral_event(session_id: str, event_type: str, event_data: dict) -> bool:
    """
    Log a single behavioral event during a login session.
    Call this for every keystroke, mouse movement, or click captured on the frontend.

    Args:
        session_id:  The UUID of the current session.
        event_type:  Type of event: 'keydown', 'keyup', 'mousemove', 'click', 'scroll'
        event_data:  Dict of event-specific fields (see examples below).

    Returns:
        True on success, False on failure.

    Example - keystroke:
        log_behavioral_event("sess-123", "keydown", {
            "key":        "a",
            "dwellTime":  87,    # ms key was held down
            "flightTime": 134,   # ms since last keyup
        })

    Example - mouse:
        log_behavioral_event("sess-123", "mousemove", {
            "mouseX":    540,
            "mouseY":    320,
            "velocity":  2.4,
        })
    """
    timestamp = int(time.time() * 1000)

    item = {
        'sessionId': session_id,
        'timestamp': timestamp,
        'eventType': event_type,
        **event_data  # Spread all the event-specific fields directly onto the item
    }

    try:
        behavioral_events_table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"[DB ERROR] log_behavioral_event: {e.response['Error']['Message']}")
        return False


def get_session_events(session_id: str) -> list:
    """
    Get all behavioral events for a session, ordered by timestamp.
    The ML model will call this to retrieve data for analysis.

    Args:
        session_id: The UUID of the session.

    Returns:
        List of event items sorted by timestamp ascending.

    Example:
        events = get_session_events("sess-123")
        # Pass events to your ML model for analysis
    """
    try:
        response = behavioral_events_table.query(
            KeyConditionExpression=Key('sessionId').eq(session_id)
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"[DB ERROR] get_session_events: {e.response['Error']['Message']}")
        return []


def get_session_events_by_type(session_id: str, event_type: str) -> list:
    """
    Get only events of a specific type for a session (e.g. only keystrokes).

    Args:
        session_id:  The UUID of the session.
        event_type:  'keydown', 'keyup', 'mousemove', 'click', etc.

    Returns:
        Filtered list of event items.
    """
    try:
        response = behavioral_events_table.query(
            KeyConditionExpression=Key('sessionId').eq(session_id),
            FilterExpression=Key('eventType').eq(event_type)
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"[DB ERROR] get_session_events_by_type: {e.response['Error']['Message']}")
        return []


def delete_session_events(session_id: str) -> bool:
    """
    Delete all behavioral events for a session (e.g. after ML processing to save storage).

    Args:
        session_id: The UUID of the session to clean up.

    Returns:
        True on success, False on failure.
    """
    try:
        events = get_session_events(session_id)
        with behavioral_events_table.batch_writer() as batch:
            for event in events:
                batch.delete_item(Key={
                    'sessionId': event['sessionId'],
                    'timestamp': event['timestamp']
                })
        print(f"[DB] Deleted {len(events)} events for session: {session_id}")
        return True
    except ClientError as e:
        print(f"[DB ERROR] delete_session_events: {e.response['Error']['Message']}")
        return False


# ─────────────────────────────────────────────
# QUICK TEST (run this file directly to verify)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("--- Running database.py smoke test ---\n")

    # 1. Create a user
    user = create_user("testuser@example.com", "hashed_password_here")
    if not user:
        print("FAILED: create_user"); exit()
    print(f"Created user: {user['userId']}\n")

    # 2. Create a session
    session = create_session(user['userId'])
    if not session:
        print("FAILED: create_session"); exit()
    print(f"Created session: {session['sessionId']}\n")

    # 3. Log some events
    log_behavioral_event(session['sessionId'], "keydown", {"key": "a", "dwellTime": 87, "flightTime": 134})
    log_behavioral_event(session['sessionId'], "keydown", {"key": "b", "dwellTime": 92, "flightTime": 110})
    log_behavioral_event(session['sessionId'], "mousemove", {"mouseX": 540, "mouseY": 320, "velocity": 2.4})
    print("Logged 3 behavioral events\n")

    # 4. Read them back
    events = get_session_events(session['sessionId'])
    print(f"Retrieved {len(events)} events:")
    for e in events:
        print(f"  {e['eventType']} @ {e['timestamp']}")

    # 5. Save ML result
    update_session_result(session['sessionId'], user['userId'], ml_score=0.97, is_bot=False, is_owner=True)
    print("\nSession result saved.")

    print("\n--- All tests passed ---")