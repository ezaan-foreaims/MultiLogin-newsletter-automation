# db.py
import psycopg2

def test_connection():
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="newsletters",
            user="ezaan-amin",
            password="123456789"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("✅ Connected to:", db_version)
        return True

    except Exception as e:
        print("❌ Error connecting to PostgreSQL:", e)
        return False

    finally:
        if 'connection' in locals() and connection:
            cursor.close()
            connection.close()
            print("🔒 Connection closed.")
