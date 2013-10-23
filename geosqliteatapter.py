import sqlite3

class SqliteAdapter:
    def __init__(self, database):
        self.__db_connection = sqlite3.connect(database)
        self.init_database()

    def init_database(self):
        cursor = self.__db_connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS GeoStats ( _id INTEGER AUTO_INCREMENT , date TEXT, h INTEGER, d INTEGER, z INTEGER, f INTEGER, observatory INTEGER ,PRIMARY KEY(_id), FOREIGN KEY(observatory) REFERENCES Locations(_id) )")
        cursor.execute("CREATE TABLE IF NOT EXISTS Locations( _id INTEGER, observatory_name TEXT, PRIMARY KEY(_id) )" )
        self.__db_connection.commit();
        cursor.execute("SELECT _id FROM Locations")
        count = len( cursor.fetchall() )
        if count == 0:
            cursor.execute("INSERT INTO Locations (observatory_name) VALUES( 'FRD')")
            cursor.execute("INSERT INTO Locations (observatory_name) VALUES( 'BOU')")
            cursor.execute("INSERT INTO Locations (observatory_name) VALUES( 'BDT')")
            self.__db_connection.commit()