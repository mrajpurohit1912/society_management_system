from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def safe_transaction(db: AsyncSession):
    """
    Context manager that safely executes operations within an active or new transaction.
    """
    if db.in_transaction():
        yield
        await db.commit()
    else:
        async with db.begin():
            yield
