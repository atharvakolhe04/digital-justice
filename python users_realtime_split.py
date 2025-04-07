import sqlite3
import time

db_path = r"instance\digital_justice.db"

def split_users_by_role():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all users
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()

    # Get column names
    col_names = [description[0] for description in cursor.description]

    # Check if 'role' or similar exists
    if 'role' not in col_names and 'user_type' not in col_names:
        print("❌ No role or user_type column found. Add one to split users.")
        conn.close()
        return

    role_column = 'role' if 'role' in col_names else 'user_type'

    # Define role-specific tables
    roles = ['citizen', 'admin', 'police', 'court']

    for role in roles:
        table_name = f"{role}_users"
        
        # Create role-specific table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} AS
            SELECT * FROM users WHERE 1=0
        """)

        # Clear existing entries (optional for full sync)
        cursor.execute(f"DELETE FROM {table_name}")

        # Insert filtered users into respective role table
        cursor.execute(f"""
            INSERT INTO {table_name}
            SELECT * FROM users WHERE {role_column} = ?
        """, (role,))
        
        print(f"✅ Synced role: {role} → {table_name}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🔁 Starting real-time user role sync...")
    while True:
        split_users_by_role()
        time.sleep(5)  # Sync every 5 seconds
