import os
import json
import datetime
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

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

    for record in event["Records"]:
        # 1) 메시지 파싱
        msg_body = json.loads(record["body"])
        room_id = msg_body.get("RoomID")
        user_name = msg_body.get("Name")
        user_message_content = msg_body.get("Message", "")

        # 현재 시간 생성 (ISO 8601 형식, 마이크로초 포함)
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # 2) DynamoDB에서 해당 Room의 최근 10개 메시지를 가져오기
        try:
            response = table_messages.query(
                KeyConditionExpression=Key("RoomID").eq(room_id),
                ScanIndexForward=False,  # 최신순 정렬
                Limit=10                 # 최대 10개만
            )
            recent_items = response.get("Items", [])
        except ClientError as e:
            print(f"[Error] query table_messages failed: {e}")
            recent_items = []

        # 가져온 메시지를 시간 오름차순으로 재정렬 (과거 -> 최신)
        recent_items_sorted = sorted(recent_items, key=lambda x: x["Timestamp"])

        # 3) ChatGPT 형식으로 메시지 변환
        #    - UserID == "chatgpt" 인 경우 role="assistant"
        #    - 그렇지 않은 경우 role="user"
        conversation = []
        for item in recent_items_sorted:
            role = "assistant" if item["UserID"] == "chatgpt" else "user"
            content = item["Message"]
            conversation.append({"role": role, "content": content})

        # 이번에 들어온 사용자 메시지도 대화에 추가
        conversation.append({"role": "user", "content": user_message_content})

        # 4) OpenAI API 호출
        api_key = os.environ.get("OPENAI_APIKEY")
        try:
            chat_response = postToOpenai.call_openai_api(conversation, api_key)
            print(chat_response)
        except Exception as e:
            print("[Error] call_openai_api failed:", e)
            chat_response = f"Error: {str(e)}"

        # 5) 결과(챗봇의 답변)를 DynamoDB에 저장
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

        # 6) WebSocket 브로드캐스트
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
                    # 연결 끊긴 유저 → DynamoDB에서 제거
                    if e.response["Error"]["Code"] == "GoneException":
                        table_users.delete_item(Key={"ConnectionID": connection_id})
                    else:
                        print("[Error] post_to_connection failed:", e)
        except ClientError as e:
            print("[Error] query userList failed:", e)

    return {
        "statusCode": 200,
        "body": json.dumps("SQS batch processed.")
    }
