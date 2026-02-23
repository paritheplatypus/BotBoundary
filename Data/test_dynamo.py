import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

table = dynamodb.Table('BehavioralEvents')

# Write a test item
table.put_item(Item={
    'sessionId': 'test-session-001',
    'timestamp': 1709123456789,
    'eventType': 'keydown',
    'key': 'a',
    'dwellTime': 87
})

# Read it back
response = table.get_item(Key={
    'sessionId': 'test-session-001',
    'timestamp': 1709123456789
})

print(response['Item'])