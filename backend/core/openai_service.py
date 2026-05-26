import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY", ""),
)

async def chat(messages: list) -> str:
    try:
        response = await client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            temperature=0.5,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OpenAI] Error: {e}")
        return f"[Error] {e}"


async def chat_stream(messages: list):
    try:
        stream = await client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            temperature=0.5,
            max_tokens=4096,
            stream=True,
        )
        full_text = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_text += delta.content
                yield {"done": False, "text": delta.content}
        yield {"done": True, "full_text": full_text}
    except Exception as e:
        print(f"[OpenAI] Stream error: {e}")
        yield {"done": True, "full_text": f"[Error] {e}"}