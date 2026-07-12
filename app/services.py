from __future__ import annotations

from typing import Any

from .database import Database
from .models import Course, Enrollment, Grade, Student, User


class AppService:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def authenticate(self, username: str, password: str) -> User | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, username, password, role, email FROM users WHERE username = ? AND password = ?",
                (username, password),
            ).fetchone()
            if row:
                return User(**dict(row))
            return None

    def get_student_profile(self, user_id: int) -> Student | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, user_id, student_id, full_name, date_of_birth, gender, address, email, phone, major, enrollment_year FROM students WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return Student(**dict(row)) if row else None

    def list_course_students(self, course_id: int) -> list[Student]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT s.id, s.user_id, s.student_id, s.full_name, s.date_of_birth, s.gender, s.address, s.email, s.phone, s.major, s.enrollment_year "
                "FROM students s "
                "JOIN enrollments e ON s.id = e.student_id "
                "WHERE e.course_id = ? ORDER BY s.full_name",
                (course_id,),
            ).fetchall()
            return [Student(**dict(row)) for row in rows]

    def get_grade_by_student_and_course(self, student_id: int, course_id: int) -> Grade | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, student_id, course_id, midterm_score, final_score, total_score, result FROM grades WHERE student_id = ? AND course_id = ?",
                (student_id, course_id),
            ).fetchone()
            return Grade(**dict(row)) if row else None

    def list_courses(self) -> list[Course]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, course_id, course_name, credit_hours, department, lecturer_id, semester, capacity FROM courses ORDER BY course_name"
            ).fetchall()
            return [Course(**dict(row)) for row in rows]

    def get_course_by_id(self, course_id: int) -> Course | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, course_id, course_name, credit_hours, department, lecturer_id, semester, capacity FROM courses WHERE id = ?",
                (course_id,),
            ).fetchone()
            return Course(**dict(row)) if row else None

    def list_enrollments(self, student_id: int) -> list[Enrollment]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, student_id, course_id, registration_date, semester, status FROM enrollments WHERE student_id = ? ORDER BY id DESC",
                (student_id,),
            ).fetchall()
            return [Enrollment(**dict(row)) for row in rows]

    def list_grades(self, student_id: int) -> list[Grade]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, student_id, course_id, midterm_score, final_score, total_score, result FROM grades WHERE student_id = ? ORDER BY id DESC",
                (student_id,),
            ).fetchall()
            return [Grade(**dict(row)) for row in rows]

    def register_course(self, student_id: int, course_id: int) -> bool:
        with self.db.connection() as conn:
            course = conn.execute(
                "SELECT id, capacity FROM courses WHERE id = ?",
                (course_id,),
            ).fetchone()
            if not course:
                return False
            existing = conn.execute(
                "SELECT id FROM enrollments WHERE student_id = ? AND course_id = ?",
                (student_id, course_id),
            ).fetchone()
            if existing:
                return False
            current_count = conn.execute(
                "SELECT COUNT(*) AS count FROM enrollments WHERE course_id = ?",
                (course_id,),
            ).fetchone()["count"]
            if current_count >= course["capacity"]:
                return False
            conn.execute(
                "INSERT INTO enrollments (student_id, course_id, registration_date, semester, status) VALUES (?, ?, date('now'), ?, 'ACTIVE')",
                (student_id, course_id, "2025-2026/1"),
            )
            conn.commit()
            return True

    def list_students(self) -> list[Student]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, user_id, student_id, full_name, date_of_birth, gender, address, email, phone, major, enrollment_year FROM students ORDER BY full_name"
            ).fetchall()
            return [Student(**dict(row)) for row in rows]

    def get_student_by_id(self, student_id: int) -> Student | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, user_id, student_id, full_name, date_of_birth, gender, address, email, phone, major, enrollment_year FROM students WHERE id = ?",
                (student_id,),
            ).fetchone()
            return Student(**dict(row)) if row else None

    def add_student(self, student: Student) -> bool:
        if not student.full_name.strip() or not student.student_id.strip() or not student.phone.strip():
            return False
        with self.db.connection() as conn:
            existing_user = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (student.student_id.strip(),),
            ).fetchone()
            if existing_user:
                return False
            conn.execute(
                "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                (student.student_id.strip(), student.phone.strip(), "student", student.email),
            )
            user_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            conn.execute(
                "INSERT INTO students (user_id, student_id, full_name, date_of_birth, gender, address, email, phone, major, enrollment_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    student.student_id,
                    student.full_name,
                    student.date_of_birth,
                    student.gender,
                    student.address,
                    student.email,
                    student.phone,
                    student.major,
                    student.enrollment_year,
                ),
            )
            conn.commit()
            return True

    def update_student(self, student: Student) -> bool:
        with self.db.connection() as conn:
            if student.user_id is not None:
                conn.execute(
                    "UPDATE users SET username=?, password=?, email=? WHERE id = ?",
                    (student.student_id.strip(), student.phone.strip(), student.email, student.user_id),
                )
            else:
                existing_user = conn.execute(
                    "SELECT id FROM users WHERE username = ?",
                    (student.student_id.strip(),),
                ).fetchone()
                if existing_user:
                    return False
                conn.execute(
                    "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                    (student.student_id.strip(), student.phone.strip(), "student", student.email),
                )
                student.user_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            conn.execute(
                "UPDATE students SET student_id=?, full_name=?, date_of_birth=?, gender=?, address=?, email=?, phone=?, major=?, enrollment_year=?, user_id=? WHERE id=?",
                (
                    student.student_id,
                    student.full_name,
                    student.date_of_birth,
                    student.gender,
                    student.address,
                    student.email,
                    student.phone,
                    student.major,
                    student.enrollment_year,
                    student.user_id,
                    student.id,
                ),
            )
            conn.commit()
            return True

    def delete_student(self, student_id: int) -> bool:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            return True

    def update_grade(self, student_id: int, course_id: int, midterm: float, final: float) -> bool:
        with self.db.connection() as conn:
            existing = conn.execute(
                "SELECT id FROM grades WHERE student_id = ? AND course_id = ?",
                (student_id, course_id),
            ).fetchone()
            total = midterm * 0.4 + final * 0.6
            result = "PASS" if total >= 5 else "FAIL"
            if existing:
                conn.execute(
                    "UPDATE grades SET midterm_score=?, final_score=?, total_score=?, result=? WHERE id=?",
                    (midterm, final, total, result, existing["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO grades (student_id, course_id, midterm_score, final_score, total_score, result) VALUES (?, ?, ?, ?, ?, ?)",
                    (student_id, course_id, midterm, final, total, result),
                )
            conn.commit()
            return True
