import os
import sqlite3
from datetime import datetime

from blockchain import generate_block_hash


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "database.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER,
    certificate_id TEXT UNIQUE NOT NULL,
    student_name TEXT NOT NULL,
    register_number TEXT NOT NULL,
    course TEXT NOT NULL,
    institution TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    file_name TEXT NOT NULL,
    qr_code TEXT NOT NULL,
    certificate_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    block_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'VALID',
    revoked_at TEXT
)
        """
    )
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        college_name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """
)
    cursor.execute("PRAGMA table_info(certificates)")

    existing_columns = {
        column["name"] for column in cursor.fetchall()
    }

    if "status" not in existing_columns:
        cursor.execute(
            """
            ALTER TABLE certificates
            ADD COLUMN status TEXT NOT NULL DEFAULT 'VALID'
            """
        )

    if "revoked_at" not in existing_columns:
        cursor.execute(
            """
            ALTER TABLE certificates
            ADD COLUMN revoked_at TEXT
            """
        )

    cursor.execute("""
INSERT OR IGNORE INTO admins
(college_name, username, password)
VALUES
('KIOT','kiotadmin','kiot@12345')
""")

    cursor.execute("""
INSERT OR IGNORE INTO admins
(college_name, username, password)
VALUES
('PSG','psgadmin','psg@12345')
""")

    cursor.execute("""
INSERT OR IGNORE INTO admins
(college_name, username, password)
VALUES
('MIT','mitadmin','mit@12345')
""")

    connection.commit()
    connection.close()


def get_previous_block_hash():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT block_hash
        FROM certificates
        ORDER BY id DESC
        LIMIT 1
        """
    )

    record = cursor.fetchone()
    connection.close()

    if record:
        return record["block_hash"]

    return "0"


def insert_certificate(
    admin_id,
    certificate_id,
    student_name,
    register_number,
    course,
    institution,
    issue_date,
    file_name,
    qr_code,
    certificate_hash
):
    previous_hash = get_previous_block_hash()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    block_hash = generate_block_hash(
        certificate_id,
        student_name,
        register_number,
        course,
        institution,
        issue_date,
        certificate_hash,
        previous_hash,
        timestamp
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO certificates (
            admin_id,
            certificate_id,
            student_name,
            register_number,
            course,
            institution,
            issue_date,
            file_name,
            qr_code,
            certificate_hash,
            previous_hash,
            block_hash,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            admin_id,
            certificate_id,
            student_name,
            register_number,
            course,
            institution,
            issue_date,
            file_name,
            qr_code,
            certificate_hash,
            previous_hash,
            block_hash,
            timestamp
        )
    )

    connection.commit()
    connection.close()


def get_certificate_by_id(certificate_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM certificates
        WHERE certificate_id = ?
        """,
        (certificate_id,)
    )

    certificate = cursor.fetchone()
    connection.close()

    return certificate


def get_all_certificates():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM certificates
        ORDER BY id ASC
        """
    )

    certificates = cursor.fetchall()
    connection.close()

    return certificates


def verify_blockchain_integrity():
    certificates = get_all_certificates()

    previous_hash = "0"

    for certificate in certificates:
        recalculated_hash = generate_block_hash(
            certificate["certificate_id"],
            certificate["student_name"],
            certificate["register_number"],
            certificate["course"],
            certificate["institution"],
            certificate["issue_date"],
            certificate["certificate_hash"],
            certificate["previous_hash"],
            certificate["created_at"]
        )

        if certificate["previous_hash"] != previous_hash:
            return False

        if certificate["block_hash"] != recalculated_hash:
            return False

        previous_hash = certificate["block_hash"]

    return True


def delete_certificate(certificate_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM certificates
        WHERE certificate_id = ?
        """,
        (certificate_id,)
    )

    connection.commit()
    connection.close()
def search_certificates(search):

    connection=get_connection()

    cursor=connection.cursor()

    keyword=f"%{search}%"

    cursor.execute(

    """

    SELECT *

    FROM certificates

    WHERE

    certificate_id LIKE ?

    OR

    student_name LIKE ?

    OR

    register_number LIKE ?

    ORDER BY id

    """,

    (

    keyword,

    keyword,

    keyword

    )

    )

    certificates=cursor.fetchall()

    connection.close()

    return certificates    
def login_admin(username, password):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM admins
        WHERE username=? AND password=?
    """, (username, password))

    admin = cursor.fetchone()

    connection.close()

    return admin  
def get_admin_certificates(admin_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM certificates
        WHERE admin_id = ?
        ORDER BY id DESC
    """, (admin_id,))

    certificates = cursor.fetchall()

    connection.close()

    return certificates  