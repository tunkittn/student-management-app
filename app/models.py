from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    role: str
    email: str


@dataclass
class Student:
    id: int
    user_id: int | None = None
    student_id: str = ""
    full_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    address: str = ""
    email: str = ""
    phone: str = ""
    major: str = ""
    enrollment_year: int = 0


@dataclass
class Lecturer:
    id: int
    user_id: int | None = None
    lecturer_id: str = ""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    department: str = ""
    specialization: str = ""


@dataclass
class Course:
    id: int
    course_id: str
    course_name: str
    credit_hours: int
    department: str
    lecturer_id: int
    semester: str
    capacity: int


@dataclass
class Enrollment:
    id: int
    student_id: int
    course_id: int
    registration_date: str
    semester: str
    status: str


@dataclass
class Grade:
    id: int
    student_id: int
    course_id: int
    midterm_score: float
    final_score: float
    total_score: float
    result: str
