import json
import onConnect
import onDisconnect

def lambda_handler(event, context):
    print(event)
    """
    WebSocket 라우팅 ($connect, $disconnect, $default)
    """
    # WebSocket 이벤트인지 확인
    if "requestContext" in event and "routeKey" in event["requestContext"]:
        route_key = event["requestContext"]["routeKey"]

        if route_key == "$connect":
            return onConnect.on_connect(event)

        elif route_key == "$disconnect":
            return onDisconnect.on_disconnect(event)

        elif route_key == "$default":
            # $default 라우트 처리 로직
            # 예: 수신한 메시지(body) 에코하기
            body_str = event.get("body", "")
            try:
                body_json = json.loads(body_str) if body_str else {}
            except json.JSONDecodeError:
                body_json = {}

            # 필요한 처리 로직 삽입 (DB 저장, 브로드캐스트 등)
            # 여기서는 단순히 메시지 구조를 반환하는 예시
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "route": "$default",
                    "receivedData": body_json
                })
            }

        else:
            # 설정되지 않은 라우트 키가 들어오면 400 반환
            return {
                "statusCode": 400,
                "body": json.dumps("Unsupported WebSocket route")
            }

    # 기타 이벤트
    return {
        "statusCode": 400,
        "body": json.dumps("Bad Request: Unsupported event type.")
    }
