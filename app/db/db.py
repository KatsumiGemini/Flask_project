import mysql.connector
import os
from flask import g

def get_db_connection():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    return g.db
