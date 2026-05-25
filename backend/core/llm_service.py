from openai import AsyncOpenAI
import settings

client = AsyncOpenAI(
    base_url=settings.LLM_BASE_URL,
    api_key=settings.LLM_API_KEY,
)

async def chat(messages: list, model: str = None) -> str:
    try:
        response = await client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[LLM] Error: {e}")
        return f"[Error] {e}"


async def chat_stream(messages: list, model: str = None):
    try:
        stream = await client.chat.completions.create(
            model=model or settings.LLM_MODEL,
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
        print(f"[LLM] Error: {e}")
        yield {"done": True, "full_text": f"[Error] {e}"}
