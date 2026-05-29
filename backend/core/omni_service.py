import os, base64, tempfile
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY", ""),
)


async def omni_chat(messages: list) -> str:
    """Text generation using qwen-omni-turbo (native multimodal model)"""
    try:
        resp = await client.chat.completions.create(
            model="qwen-omni-turbo",
            messages=messages, temperature=0.7, max_tokens=2048,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[Omni] chat error: {e}")
        return f"[Error] {e}"


async def omni_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str | None:
    """TTS via Microsoft Edge TTS (free, natural Chinese voice). Returns base64 mp3."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        await communicate.save(tmp.name)
        with open(tmp.name, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        os.unlink(tmp.name)
        print(f"[EdgeTTS] Generated {len(data)} chars base64 audio")
        return data
    except Exception as e:
        print(f"[EdgeTTS] error (fallback to browser TTS): {e}")
        return None
