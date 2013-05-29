import config
import logging
from time import time

import psycopg2

import config

log = logging.getLogger("pyxie")

class TrafficDB:


    def __init__(self):

        try:
            self.create_tables()

        except psycopg2.ProgrammingError:
            pass

    def drop_tables(self):

        try:
            con = psycopg2.connect(config.dsn)
            cursor = con.cursor()
            cursor.execute("""
            DROP TABLE traffic;
            DROP TABLE streams;
            """)

        except psycopg2.ProgrammingError:
            pass

    def create_tables(self):

        try:
            con = psycopg2.connect(config.dsn)
            cursor = con.cursor()
            cursor.execute("""
            CREATE TABLE streams
            (
                id          SERIAL PRIMARY KEY,
                srcip       VARCHAR(16),
                srcport     INT,
                dstip       VARCHAR(16),
                dstport     INT,
                proto       VARCHAR(20)
            );
            CREATE TABLE IF NOT EXISTS traffic
            (
                id          SERIAL      PRIMARY KEY,
                streamid    INT         REFERENCES streams(id),
                timestamp   TEXT,
                direction   BOOLEAN,
                modified    BOOLEAN,
                payload     BYTEA
            )
            """)
        
        except psycopg2.ProgrammingError:
            raise
                
        finally:
            con.commit()
            con.close()
        
    def add_stream(self, stream):

        con = psycopg2.connect(config.dsn)
        cursor = con.cursor()

        stmt = """INSERT INTO streams (srcip, srcport, dstip, dstport, proto) VALUES (%s, %s, %s, %s, %s)"""
        srcip, srcport = stream.client.getpeername()
        dstip, dstport = stream.server.getpeername()
        proto = stream.proto_name

        cursor.execute(stmt, (srcip, srcport, dstip, dstport, proto))
        con.commit()
        
        cursor.execute('SELECT LASTVAL()')
        streamid = cursor.fetchone()[0]
        log.debug("stream id: " + str(streamid))
        con.close()

        return streamid

    def add_traffic(self, stream, direc, ismodified, data):

        con = psycopg2.connect(config.dsn)
        cursor = con.cursor()

        stmt = """INSERT INTO traffic (streamid, timestamp, direction, modified, payload) VALUES (%s, %s, %s, %s, %s)"""

        cursor.execute(stmt, (stream.streamid, time(), direc, ismodified, data))

        con.commit()
        con.close()
