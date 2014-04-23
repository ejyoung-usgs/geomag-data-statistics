import postgresql

class PostgresAdapter:

    def __init__(self, uname, database, observatories, delays):
        self.__db_connection = postgresql.open(user = uname, database = database)
        self.__delays = delays
        self.__locations = observatories
        self.init_database()

    def __del__(self):
        self.__db_connection.close()

    def init_database(self):
        self.__db_connection.execute("CREATE TABLE IF NOT EXISTS Locations( _id SERIAL, observatory_name TEXT, PRIMARY KEY(_id) )" )
        self.__db_connection.execute("CREATE TABLE IF NOT EXISTS Delays ( _id SERIAL, delay INTEGER, PRIMARY KEY(_id) ) ") #### Delay is in seconds ####
        self.__db_connection.execute("CREATE TABLE IF NOT EXISTS Resolutions ( _id SERIAL, res TEXT, PRIMARY KEY (_id) )")
        self.__db_connection.execute("CREATE TABLE IF NOT EXISTS GeoStats ( _id SERIAL PRIMARY KEY , h_fail INTEGER, d_fail INTEGER, z_fail INTEGER, f_fail INTEGER, insert_date date, point_count INTEGER, observatory_fk INTEGER,  res_fk INTEGER, delay_fk INTEGER, FOREIGN KEY(observatory_fk) REFERENCES Locations(_id), FOREIGN KEY(delay_fk) REFERENCES Delays(_id), FOREIGN KEY(res_fk) REFERENCES Resolutions(_id) )")

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
        statement = self.__db_connection.prepare("INSERT INTO Locations (observatory_name) VALUES($1)")
        statement(location)

    def insert_resolution(self, res):
        statement = self.__db_connection.prepare("INSERT INTO Resolutions (res) VALUES($1)")
        statement(res)

    def insert_delay(self, delay):
        statement = self.__db_connection.prepare("INSERT INTO Delays (delay) VALUES($1)")
        statement(delay)

    def find_location_id_by_name(self, name):
        query =  self.__db_connection.prepare("SELECT _id FROM Locations WHERE observatory_name = $1")
        return query.first(name)

    def find_delay_id_by_value(self, delay):
        query = self.__db_connection.prepare("SELECT _id FROM Delays WHERE delay=$1")
        return query.first(delay)

    def find_res_id_by_name(self, res):
        query = self.__db_connection.prepare("SELECT _id FROM Resolutions WHERE res=$1")
        return query.first(res)

    def insert_geostat(self, stat):
        obs_key = self.find_location_id_by_name(stat["obs"])
        delay_key = self.find_delay_id_by_value(stat["delay"])
        res_key = self.find_res_id_by_name(stat["res"])

        check_query = self.__db_connection.prepare("SELECT h_fail, d_fail, z_fail, f_fail, point_count FROM GeoStats WHERE observatory_fk = $1 AND delay_fk = $2 AND res_fk = $3 AND insert_date = $4")
        result_map = check_query.first(obs_key, delay_key, res_key, stat["timestamp"])

        if result_map == None:
            query = self.__db_connection.prepare("INSERT INTO GeoStats (observatory_fk, delay_fk, res_fk, h_fail, d_fail, z_fail, f_fail, insert_date, point_count) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)")
            query(obs_key, delay_key, res_key, stat["h"], stat["d"], stat["z"], stat["f"], stat["timestamp"], 1)
        else:
            stat["point_count"] = result_map["point_count"] + 1
            stat["h"] = int(stat["h"]) + result_map["h_fail"]
            stat["d"] = int(stat["d"]) + result_map["d_fail"]
            stat["z"] = int(stat["z"]) + result_map["z_fail"]
            stat["f"] = int(stat["f"]) + result_map["f_fail"]
            query = self.__db_connection.prepare ("UPDATE GeoStats SET h_fail = $1, d_fail = $2, z_fail = $3, f_fail = $4, point_count = $5 WHERE observatory_fk = $6 and delay_fk = $7 and res_fk = $8 and insert_date = $9")
            query(stat["h"], stat["d"], stat["z"], stat["f"], stat["point_count"], obs_key, delay_key, res_key, stat["timestamp"])

    def get_resolutions(self):
        query = self.__db_connection.prepare("SELECT * FROM Resolutions")
        return query.first()

    def get_stats(self, delay, res, obs, filter):
        query = self.__db_connection.prepare("SELECT h_fail, d_fail, z_fail, f_fail, point_count FROM GeoStats INNER JOIN Locations ON observatory_fk = Locations._id INNER JOIN Delays ON delay_fk = Delays._id INNER JOIN Resolutions on res_fk = Resolutions._id WHERE delay = $1 and res = $2 and Locations.observatory_name = $3 and insert_date >= $4")
        return query(delay, res, obs, filter)

    def delete_old(self, timestamp):
        query = self.__db_connection.prepare("DELETE FROM GeoStats WHERE insert_date < $1")
        query(timestamp)
