from models.question_bank import QuestionBank
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import random


class QuestionBankRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def random_sample(self, chapter_id: int, difficulty: str, count: int) -> list:
        stmt = select(QuestionBank).where(
            QuestionBank.chapter_id == chapter_id,
            QuestionBank.difficulty == difficulty
        )
        result = await self.db.execute(stmt)
        all_rows = list(result.scalars().all())
        sampled = random.sample(all_rows, min(count, len(all_rows)))
        for q in sampled:
            q.usage_count = (q.usage_count or 0) + 1
        return sampled

    async def count_by_chapter(self, chapter_id: int, difficulty: str) -> int:
        stmt = select(func.count()).select_from(QuestionBank).where(
            QuestionBank.chapter_id == chapter_id,
            QuestionBank.difficulty == difficulty
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def batch_insert(self, questions: list[dict]) -> list:
        objs = []
        for q in questions:
            obj = QuestionBank(
                chapter_id=q.get("chapter_id"),
                type=q.get("type", "choice"),
                difficulty=q.get("difficulty", "medium"),
                question=q["question"],
                options=q.get("options"),
                answer=str(q.get("answer", "")),
                explanation=q.get("explanation", ""),
                usage_count=0,
            )
            self.db.add(obj)
            objs.append(obj)
        await self.db.flush()
        return objs
