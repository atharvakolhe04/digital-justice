import sqlite3
import time

db_path = r"instance\digital_justice.db"

def get_existing_locations(cursor):
    cursor.execute("SELECT DISTINCT location FROM sos_alerts")
    return [row[0] for row in cursor.fetchall() if row[0] is not None]

def create_location_table(cursor, location):
    table_name = f"sos_{location.lower().replace(' ', '_')}_alerts"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} AS
        SELECT * FROM sos_alerts WHERE 1=0
    """)
    return table_name

def sync_alerts_for_location(cursor, location):
    table_name = f"sos_{location.lower().replace(' ', '_')}_alerts"

    # Create table if it doesn’t exist
    create_location_table(cursor, location)

    # Clear old data (optional)
    cursor.execute(f"DELETE FROM {table_name}")

    # Insert current alerts for the location
    cursor.execute(f"""
        INSERT INTO {table_name}
        SELECT * FROM sos_alerts WHERE location = ?
    """, (location,))

def split_sos_alerts_by_location():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    locations = get_existing_locations(cursor)

    for location in locations:
        sync_alerts_for_location(cursor, location)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🚨 Starting realtime location-wise sync of sos_alerts...")
    while True:
        split_sos_alerts_by_location()
        print("✅ Synced sos_alerts by location.")
        time.sleep(5)  # sync every 5 seconds
