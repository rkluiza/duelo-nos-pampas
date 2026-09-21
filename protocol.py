import json

def create_message(message_type, data=None):
    return {
        "type": message_type,
        "data": data or {}
    }

def encode(message_type, data=None):
    return (
        json.dumps(
            create_message(message_type, data)
        ) + '\n'
    ).encode('utf-8')

def decode(message):
    return json.loads(message)