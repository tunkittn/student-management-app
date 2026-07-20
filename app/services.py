from __future__ import annotations

import sqlite3
from typing import Any

from .database import Database
from .models import Course, Enrollment, Grade, Lecturer, Student, User
from .security import hash_password, verify_password


class AppService:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def authenticate(self, username: str, password: str) -> User | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, username, password, role, email FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if row and verify_password(password, row["password"]):
                return User(
                    id=row["id"],
                    username=row["username"],
                    role=row["role"],
                    email=row["email"],
                )
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

    def list_courses_by_lecturer(self, lecturer_id: int) -> list[Course]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, course_id, course_name, credit_hours, department, lecturer_id, semester, capacity "
                "FROM courses WHERE lecturer_id = ? ORDER BY course_name",
                (lecturer_id,),
            ).fetchall()
            return [Course(**dict(row)) for row in rows]

    def get_lecturer_profile(self, user_id: int) -> Lecturer | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, user_id, lecturer_id, full_name, email, phone, department, specialization "
                "FROM lecturers WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return Lecturer(**dict(row)) if row else None

    def list_lecturers(self) -> list[Lecturer]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, user_id, lecturer_id, full_name, email, phone, department, specialization "
                "FROM lecturers ORDER BY full_name"
            ).fetchall()
            return [Lecturer(**dict(row)) for row in rows]

    def get_lecturer_by_id(self, lecturer_id: int) -> Lecturer | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, user_id, lecturer_id, full_name, email, phone, department, specialization "
                "FROM lecturers WHERE id = ?",
                (lecturer_id,),
            ).fetchone()
            return Lecturer(**dict(row)) if row else None

    def add_lecturer(self, lecturer: Lecturer) -> bool:
        if not lecturer.full_name.strip() or not lecturer.lecturer_id.strip() or not lecturer.phone.strip():
            return False
        with self.db.connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (username, password, role, email) VALUES (?, ?, 'lecturer', ?)",
                    (lecturer.lecturer_id.strip(), hash_password(lecturer.phone.strip()), lecturer.email),
                )
                user_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
                conn.execute(
                    """
                    INSERT INTO lecturers (
                        user_id, lecturer_id, full_name, email, phone,
                        department, specialization
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        lecturer.lecturer_id.strip(),
                        lecturer.full_name.strip(),
                        lecturer.email.strip(),
                        lecturer.phone.strip(),
                        lecturer.department.strip(),
                        lecturer.specialization.strip(),
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                conn.rollback()
                return False

    def update_lecturer(self, lecturer: Lecturer) -> bool:
        with self.db.connection() as conn:
            current = conn.execute(
                "SELECT user_id FROM lecturers WHERE id = ?", (lecturer.id,)
            ).fetchone()
            if not current:
                return False
            lecturer.user_id = current["user_id"]
            try:
                conn.execute(
                    "UPDATE users SET username = ?, password = ?, email = ? WHERE id = ?",
                    (lecturer.lecturer_id.strip(), hash_password(lecturer.phone.strip()), lecturer.email, lecturer.user_id),
                )
                conn.execute(
                    """
                    UPDATE lecturers SET lecturer_id = ?, full_name = ?, email = ?,
                        phone = ?, department = ?, specialization = ?
                    WHERE id = ?
                    """,
                    (
                        lecturer.lecturer_id.strip(),
                        lecturer.full_name.strip(),
                        lecturer.email.strip(),
                        lecturer.phone.strip(),
                        lecturer.department.strip(),
                        lecturer.specialization.strip(),
                        lecturer.id,
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                conn.rollback()
                return False

    def delete_lecturer(self, lecturer_id: int) -> bool:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT user_id FROM lecturers WHERE id = ?", (lecturer_id,)
            ).fetchone()
            if not row:
                return False
            assigned = conn.execute(
                "SELECT COUNT(*) FROM courses WHERE lecturer_id = ?", (row["user_id"],)
            ).fetchone()[0]
            if assigned:
                return False
            conn.execute("DELETE FROM lecturers WHERE id = ?", (lecturer_id,))
            conn.execute("DELETE FROM users WHERE id = ?", (row["user_id"],))
            conn.commit()
            return True

    def assign_course_lecturer(self, course_id: int, lecturer_user_id: int) -> bool:
        with self.db.connection() as conn:
            lecturer = conn.execute(
                "SELECT id FROM lecturers WHERE user_id = ?", (lecturer_user_id,)
            ).fetchone()
            course = conn.execute("SELECT id FROM courses WHERE id = ?", (course_id,)).fetchone()
            if not lecturer or not course:
                return False
            conn.execute(
                "UPDATE courses SET lecturer_id = ? WHERE id = ?",
                (lecturer_user_id, course_id),
            )
            conn.commit()
            return True

    def get_admin_stats(self) -> dict[str, int | float]:
        with self.db.connection() as conn:
            return {
                "students": conn.execute("SELECT COUNT(*) FROM students").fetchone()[0],
                "courses": conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
                "enrollments": conn.execute("SELECT COUNT(*) FROM enrollments WHERE status = 'ACTIVE'").fetchone()[0],
                "lecturers": conn.execute("SELECT COUNT(*) FROM users WHERE role = 'lecturer'").fetchone()[0],
            }

    def get_student_stats(self, student_id: int) -> dict[str, int | float]:
        with self.db.connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT e.course_id) AS courses,
                    COUNT(DISTINCT CASE WHEN g.result = 'PASS' THEN g.course_id END) AS passed,
                    COALESCE(AVG(g.total_score), 0) AS average
                FROM enrollments e
                LEFT JOIN grades g
                    ON g.student_id = e.student_id AND g.course_id = e.course_id
                WHERE e.student_id = ? AND e.status = 'ACTIVE'
                """,
                (student_id,),
            ).fetchone()
            return {
                "courses": row["courses"],
                "passed": row["passed"],
                "average": round(row["average"], 2),
            }

    def get_lecturer_stats(self, lecturer_id: int) -> dict[str, int | float]:
        with self.db.connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT c.id) AS courses,
                    COUNT(DISTINCT e.student_id) AS students,
                    COUNT(DISTINCT g.id) AS graded
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'ACTIVE'
                LEFT JOIN grades g ON g.course_id = c.id AND g.student_id = e.student_id
                WHERE c.lecturer_id = ?
                """,
                (lecturer_id,),
            ).fetchone()
            return {
                "courses": row["courses"],
                "students": row["students"],
                "graded": row["graded"],
            }

    def get_course_enrollment_count(self, course_id: int) -> int:
        with self.db.connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM enrollments WHERE course_id = ? AND status = 'ACTIVE'",
                (course_id,),
            ).fetchone()[0]

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
                (student.student_id.strip(), hash_password(student.phone.strip()), "student", student.email),
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
            current = conn.execute(
                "SELECT user_id FROM students WHERE id = ?", (student.id,)
            ).fetchone()
            if not current:
                return False
            if student.user_id is None:
                student.user_id = current["user_id"]
            if student.user_id is not None:
                conn.execute(
                    "UPDATE users SET username=?, password=?, email=? WHERE id = ?",
                    (student.student_id.strip(), hash_password(student.phone.strip()), student.email, student.user_id),
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
                    (student.student_id.strip(), hash_password(student.phone.strip()), "student", student.email),
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
            row = conn.execute(
                "SELECT user_id FROM students WHERE id = ?", (student_id,)
            ).fetchone()
            if not row:
                return False
            conn.execute("DELETE FROM grades WHERE student_id = ?", (student_id,))
            conn.execute("DELETE FROM enrollments WHERE student_id = ?", (student_id,))
            conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
            if row["user_id"] is not None:
                conn.execute("DELETE FROM users WHERE id = ?", (row["user_id"],))
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
