import sqlite3

class SqliteAdapter:

    def __init__(self, database, observatories, delays):
        self.__db_connection = sqlite3.connect(database)
        self.__delays = delays
        self.__locations = observatories
        self.init_database()

    def __del__(self):
        self.__db_connection.close()

    def init_database(self):
        cursor = self.__db_connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS GeoStats ( _id INTEGER , h INTEGER, d INTEGER, z INTEGER, f INTEGER, timestamp NUMERIC, observatory_fk INTEGER,  res_fk INTEGER, delay_fk INTEGER,PRIMARY KEY(_id), FOREIGN KEY(observatory_fk) REFERENCES Locations(_id), FOREIGN KEY(delay_fk) REFERENCES Delays(_id), FOREIGN KEY(res_fk) REFERENCES Resolutions(_id) )")
        cursor.execute("CREATE TABLE IF NOT EXISTS Locations( _id INTEGER, observatory_name TEXT, PRIMARY KEY(_id) )" )
        cursor.execute("CREATE TABLE IF NOT EXISTS Delays ( _id INTEGER, delay INTEGER, PRIMARY KEY(_id) ) ") #### Delay is in seconds ####
        cursor.execute("CREATE TABLE IF NOT EXISTS Resolutions ( _id INTEGER, res TEXT, PRIMARY KEY (_id) )")
        self.__db_connection.commit();

        #### Setup available delays ####
        for delay in self.__delays:
            if self.find_delay_id_by_value(delay.seconds) == None:
                self.insert_delay(delay.seconds)

        #### Setup available resolutions ####
        if self.get_resolutions() == None:
            self.insert_resolution("min")
            self.insert_resolution("sec")

        #### Setup Observatory locations ####
        for id in self.__locations:

            if self.find_location_id_by_name(id) == None:
                self.insert_observatory(id)

    def insert_observatory(self, location):
        cursor = self.__db_connection.cursor()
        cursor.execute("INSERT INTO Locations (observatory_name) VALUES(?)", (location,) )
        self.__db_connection.commit()

    def insert_resolution(self, res):
        cursor = self.__db_connection.cursor()
        cursor.execute("INSERT INTO Resolutions (res) VALUES(?)", (res,) )
        self.__db_connection.commit()

    def insert_delay(self, delay):
        cursor = self.__db_connection.cursor()
        cursor.execute("INSERT INTO Delays (delay) VALUES(?)", (delay,) )
        self.__db_connection.commit()

    def find_location_id_by_name(self, name):
        cursor = self.__db_connection.cursor()
        query = "select _id from Locations where observatory_name = ?"
        cursor.execute(query, (name,))
        location_return = cursor.fetchall()
        if len(location_return) == 0:
            return None
        return location_return[0][0]
    def find_delay_id_by_value(self, delay):
        cursor = self.__db_connection.cursor()
        query = "select _id from Delays where delay=?"
        cursor.execute(query, (delay,) )
        delay_return = cursor.fetchall()
        if len(delay_return) == 0:
            return None
        return delay_return[0][0]

    def find_res_id_by_name(self, res):
        cursor = self.__db_connection.cursor()
        query = "select _id from Resolutions where res=?"
        cursor.execute(query, (res,) )
        res_return = cursor.fetchone()
        return res_return[0]

    def insert_geostat(self, stat):
        cursor = self.__db_connection.cursor()
        query = "INSERT INTO GeoStats (observatory_fk, delay_fk, res_fk, h, d, z , f, timestamp) VALUES(?,?,?,?,?,?,?,?)"
        obs_key = self.find_location_id_by_name(stat["obs"])
        delay_key = self.find_delay_id_by_value(stat["delay"])
        res_key = self.find_res_id_by_name(stat["res"])
        cursor.execute(query, (obs_key, delay_key, res_key, stat["h"], stat["d"], stat["z"], stat["f"], stat["timestamp"],) )
        self.__db_connection.commit()

    def get_resolutions(self):
        cursor = self.__db_connection.cursor()
        query = "select * from Resolutions"
        result = cursor.execute(query)
        result_set = result.fetchall()
        if len(result_set) == 0:
            return None
        else:
            return result_set

    def get_stats_for_point(self, delay, res, obs, filter, point_type):
        self.__db_connection.row_factory = sqlite3.Row
        cursor = self.__db_connection.cursor()
        query = "select {type} from GeoStats INNER JOIN Locations ON observatory_fk = Locations._id INNER JOIN Delays on delay_fk = Delays._id INNER JOIN Resolutions on res_fk = Resolutions._id WHERE delay = ? and res = ? and Locations.observatory_name = ? and timestamp >= ?"
        result_set = cursor.execute(query.format(type = point_type), (delay, res, obs, filter,))
        rows = result_set.fetchall()
        result_list = []
        for row in rows:
            result_list.append(row[point_type])
        return result_list

    def delete_old(self, timestamp):
        query = "delete from GeoStats where timestamp < ?"
        cursor = self.__db_connection.cursor()
        cursor.execute(query, (timestamp,))