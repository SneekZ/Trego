from db.models import User
from db.schemas import UserModel

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

async def createUser(session: AsyncSession, userModel: UserModel) -> User:
    newUser = User(
        email=userModel.email,
        lastName=userModel.lastName,
        firstName=userModel.firstName,
        refreshToken=userModel.refreshToken,
        sessionToken=userModel.sessionToken,
        deleted=False
    )

    session.add(newUser)
    await session.commit()
    await session.refresh(newUser)

    return newUser

async def getUserBySessionToken(session: AsyncSession, sessionToken: str) -> User:
    result = await session.execute(select(User).where(User.sessionToken==sessionToken))
    return result.scalar_one_or_none() 

async def patchUserBySessionToken(session: AsyncSession, userModel: UserModel) -> User:
    result = await session.execute(select(User).where(User.email==userModel.email))
    user = result.scalar_one_or_none()
    if not user:
        return None

    if userModel.lastName:
        user.lastName = userModel.lastName
    if userModel.firstName:
        user.firstName = userModel.firstName
    if userModel.refreshToken:
        user.refreshToken = userModel.refreshToken
    if userModel.sessionToken:
        user.sessionToken = userModel.sessionToken

    await session.commit()
    await session.refresh(user)

    return user

async def deleteUser(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email==email))
    user = result.scalar_one_or_none()
    if not user:
        return None

    await session.delete(user)
    await session.commit()

    return user