# models.py
import psycopg2

def create_table():
    connection = psycopg2.connect(
        host="localhost",
        database="newsletters",
        user="ezaan-amin",
        password="123456789"
    )
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_submissions (
            id SERIAL PRIMARY KEY,
            website_name VARCHAR(255),
            website_url TEXT,
            email_used VARCHAR(255),
            submission_status VARCHAR(50),
            captcha_status VARCHAR(50),
            blocked_status BOOLEAN,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    connection.commit()
    cursor.close()
    connection.close()
    print("✅ Table created successfully!")


def insert_submission(website_name, website_url, email_used, submission_status, captcha_status, blocked_status):
    connection = psycopg2.connect(
        host="localhost",
        database="newsletters",
        user="ezaan-amin",
        password="123456789"
    )
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO newsletter_submissions 
        (website_name, website_url, email_used, submission_status, captcha_status, blocked_status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (website_name, website_url, email_used, submission_status, captcha_status, blocked_status))
    connection.commit()
    cursor.close()
    connection.close()
    print(f"✅ Submission for {website_name} added!")
