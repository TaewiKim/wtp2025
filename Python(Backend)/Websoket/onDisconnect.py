import json
import boto3
from botocore.exceptions import ClientError

dynamo = boto3.resource("dynamodb", region_name="ap-northeast-2")

def on_disconnect(event):
    """
    WebSocket 연결 해제 시 ($disconnect) 처리:
    1) connection_id로 userlist 테이블에서 삭제
    """
    table_users = dynamo.Table("DynamoDB-Taewi-Brainstorming-UserList")
    connection_id = event["requestContext"]["connectionId"]

    try:
        table_users.delete_item(Key={"ConnectionID": connection_id})
    except ClientError as e:
        print(f"[Error] on_disconnect delete_item failed: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps("Disconnected")
    }
