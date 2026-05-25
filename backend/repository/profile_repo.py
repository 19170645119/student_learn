from models import AsyncSession
from models.profile import StudentProfile
from sqlalchemy import select

class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> StudentProfile | None:
        return await self.session.scalar(
            select(StudentProfile).filter(StudentProfile.user_id == user_id)
        )

    async def create_or_update(self, user_id: int, **kwargs) -> StudentProfile:
        profile = await self.session.scalar(
            select(StudentProfile).filter(StudentProfile.user_id == user_id)
        )
        if profile:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(profile, key, value)
        else:
            profile = StudentProfile(user_id=user_id, **kwargs)
            self.session.add(profile)
        return profile

    async def get_by_id(self, profile_id: int) -> StudentProfile | None:
        return await self.session.scalar(
            select(StudentProfile).filter(StudentProfile.id == profile_id)
        )
