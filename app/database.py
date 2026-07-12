import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path: str | None = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = Path(db_path) if db_path else base_dir / "student_management.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    email TEXT
                );

                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    student_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    date_of_birth TEXT,
                    gender TEXT,
                    address TEXT,
                    email TEXT,
                    phone TEXT,
                    major TEXT,
                    enrollment_year INTEGER
                );

                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id TEXT UNIQUE NOT NULL,
                    course_name TEXT NOT NULL,
                    credit_hours INTEGER NOT NULL,
                    department TEXT NOT NULL,
                    lecturer_id INTEGER NOT NULL,
                    semester TEXT NOT NULL,
                    capacity INTEGER NOT NULL DEFAULT 30
                );

                CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    course_id INTEGER NOT NULL,
                    registration_date TEXT NOT NULL,
                    semester TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    UNIQUE(student_id, course_id)
                );

                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    course_id INTEGER NOT NULL,
                    midterm_score REAL NOT NULL DEFAULT 0,
                    final_score REAL NOT NULL DEFAULT 0,
                    total_score REAL NOT NULL DEFAULT 0,
                    result TEXT NOT NULL DEFAULT 'PENDING',
                    UNIQUE(student_id, course_id)
                );
                """
            )
            self.seed_data(conn)

    def seed_data(self, conn: sqlite3.Connection) -> None:
        user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if user_count == 0:
            conn.execute(
                "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                ("admin", "admin123", "admin", "admin@university.edu"),
            )
            conn.execute(
                "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                ("student", "student123", "student", "student@university.edu"),
            )
            conn.execute(
                "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                ("lecturer", "lecturer123", "lecturer", "lecturer@university.edu"),
            )
            conn.commit()

        course_count = conn.execute("SELECT COUNT(*) AS count FROM courses").fetchone()["count"]
        if course_count == 0:
            lecturer_id = conn.execute("SELECT id FROM users WHERE role = 'lecturer' LIMIT 1").fetchone()["id"]
            conn.execute(
                "INSERT INTO courses (course_id, course_name, credit_hours, department, lecturer_id, semester, capacity) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("TR101", "Triết học Mác Lênin", 3, "Giáo dục", lecturer_id, "2025-2026/1", 30),
            )
            conn.execute(
                "INSERT INTO courses (course_id, course_name, credit_hours, department, lecturer_id, semester, capacity) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("PNR101", "Phương pháp nghiên cứu", 3, "Giáo dục", lecturer_id, "2025-2026/1", 30),
            )
            conn.execute(
                "INSERT INTO courses (course_id, course_name, credit_hours, department, lecturer_id, semester, capacity) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("TA101", "Tiếng Anh", 3, "Ngoại ngữ", lecturer_id, "2025-2026/1", 30),
            )
            conn.commit()
