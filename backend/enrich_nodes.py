import asyncio, aiomysql, sys
sys.path.insert(0, r'D:\CodeBase\student_learn\backend')
sys.path.insert(0, r'D:\CodeBase\student_learn\backend\settings')
from openai import AsyncOpenAI
from settings import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

async def enrich_node(cur, node_id, title, parent_title):
    await cur.execute('SELECT content FROM knowledge_node WHERE id=%s', (node_id,))
    row = await cur.fetchone()
    current = row[0] or ''
    if len(current) > 300:
        print(f'  [{title}] SKIP ({len(current)} chars)')
        return

    prompt = f'作为《人工智能导论》教师，请为以下知识点编写详细教学内容（300-500字）：\n所属章节：{parent_title}\n知识点：{title}\n要求：概念定义清晰、包含核心原理/算法、1-2个实际应用例子、语言通俗适合本科生、不使用markdown格式'
    
    try:
        resp = await client.chat.completions.create(model=LLM_MODEL, messages=[{'role': 'user', 'content': prompt}], temperature=0.3, max_tokens=1500)
        content = resp.choices[0].message.content
        await cur.execute('UPDATE knowledge_node SET content=%s WHERE id=%s', (content, node_id))
        print(f'  [{title}] DONE ({len(content)} chars)')
    except Exception as e:
        print(f'  [{title}] ERROR: {e}')

async def main():
    conn = await aiomysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', db='student_learn')
    async with conn.cursor() as cur:
        await cur.execute("SELECT id, title FROM knowledge_node WHERE parent_id IS NULL")
        chapters = await cur.fetchall()
        for ch in chapters:
            print(f'\n=== {ch[1]} ===')
            await cur.execute("SELECT id, title FROM knowledge_node WHERE parent_id=%s", (ch[0],))
            sections = await cur.fetchall()
            for sec in sections:
                await enrich_node(cur, sec[0], sec[1], ch[1])
                await conn.commit()
        print('\nDone!')
    conn.close()

asyncio.run(main())
