import os
import platform

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from sqlite.sqlite_procs import getDbPath

db_session = None

db_sessions_dict = {}
def listDbSessions():
    for temp_session in iter(db_sessions_dict):
        print(f'{db_sessions_dict[temp_session].bind.url.database}')

def getAlchemySession(db_name: str = 'AttendanceV3.db'):
    if db_name in db_sessions_dict:
        return db_sessions_dict[db_name]
    engine  = create_engine(f'sqlite:///{getDbPath(db_name)}')
    session = sessionmaker(bind=engine)
    db_sessions_dict[db_name] = session()
    return session()
