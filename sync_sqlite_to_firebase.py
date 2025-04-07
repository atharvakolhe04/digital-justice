import sqlite3
import firebase_admin
from firebase_admin import credentials, db
import time
import subprocess
import os

# Firebase setup
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://digitaljustice-5e563-default-rtdb.firebaseio.com/'
})

# SQLite setup
sqlite_path = r"instance\digital_justice.db"

def fetch_data():
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    data = {}
    for (table,) in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
        data[table] = [dict(zip(col_names, row)) for row in rows]

    conn.close()
    return data

def sync_to_firebase():
    data = fetch_data()
    for table, records in data.items():
        ref = db.reference(f"/{table}")
        ref.set(records)  # replaces all data for that table

# Looping to make it near-realtime (every 5 seconds)
while True:
    subprocess.Popen(['python', 'users_realtime_split.py'])
    sync_to_firebase()
    print("Synced to Firebase.")
    time.sleep(5)
