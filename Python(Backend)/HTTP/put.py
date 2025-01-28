import json
import boto3
import datetime
from botocore.exceptions import ClientError

dynamo = boto3.resource("dynamodb", region_name="ap-northeast-2")
sqs = boto3.client("sqs", region_name="ap-northeast-2")

def put_message(event):
    """
    HTTP PUT /dev/chat 처리:
    Body에 {room_id, text, user_id, name} 필드
    1) DynamoDB-Taewi-Brainstorming-ChatHistory 테이블에 메시지 저장
    2) SQS로 메시지 전달(응답은 별도 Lambda에서)
    """
    table_messages = dynamo.Table("DynamoDB-Taewi-Brainstorming-ChatHistory")

    # Body 파싱
    if "body" not in event or not event["body"]:
        return {
            "statusCode": 400,
            "body": json.dumps("Missing request body")
        }

    try:
        data = json.loads(event["body"])
        print(data)
    except:
        return {
            "statusCode": 400,
            "body": json.dumps("Invalid JSON in body")
        }

    required = ["room_id", "text", "user_id", "name"]
    for field in required:
        if field not in data:
            return {
                "statusCode": 400,
                "body": json.dumps(f"Missing field: {field}")
            }

    # 현재 시간 생성
    now = datetime.datetime.now()

    # ISO 8601 형식으로 변환 (마이크로초 포함)
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    item = {
        "RoomID": str(data["room_id"]),
        "Timestamp": timestamp_str,
        "Message": str(data["text"]),
        "UserID": str(data["user_id"]),
        "Name": str(data["name"])
    }

    # queue_url = os.environ.get("SQS_QUEUE_URL")
    queue_url = "https://sqs.ap-northeast-2.amazonaws.com/225989345027/SQS-Taewi-Brainstorming-WebsoketToChatGPT"
    if not queue_url:
        return {
            "statusCode": 400,
            "body": json.dumps("Missing queue_url")
        }

    # 1) DB에 메시지 저장
    try:
        table_messages.put_item(Item=item)
    except ClientError as e:
        print(f"[Error] put_message put_item failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps("Error saving message.")
        }

    # 2) SQS로 메시지 전달
    try:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(item)
        )
        return {
            "statusCode": 200,
            "body": json.dumps("Message sent to SQS successfully.")
        }
    except ClientError as e:
        print(f"[Error] put_message SQS failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps("Error sending message to SQS.")
        }
