import json
import http.client

def call_openai_api(messages, api_key):
    """
    http.client를 사용해 OpenAI API의 ChatCompletion을 호출하고
    결과 텍스트를 반환한다.
    """
    conn = http.client.HTTPSConnection("api.openai.com")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # messages: [{"role": "user"|"assistant", "content": "..."}] 형태
    payload = json.dumps({
        "model": "gpt-4o-mini",     # 사용 모델
        "messages": messages,       # 전체 대화 기록 전달
        "max_tokens": 2000,
        "temperature": 0
    })

    try:
        conn.request("POST", "/v1/chat/completions", payload, headers)
        response = conn.getresponse()
        status_code = response.status
        response_data = response.read().decode("utf-8")

        data = json.loads(response_data)
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "(No response from OpenAI)"

    except json.JSONDecodeError:
        print("[Error] Invalid JSON response from OpenAI")
        return "(Invalid JSON response)"
    except Exception as e:
        print(f"[Error] API call failed: {e}")
        return "(Error occurred)"
    finally:
        conn.close()
