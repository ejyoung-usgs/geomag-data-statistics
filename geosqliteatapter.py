import sqlite3

class SqliteAdapter:

    def __init__(self, database):
        self.__db_connection = sqlite3.connect(database)
        self.__delays = [0, 60, 300, 600, 900]
        self.__locations = ["FRD", "BOU", "BDT"]
        self.init_database()

    def __del__(self):
        self.__db_connection.close()

    def init_database(self):
        cursor = self.__db_connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS GeoStats ( _id INTEGER , h INTEGER, d INTEGER, z INTEGER, f INTEGER, point_count INTEGER,observatory_fk INTEGER,  delay_fk ,PRIMARY KEY(_id), FOREIGN KEY(observatory_fk) REFERENCES Locations(_id), FOREIGN KEY(delay_fk) REFERENCES Delays(_id) )")
        cursor.execute("CREATE TABLE IF NOT EXISTS Locations( _id INTEGER, observatory_name TEXT, PRIMARY KEY(_id) )" )
        cursor.execute("CREATE TABLE IF NOT EXISTS Delays ( _id INTEGER, delay INTEGER, PRIMARY KEY(_id) ) ") #### Delay is in seconds ####
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

        for id in self.__locations:
            check_stat_query = "select * from GeoStats where observatory_fk=? and delay_fk=?"
            location_id = self.find_location_id_by_name(id)
            for delay in self.__delays:
                delay_id = self.find_delay_id_by_value(delay)
                cursor.execute(check_stat_query, (location_id, delay_id,) )
                results = cursor.fetchall()
                if len(results ) == 0 :
                    self.__insert_stat(location_id, delay_id)

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
        cursor.execute("SELECT ?, point_count FROM GeoStats INNER JOIN Locations ON observatory_fk = Locations._id INNER JOIN delay_fk = Delays._id where Locations._id = ? and Delays._id = ?", (type, location, delay,))

    def __insert_stat(self, location, delay):
        cursor = self.__db_connection.cursor()
        query = "insert into GeoStats(observatory_fk, delay_fk, h, d, z, f, point_count) values (?, ? , 0, 0, 0, 0, 0)"
        cursor.execute( query, (location, delay,) )
        self.__db_connection.commit()

    def find_location_id_by_name(self, name):
        cursor = self.__db_connection.cursor()
        query = "select _id from Locations where observatory_name = ?"
        cursor.execute(query, (name,))
        return cursor.fetchall()[0][0]
    def find_delay_id_by_value(self, delay):
        cursor = self.__db_connection.cursor()
        query = "select _id from Delays where delay=?"
        cursor.execute(query, (delay,) )
        return cursor.fetchall()[0][0]

    def update_geostat(self, id, h, d, z, f, point_count):
        cursor = self.__db_connection.cursor()
        query = "update GeoStats set h=?, d=?, z=?, f=?, point_count=? where _id=?"
        cursor.execute(query, (h, d, z, f, point_count, id,) )
        self.__db_connection.commit()