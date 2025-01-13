from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class DatabaseHelper:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, url: str, echo: bool = False):
        if self._initialized:
            return

        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            autocommit=False,
        )

        self._initialized = True

    async def session_dependency(self):
        async with self.session_factory() as session:
            yield session
            await session.close()
