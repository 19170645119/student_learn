from models import AsyncSession
from models.user import User, EmailCode
from sqlalchemy import select, exists
from datetime import datetime, timedelta
from schemas.user import UserCreateSchema

class EmailCodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str, code: str) -> EmailCode:
        email_code = EmailCode(email=email, code=code)
        self.session.add(email_code)
        return email_code

    async def check_email_code(self, email: str, code: str) -> bool:
        email_code = await self.session.scalar(
            select(EmailCode).filter(EmailCode.email == email, EmailCode.code == code)
        )
        if not email_code:
            return False
        if (datetime.now() - email_code.created_time) > timedelta(minutes=10):
            return False
        return True

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).filter(User.email == email))

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.scalar(select(User).filter(User.id == user_id))

    async def email_is_exist(self, email: str) -> bool:
        stmt = select(exists().where(User.email == email))
        return await self.session.scalar(stmt)

    async def create(self, user_schema: UserCreateSchema) -> User:
        user = User(**user_schema.model_dump())
        self.session.add(user)
        return user
