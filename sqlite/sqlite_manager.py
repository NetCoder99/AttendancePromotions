from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from sqlite.sqlite_procs import getDbPath


class sqlite_manager:
    _instance = None

    def __new__(cls, db_name: str = "AttendanceV3.db"):
        if cls._instance is None:
            db_url = f'sqlite:///{getDbPath(db_name)}'
            if db_url is None:
                raise ValueError("Database URL required for initialization")

            cls._instance = super().__new__(cls)

            # 1. The Engine acts as the actual connection pool (Safe as a global singleton)
            cls._instance.engine = create_engine(db_url, pool_pre_ping=True)

            # 2. Create a session factory
            cls._instance.session_factory = sessionmaker(
                bind=cls._instance.engine,
                expire_on_commit=False
            )

            # 3. Use scoped_session to ensure thread-safety
            # This provides a unique Session instance per thread
            cls._instance.scoped_session = scoped_session(cls._instance.session_factory)

        return cls._instance

    @property
    def session(self):
        """Returns the thread-local session."""
        return self._instance.scoped_session()

    def remove_session(self):
        """Closes the current thread's session and removes it from the registry."""
        self._instance.scoped_session.remove()
