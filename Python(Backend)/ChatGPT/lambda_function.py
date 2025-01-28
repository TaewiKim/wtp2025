import os
import json
import datetime
import boto3
from botocore.exceptions import ClientError

import postToOpenai

endpoint_url = "https://f98s3b6lh9.execute-api.ap-northeast-2.amazonaws.com/production/"
dynamo = boto3.resource("dynamodb", region_name="ap-northeast-2")
apigw = boto3.client("apigatewaymanagementapi", region_name="ap-northeast-2", endpoint_url=endpoint_url)

def lambda_handler(event, context):
    """
    SQS로부터 메시지를 받고, 메시지 내용을 바탕으로 외부(OpenAI) API를 호출,
    결과를 DynamoDB에 저장하고 WebSocket 연결 유저에게 브로드캐스트.
    """
    table_users = dynamo.Table("DynamoDB-Taewi-Brainstorming-UserList")
    table_messages = dynamo.Table("DynamoDB-Taewi-Brainstorming-ChatHistory")

    # SQS 이벤트 레코드를 순회
    for record in event["Records"]:
        # 1) 메시지 파싱
        msg_body = json.loads(record["body"])
        room_id = msg_body.get("RoomID")
        user_name = msg_body.get("Name")
        prompt = msg_body.get("Message", "")

        # 현재 시간 생성
        now = datetime.datetime.now()

        # ISO 8601 형식으로 변환 (마이크로초 포함)
        timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # 2) OpenAI API 호출 (postToOpenai.py 참고)
        # 환경변수에 저장된 키를 사용
        api_key = os.environ.get("OPENAI_APIKEY")
        try:
            chat_response = postToOpenai.call_openai_api(prompt, api_key)
            print(chat_response)
        except Exception as e:
            print("[Error] call_openai_api failed:", e)
            chat_response = f"Error: {str(e)}"

        # 3) 결과를 DynamoDB에 저장
        item = {
            "RoomID": room_id,
            "Timestamp": timestamp_str,
            "Message": chat_response,
            "UserID": "chatgpt",
            "Name": user_name
        }
        try:
            table_messages.put_item(Item=item)
        except ClientError as e:
            print(f"[Error] put_item in table_messages failed: {e}")

        # 4) WebSocket 브로드캐스트
        try:
            users = table_users.query(
                IndexName="RoomID-UserID-index",
                KeyConditionExpression="#HashKey = :hkey",
                ExpressionAttributeNames={"#HashKey": "RoomID"},
                ExpressionAttributeValues={":hkey": room_id}
            )

            for user in users.get("Items", []):
                connection_id = user["ConnectionID"]
                try:
                    apigw.post_to_connection(
                        ConnectionId=connection_id,
                        Data=json.dumps(item)
                    )
                except ClientError as e:
                    # 연결 끊긴 유저 → DynamoDB 제거
                    if e.response["Error"]["Code"] == "GoneException":
                        table_users.delete_item(Key={"connection_id": connection_id})
                    else:
                        print("[Error] post_to_connection failed:", e)
        except ClientError as e:
            print("[Error] query userList failed:", e)

    # SQS 메시지는 Lambda 종료 후 자동 삭제(혹은 Visibility Timeout 만료 시 재시도)
    return {
        "statusCode": 200,
        "body": json.dumps("SQS batch processed.")
    }
