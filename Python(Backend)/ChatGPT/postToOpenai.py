import json
import http.client

def call_openai_api(prompt, api_key):
    """
    http.client를 사용해 OpenAI API를 호출하고
    결과 텍스트를 반환한다.
    """
    conn = http.client.HTTPSConnection("api.openai.com")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],  # ChatGPT API 형식
        "max_tokens": 2000,
        "temperature": 0
    })

    try:
        # 올바른 경로로 POST 요청
        conn.request("POST", "/v1/chat/completions", payload, headers)
        response = conn.getresponse()
        status_code = response.status
        response_data = response.read().decode("utf-8")

        # 응답 데이터를 JSON으로 변환
        data = json.loads(response_data)

        # OpenAI 응답 데이터에서 텍스트 추출
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
