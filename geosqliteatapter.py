import sqlite3

class SqliteAdapter:
    def __init__(self, database):
        self.__db_connection = sqlite3.connect(database)
        self.init_database()

    def __del__(self):
        self.__db_connection.close()

    def init_database(self):
        cursor = self.__db_connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS GeoStats ( _id INTEGER AUTO_INCREMENT , date TEXT, h INTEGER, d INTEGER, z INTEGER, f INTEGER, point_count INTEGER,observatory_fk INTEGER,  delay_fk ,PRIMARY KEY(_id), FOREIGN KEY(observatory_fk) REFERENCES Locations(_id), FOREIGN KEY(delay_fk) REFERENCES Delays(_id) )")
        cursor.execute("CREATE TABLE IF NOT EXISTS Locations( _id INTEGER, observatory_name TEXT, PRIMARY KEY(_id) )" )
        cursor.execute("CREATE TABLE IF NOT EXISTS Delays ( _id INTEGER AUTO_INCREMENT, delay INTEGER, PRIMARY KEY(_id) ) ") #### Delay is in seconds ####
        self.__db_connection.commit();
        #### Setup Observatory locations ####
        cursor.execute("SELECT _id FROM Locations")
        count = len( cursor.fetchall() )
        if count == 0:
            self.insert_observatory("FRD")
            self.insert_observatory("BOU")
            self.insert_observatory("BDT")

        #### Setup available delays ####
        cursor.execute("SELECT _id FROM Delays")
        count = len( cursor.fetchall() )
        if count == 0:
            self.insert_delay(0)
            self.insert_delay(60)
            self.insert_delay(300)
            self.insert_delay(600)
            self.insert_delay(900)

    def insert_observatory(self, location):
        cursor = self.__db_connection.cursor()
        cursor.execute("INSERT INTO Locations (observatory_name) VALUES(?)", (location,) )
        self.__db_connection.commit()

    def insert_delay(self, delay):
        cursor = self.__db_connection.cursor()
        cursor.execute("INSERT INTO Delays (delay) VALUES(?)", (delay,) )
        self.__db_connection.commit()

    def select_stat(self, location, type, delay):
        cursor = self.__db_connection.cursor()
        cursor.execute("SELECT ?, point_count FROM GeoStats INNER JOIN Locations ON observatory_fk = Locations._id INNER JOIN delay_fk = Delays._id where Locations._id = ? and Delays._id = ?")