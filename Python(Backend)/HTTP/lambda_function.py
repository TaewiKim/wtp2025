import json
import get
import put

def lambda_handler(event, context):
    """
    HTTP API 라우팅 (GET /dev/chat, PUT /dev/chat)
    """
    # HTTP API 이벤트인지 확인
    if "requestContext" in event and "http" in event["requestContext"]:
        method = event["requestContext"]["http"]["method"]
        if method == "GET":
            return get.get_messages(event)
        elif method == "PUT":
            response = put.put_message(event)
            response["headers"] = {
                "Access-Control-Allow-Origin": "*",  # 모든 도메인에서 요청 허용
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT",  # 허용할 메서드
                "Access-Control-Allow-Headers": "Content-Type"  # 허용할 헤더
            }
            print(response)
            return response
        elif method == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",                  # 허용할 도메인 (*: 모든 도메인 허용)
                    "Access-Control-Allow-Methods": "OPTIONS, GET, PUT", # 허용할 메서드
                    "Access-Control-Allow-Headers": "Content-Type"       # 허용할 요청 헤더
                },
                "body": ""
            }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps(f"Unsupported HTTP method: {method}")
            }

    # 3) 기타 이벤트 (SQS, etc.)를 이 Lambda에 연결하지 않았다면 처리 불가
    return {
        "statusCode": 400,
        "body": json.dumps("Bad Request: Unsupported event type.")
    }
