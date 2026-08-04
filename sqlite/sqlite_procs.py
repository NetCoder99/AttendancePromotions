import os
import sqlite3
import platform


# ----------------------------------------------------------------------------
def getDbPath(db_name: str = 'AttendanceV3.db'):
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('APPDATA'), 'Attendance', db_name)
    else:
        return os.path.join('/', 'Attendance', db_name)

# ----------------------------------------------------------------------------
def DictFactory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# ----------------------------------------------------------------------------
def CursorToDict(cursor: any):
    return_dict = []
    rows = cursor.fetchall()
    for row in rows:
        return_dict.append(dict(row)) # Convert sqlite3.Row to a standard dictionary
    return return_dict

# ----------------------------------------------------------------------------
def GetDataNoArgs(queryStmt):
    try:
        db_path = getDbPath()
        dbObj = sqlite3.connect(db_path)
        dbObj.row_factory = DictFactory
        cursor = dbObj.cursor()
        cursor.execute(queryStmt)
        rows = cursor.fetchall()
        dbObj.close()
        return rows
    except Exception as ex:
        print(f'Error: {ex.__str__()}')

# ----------------------------------------------------------------------------
def GetDataWithArgs(queryStmt, queryDict):
    try:
        db_path = getDbPath()
        dbObj = sqlite3.connect(db_path)
        dbObj.row_factory = DictFactory
        cursor = dbObj.cursor()
        cursor.execute(queryStmt, queryDict)
        rows = cursor.fetchall()
        dbObj.close()
        return rows
    except Exception as ex:
        print(f'Error: {ex.__str__()}')

# # ----------------------------------------------------------------------------
# def UpdDataWithArgs(queryStmt, queryDict):
#     try:
#         db_path = getDbPath()
#         dbObj = sqlite3.connect(db_path)
#         dbObj.row_factory = DictFactory
#         cursor = dbObj.cursor()
#         cursor.execute(queryStmt, queryDict)
#         dbObj.commit()
#         rows = cursor.fetchall()
#         dbObj.close()
#         return {'lastrowid' : cursor.lastrowid, 'rowcount': cursor.rowcount}
#     except Exception as ex:
#         print(f'Error: {ex.__str__()}')
#         raise ex


#
# def UpsetStudentRecords(db_path: str, student_records: dict):
#     dbObj   = sqlite3.connect(db_path)
#     cursor  = dbObj.cursor()
#     for student_record in student_records:
#         upsert_stmt = UpsetStudentRecordStmt(student_record)
#         print(f'upsert_stmt: {upsert_stmt}')
#         cursor.execute(upsert_stmt)
#     dbObj.commit()
#     dbObj.close()
#
# def UpsetStudentRecordStmt(student_record):
#     return f'''
#         insert into students
#         (
#           badgeNumber,
#           firstName,
#           lastName,
#           namePrefix,
#           email,
#           address,
#           address2,
#           city,
#           country,
#           state,
#           zip,
#           birthdate,
#           phoneHome,
#           phoneMobile,
#           status,
#           memberSince,
#           gender,
#           currentRank,
#           ethnicity
#         )
#         values(
#           '{student_record['badgeNumber']}',
#           '{student_record['firstName']}',
#           '{student_record['lastName']}',
#           '{student_record['namePrefix']}',
#           '{student_record['email']}',
#           '{student_record['address']}',
#           '{student_record['address2']}',
#           '{student_record['city']}',
#           '{student_record['country']}',
#           '{student_record['state']}',
#           '{student_record['zip']}',
#           '{student_record['birthDate']}',
#           '{student_record['phoneHome']}',
#           '{student_record['phoneMobile']}',
#           '{student_record['status']}',
#           '{student_record['memberSince']}',
#           '{student_record['gender']}',
#           '{student_record['currentRank']}',
#           '{student_record['ethnicity']}'
#         )
#         on conflict(badgeNumber)
#         do update set
#           firstName     = '{student_record['firstName']}',
#           lastName      = '{student_record['lastName']}',
#           namePrefix    = '{student_record['namePrefix']}',
#           email         = '{student_record['email']}',
#           address       = '{student_record['address']}',
#           address2      = '{student_record['address2']}',
#           city          = '{student_record['city']}',
#           country       = '{student_record['country']}',
#           state         = '{student_record['state']}',
#           zip           = '{student_record['zip']}',
#           birthDate     = '{student_record['birthDate']}',
#           phoneHome     = '{student_record['phoneHome']}',
#           phoneMobile   = '{student_record['phoneMobile']}',
#           status        = '{student_record['status']}',
#           memberSince   = '{student_record['memberSince']}',
#           gender        = '{student_record['gender']}',
#           currentRank   = '{student_record['currentRank']}',
#           ethnicity     = '{student_record['ethnicity']}'
#     '''
#
# # ----------------------------------------------------------------------------
# def CreateAttendanceTable(db_path: str):
#     connection_obj = sqlite3.connect(db_path)
#     cursor_obj = connection_obj.cursor()
#     cursor_obj.execute("DROP TABLE IF EXISTS attendance")
#     table = """ CREATE TABLE attendance
#     (
#         attendance_id  INTEGER PRIMARY KEY,
#         badgeNumber     int,
#         checkinDateTime text,
#         checkinDate     text,
#         checkinTime     text,
#         studentName     text,
#         studentStatus   text,
#         className       text,
#         rankName        text,
#         classStartTime  text
#     ); """
#
#     cursor_obj.execute(table)
#     print("Table is Ready")
#     connection_obj.close()
#
# def InsertAttendanceRecords(db_path: str, attendance_records: dict):
#     dbObj   = sqlite3.connect(db_path)
#     cursor  = dbObj.cursor()
#     for attendance_record in attendance_records:
#         insert_stmt = InsertAttendanceRecordStmt(attendance_record)
#         print(f'insert_stmt: {insert_stmt}')
#         cursor.execute(insert_stmt)
#     dbObj.commit()
#     dbObj.close()
#
# def InsertAttendanceRecordStmt(student_record):
#     return f'''
#         insert into attendance
#         (
#             badgeNumber,
#             checkinDateTime,
#             checkinDate,
#             checkinTime,
#             studentName,
#             studentStatus,
#             className,
#             rankName,
#             classStartTime
#         )
#         values(
#           "{student_record['badgeNumber']}',
#           "{student_record['checkinDateTime']}',
#           "{student_record['checkinDate']}',
#           "{student_record['checkinTime']}',
#           "{student_record['studentName']}',
#           "{student_record['studentStatus']}',
#           "{student_record['className']}',
#           "{student_record['rankName']}',
#           "{student_record['classStartTime']}"
#         )
#     '''
#
# def InsertAttendanceImports(db_path: str, attendance_records: dict):
#     dbObj   = sqlite3.connect(db_path)
#     cursor  = dbObj.cursor()
#     for attendance_record in attendance_records:
#         insert_stmt = InsertAttendanceImportStmt(attendance_record)
#         print(f'insert_stmt: {insert_stmt}')
#         cursor.execute(insert_stmt)
#     dbObj.commit()
#     dbObj.close()
#
# def InsertAttendanceImportStmt(attendance_record):
#     return f'''
#         insert into attendance_import
#         (
#              badgeNumber
#             ,studentBirthDate
#             ,studentBirthDateSong
#             ,className
#             ,attendanceDate
#             ,attendanceHours
#             ,attendanceRankName
#             ,attendanceRankNum
#             ,attendanceStudentName
#             ,attendanceCheckinTimeIn
#             ,attendanceCheckinDateTime
#             ,attendanceCheckinDayName
#             ,attendanceTimeStamp
#             ,attendanceWeekofYear
#             ,attendanceScannedNum
#             ,attendanceStudentNum
#             ,attendanceStyleName
#             ,rankNum
#         )
#         values(
#              CAST({attendance_record['attendanceScannedNum']} AS INTEGER),
#             '{attendance_record['studentBirthDate']}',
#             '{attendance_record['studentBirthDateSong']}',
#             '{attendance_record['className']}',
#             '{attendance_record['attendanceDate']}',
#             '{attendance_record['attendanceHours']}',
#             '{attendance_record['attendanceRankName']}',
#             '{attendance_record['attendanceRankNum']}',
#             '{attendance_record['attendanceStudentName']}',
#             '{attendance_record['attendanceCheckinTimeIn']}',
#             '{attendance_record['attendanceCheckinDateTime']}',
#             '{attendance_record['attendanceCheckinDayName']}',
#             '{attendance_record['attendanceTimeStamp']}',
#             '{attendance_record['attendanceWeekofYear']}',
#             '{attendance_record['attendanceScannedNum']}',
#             '{attendance_record['attendanceStudentNum']}',
#             '{attendance_record['attendanceStyleName']}',
#             '{attendance_record['rankNum']}'
#         )
#     '''
#
# def convertAttdImportToAttdStmt():
#     return '''
#         SELECT  null as attendance_id
#             ,CAST(attd.attendanceScannedNum as integer)   as badgeNumber
#             ,attd.attendanceCheckinDateTime               as checkinDateTime    -- 2019-06-15 08:53:00
#             ,substr(attd.attendanceDate, 6, 2) || '/' ||
#             substr(attd.attendanceDate, 9, 2) || '/' ||
#             substr(attd.attendanceDate, 1, 4)            as checkinDate        -- 06/15/2019
#             ,attd .attendanceCheckinTimeIn
#             ,cast(substr(attd .attendanceCheckinTimeIn, 1, 2) as integer )
#             ,case when substr(attd .attendanceCheckinTimeIn, 1, 2) > '11' then 'PM'
#                  else 'AM'
#             end as timeStamp
#             --9:07 AM
#             --3:28 PM
#             --checkinTime,
#             --studentName,
#             --studentStatus,
#             --className,
#             --rankName,
#             --classStartTime
#         FROM   attendance_import   attd
#         --where  attd.attendanceScannedNum = '1565'
#         order  by attd.attendanceCheckinDateTime asc;
# '''