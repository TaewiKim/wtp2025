import json
import boto3
from botocore.exceptions import ClientError

dynamo = boto3.resource("dynamodb", region_name="ap-northeast-2")

def on_connect(event):
    """
    WebSocket 연결 시 ($connect) 처리:
    1) connection_id를 userlist 테이블에 저장
    2) queryStringParameters로 RoomID, user_id를 받았다고 가정
    """
    table_users = dynamo.Table("DynamoDB-Taewi-Brainstorming-UserList")
    connection_id = event["requestContext"]["connectionId"]

    query_params = event.get("queryStringParameters", {}) or {}
    room_id = query_params.get("room_id", "default_room")
    user_id = query_params.get("user_id", "guest")

    try:
        table_users.put_item(
            Item={
                "ConnectionID": connection_id,
                "RoomID": room_id,
                "UserID": user_id
            }
        )
    except ClientError as e:
        print(f"[Error] on_connect put_item failed: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps("Connected")
    }
