import sqlite3


class TrafficDB:
    def __init__(self, filename=":memory:"):
        con = None
        try:
            con = sqlite3.connect(filename)
            cursor = con.cursor()
            cursor.execute("""
            create table if not exists traffic(
                id integer primary key,
                date text,
                ip text,
                port integer,
                direction int,
                payload blob 
            )
            """);
            con.commit()
            con.close()
                    
        except:
            con.close()
            raise
