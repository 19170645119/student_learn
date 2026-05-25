import json
import httpx
import settings

class SparkService:
    def __init__(self):
        self.url = settings.SPARK_API_URL
        self.password = settings.SPARK_API_PASSWORD

    async def chat(self, messages: list) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.password}"
        }
        payload = {
            "model": "spark",
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 4096,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.url, json=payload, headers=headers)
                text = response.text
                if response.status_code != 200:
                    print(f"[Spark] HTTP {response.status_code}: {text[:300]}")
                    return f"[API Error] {text[:300]}"

                data = json.loads(text)
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")

                payload_data = data.get("payload", {})
                text_list = payload_data.get("choices", {}).get("text", [])
                if text_list:
                    return text_list[0].get("content", "")

                return str(data)
        except Exception as e:
            print(f"[Spark] Error: {e}")
            return f"[Error] {e}"


spark_service = SparkService()
