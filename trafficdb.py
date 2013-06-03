import sqlite3
import logging
from time import time
from threading import Lock

log = logging.getLogger("pyxie")
mutex = Lock()


class TrafficDB:


    filename = None

    def __init__(self, filename=":memory:"):

        self.filename = filename
        self.create_tables()

    def create_tables(self):

        con = sqlite3.connect(self.filename)
        cursor = con.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS streams
        (
            id INTEGER PRIMARY KEY,
            srcip INTEGER,
            srcport TEXT,
            dstip INTEGER,
            dstport TEXT,
            proto TEXT
        )
        """)
        con.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic
        (
            id INTEGER PRIMARY KEY,
            streamid INTEGER,
            timestamp TEXT,
            direction INTEGER,
            modified INTEGER,
            payload BLOB,
            FOREIGN KEY(streamid) REFERENCES streams(streamid)
        )
        """)
            
        con.commit()
        con.close()
        
    def add_stream(self, stream):

        mutex.acquire()
        con = sqlite3.connect(self.filename)
        cursor = con.cursor()

        stmt = """INSERT INTO streams(srcip, srcport, dstip, dstport, proto)
                  VALUES (?, ?, ?, ?, ?)"""
        srcip, srcport = stream.client.getpeername()
        dstip, dstport = stream.server.getpeername()
        proto = stream.proto_name

        cursor.execute(stmt, (srcip, srcport, dstip, dstport, proto))
        streamid = cursor.lastrowid

        con.commit()
        con.close()
        mutex.release()

        return streamid

    def add_traffic(self, stream, sid, direc, ismodified, data):

        mutex.acquire()
        con = sqlite3.connect(self.filename)
        cursor = con.cursor()

        stmt = """INSERT INTO traffic (streamid, timestamp, direction, modified, payload)
                  VALUES (?, ?, ?, ?, ?)"""

        cursor.execute(stmt, (sid, time(), direc, ismodified, data))
        trafficid = cursor.lastrowid

        con.commit()
        con.close()
        mutex.release()

        return trafficid
