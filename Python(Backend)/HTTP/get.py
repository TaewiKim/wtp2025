import json
import boto3
from botocore.exceptions import ClientError

dynamo = boto3.resource("dynamodb", region_name="ap-northeast-2")

def get_messages(event):
    """
    HTTP GET /dev/chat 처리:
    queryStringParameters에 room_id가 있다고 가정
    1) DynamoDB-Taewi-Brainstorming-ChatHistory 테이블에서 해당 room_id의 메시지를 조회
    2) 결과 반환
    """
    table_messages = dynamo.Table("DynamoDB-Taewi-Brainstorming-ChatHistory")
    query_params = event.get("queryStringParameters", {}) or {}
    room_id = query_params.get("room_id")

    if not room_id:
        return {
            "statusCode": 400,
            "body": json.dumps("Missing room_id")
        }

    try:
        result = table_messages.query(
            KeyConditionExpression="#HashKey = :hkey",
            ExpressionAttributeNames={"#HashKey": "RoomID"},
            ExpressionAttributeValues={":hkey": room_id}
        )
        return {
            "statusCode": 200,
            "body": json.dumps(result.get("Items", []))
        }
    except ClientError as e:
        print(f"[Error] get_messages query failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps("Internal Server Error")
        }
