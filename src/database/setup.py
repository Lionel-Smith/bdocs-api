from src.database.SQLReader import SQLReader
from src.database.oracle_db_service import OracleDBService
import os
from cx_Oracle import DatabaseError

class DBSetup(SQLReader):
    def __init__(self):
        self.db = OracleDBService()
        self.scriptPath = os.path.join(os.path.dirname(__file__), "scripts")

    def schemaExists(self) -> bool:
        results = self.db.cursor.execute("select count(*) user_exists from dba_users where username='ONLINE_CLAIMS'")
        rows = results.fetchall()
        if rows and rows[0][0] == 1:
            return True
        return False

    def initializeDB(self):
        createUser = self.getSQL(os.path.join(self.scriptPath,"createApplicationUser.sql"))
        applyUserProfile = self.getSQL(os.path.join(self.scriptPath,"applyUserProfile.sql"))
        grantUserPrivileges = self.getSQL(os.path.join(self.scriptPath,"grantUserPrivileges.sql")).split(";")
        try:
            self.db.cursor.execute(createUser)
        except DatabaseError as e:
            error, = e.args
            #Error code 1920 raised by oracle if user already exists
            if error.code in [1920]:
                pass
            else:
                raise e
        self.db.cursor.execute(applyUserProfile)
        for privilege in grantUserPrivileges:
            if privilege:
                self.db.cursor.execute(privilege)