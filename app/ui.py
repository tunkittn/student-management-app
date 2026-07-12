from __future__ import annotations

from datetime import datetime

import flet as ft

from .models import Student
from .services import AppService


class StudentManagementApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Student Management System"
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window.width = 1200
        self.page.window.height = 800
        self.service = AppService()
        self.current_user = None
        self.current_student = None
        self.username_field: ft.TextField | None = None
        self.password_field: ft.TextField | None = None
        self.midterm_field: ft.TextField | None = None
        self.final_field: ft.TextField | None = None
        self.grade_status_text: ft.Text | None = None
        self.selected_course_id: int | None = None
        self.grade_course_dropdown: ft.Dropdown | None = None
        self.course_student_list: ft.Column | None = None
        self.course_student_status: ft.Text | None = None
        self.admin_name_field: ft.TextField | None = None
        self.admin_student_id_field: ft.TextField | None = None
        self.admin_dob_field: ft.TextField | None = None
        self.admin_gender_field: ft.Dropdown | None = None
        self.admin_address_field: ft.TextField | None = None
        self.admin_email_field: ft.TextField | None = None
        self.admin_phone_field: ft.TextField | None = None
        self.admin_major_field: ft.Dropdown | None = None
        self.admin_year_field: ft.TextField | None = None
        self.admin_status_text: ft.Text | None = None
        self.selected_student_id: int | None = None
        self.grade_student_dropdown: ft.Dropdown | None = None
        self.grade_course_dropdown: ft.Dropdown | None = None
        self.container = ft.Container(expand=True)
        self.build_login_view()

    def build_login_view(self) -> None:
        self.page.clean()
        self.username_field = ft.TextField(label="Tên đăng nhập", autofocus=True, width=320)
        self.password_field = ft.TextField(label="Mật khẩu", password=True, width=320)
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Student Management System", size=28, weight="bold"),
                        ft.Text("Đăng nhập để tiếp tục", size=16, color="#546e7a"),
                        self.username_field,
                        self.password_field,
                        ft.ElevatedButton("Đăng nhập", width=320, on_click=self.handle_login),
                        ft.Text("Mặc định: admin/admin123", size=12, color="#757575"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        )

    def handle_login(self, e: ft.ControlEvent) -> None:
        username = self.username_field.value if self.username_field else ""
        password = self.password_field.value if self.password_field else ""
        user = self.service.authenticate(username, password)
        if user:
            self.current_user = user
            if user.role == "admin":
                self.show_admin_view()
            elif user.role == "lecturer":
                self.show_lecturer_view()
            else:
                self.show_student_view()
        else:
            self.page.overlay.append(ft.SnackBar(content=ft.Text("Thông tin đăng nhập không đúng"), open=True))
            self.page.update()

    def show_student_view(self) -> None:
        self.page.clean()
        profile = self.service.get_student_profile(self.current_user.id)
        self.current_student = profile
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Xin chào, " + (profile.full_name if profile else self.current_user.username), size=24, weight="bold"),
                                ft.ElevatedButton("Đăng xuất", on_click=lambda _: self.build_login_view()),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text("Quản lý sinh viên và học tập", size=16, color="#546e7a"),
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text("Thông tin cá nhân", weight="bold"),
                                        ft.Text("MSSV: " + (profile.student_id if profile else "")),
                                        ft.Text("Chuyên ngành: " + (profile.major if profile else "")),
                                        ft.Text("Email: " + (profile.email if profile else "")),
                                    ],
                                    spacing=6,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("Danh sách khóa học", weight="bold"),
                                        self.build_course_list(),
                                    ],
                                    expand=True,
                                ),
                            ],
                            spacing=20,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Text("Kết quả học tập", weight="bold"),
                        self.build_grade_view(),
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=20,
                expand=True,
            )
        )
        self.page.update()

    def build_course_list(self) -> ft.Control:
        if not self.current_student:
            return ft.Text("")
        enrolled_ids = {enrollment.course_id for enrollment in self.service.list_enrollments(self.current_student.id)}
        available_courses = [course for course in self.service.list_courses() if course.id not in enrolled_ids]
        if not available_courses:
            return ft.Text("Bạn đã đăng ký tất cả môn học hiện có.")
        items = []
        for course in available_courses:
            items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(course.course_name),
                            ft.ElevatedButton("Đăng ký", on_click=lambda e, cid=course.id: self.register_course(cid)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    border=ft.Border.all(1, "#e0e0e0"),
                    padding=10,
                    width=400,
                )
            )
        return ft.Column(items, spacing=8)

    def register_course(self, course_id: int) -> None:
        if not self.current_student:
            return
        ok = self.service.register_course(self.current_student.id, course_id)
        self.page.overlay.append(ft.SnackBar(content=ft.Text("Đăng ký thành công" if ok else "Đăng ký thất bại"), open=True))
        if ok:
            self.show_student_view()
        else:
            self.page.update()

    def build_grade_view(self) -> ft.Control:
        if not self.current_student:
            return ft.Text("")
        enrollments = self.service.list_enrollments(self.current_student.id)
        if not enrollments:
            return ft.Text("Chưa có môn học nào được đăng ký.")
        rows = []
        for enrollment in enrollments:
            course = self.service.get_course_by_id(enrollment.course_id)
            course_label = course.course_name if course else str(enrollment.course_id)
            grade = self.service.get_grade_by_student_and_course(self.current_student.id, enrollment.course_id)
            status = f"{grade.total_score:.2f} ({grade.result})" if grade else "In progress"
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(course_label)),
                        ft.DataCell(ft.Text(status)),
                    ]
                )
            )
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Môn học")),
                ft.DataColumn(ft.Text("Trạng thái")),
            ],
            rows=rows,
        )

    def show_admin_view(self) -> None:
        self.page.clean()
        self.selected_student_id = None
        self.admin_name_field = ft.TextField(label="Họ tên", width=300)
        self.admin_student_id_field = ft.TextField(label="MSSV", width=300)
        self.admin_dob_field = ft.TextField(label="Ngày sinh", hint_text="DD-MM-YYYY", width=300)
        self.admin_gender_field = ft.Dropdown(
            label="Giới tính",
            width=300,
            options=[
                ft.dropdown.DropdownOption(key="Nam", text="Nam"),
                ft.dropdown.DropdownOption(key="Nữ", text="Nữ"),
            ],
        )
        self.admin_address_field = ft.TextField(label="Địa chỉ", width=300)
        self.admin_email_field = ft.TextField(label="Email", width=300)
        self.admin_phone_field = ft.TextField(label="Số điện thoại", width=300)
        self.admin_major_field = ft.Dropdown(
            label="Chuyên ngành",
            width=300,
            options=[
                ft.dropdown.DropdownOption(key="CNTT", text="Công nghệ thông tin"),
                ft.dropdown.DropdownOption(key="KT", text="Kinh tế"),
                ft.dropdown.DropdownOption(key="QTKD", text="Quản trị kinh doanh"),
            ],
        )
        self.admin_year_field = ft.TextField(label="Năm nhập học", width=300)
        self.admin_status_text = ft.Text("")

        students = self.service.list_students()
        student_cards = []
        for student in students:
            student_cards.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column(
                            [
                                ft.Text(student.full_name, weight="bold"),
                                ft.Text("MSSV: " + student.student_id),
                                ft.Text("Chuyên ngành: " + student.major),
                                ft.Row(
                                    [
                                        ft.TextButton("Sửa", on_click=lambda e, sid=student.id: self.edit_student(sid)),
                                        ft.TextButton("Xóa", on_click=lambda e, sid=student.id: self.delete_student(sid)),
                                    ]
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=12,
                    )
                )
            )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Bảng điều khiển Admin", size=24, weight="bold"),
                                ft.ElevatedButton("Đăng xuất", on_click=lambda _: self.build_login_view()),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text("Quản lý sinh viên"),
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("Danh sách sinh viên", weight="bold"),
                                            ft.Column(student_cards, spacing=8, scroll=ft.ScrollMode.AUTO),
                                        ],
                                        width=420,
                                        spacing=8,
                                    ),
                                    border=ft.Border.all(1, "#e0e0e0"),
                                    padding=12,
                                ),
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("Thông tin sinh viên", weight="bold"),
                                            self.admin_name_field,
                                            self.admin_student_id_field,
                                            self.admin_dob_field,
                                            self.admin_gender_field,
                                            self.admin_address_field,
                                            self.admin_email_field,
                                            self.admin_phone_field,
                                            self.admin_major_field,
                                            self.admin_year_field,
                                            ft.Row(
                                                [
                                                    ft.ElevatedButton("Lưu", on_click=self.handle_admin_save),
                                                    ft.OutlinedButton("Làm mới", on_click=lambda _: self.reset_admin_form()),
                                                ]
                                            ),
                                            self.admin_status_text,
                                        ],
                                        width=500,
                                        spacing=8,
                                    ),
                                    border=ft.Border.all(1, "#e0e0e0"),
                                    padding=12,
                                ),
                            ],
                            spacing=20,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=20,
                expand=True,
            )
        )
        self.page.update()

    def reset_admin_form(self) -> None:
        if not self.admin_name_field or not self.admin_student_id_field or not self.admin_dob_field or not self.admin_gender_field or not self.admin_address_field or not self.admin_email_field or not self.admin_phone_field or not self.admin_major_field or not self.admin_year_field or not self.admin_status_text:
            return
        self.selected_student_id = None
        self.admin_name_field.value = ""
        self.admin_student_id_field.value = ""
        self.admin_dob_field.value = ""
        if self.admin_gender_field:
            self.admin_gender_field.value = ""
        self.admin_address_field.value = ""
        self.admin_email_field.value = ""
        self.admin_phone_field.value = ""
        self.admin_major_field.value = ""
        self.admin_year_field.value = ""
        self.admin_status_text.value = ""
        self.page.update()

    def edit_student(self, student_id: int) -> None:
        student = self.service.get_student_by_id(student_id)
        if not student:
            return
        self.selected_student_id = student.id
        if not self.admin_name_field or not self.admin_student_id_field or not self.admin_dob_field or not self.admin_gender_field or not self.admin_address_field or not self.admin_email_field or not self.admin_phone_field or not self.admin_major_field or not self.admin_year_field:
            return
        self.admin_name_field.value = student.full_name
        self.admin_student_id_field.value = student.student_id
        self.admin_dob_field.value = student.date_of_birth or ""
        if self.admin_gender_field:
            self.admin_gender_field.value = student.gender or ""
        self.admin_address_field.value = student.address or ""
        self.admin_email_field.value = student.email or ""
        self.admin_phone_field.value = student.phone or ""
        if self.admin_major_field:
            self.admin_major_field.value = student.major or ""
        self.admin_year_field.value = str(student.enrollment_year or "")
        self.page.update()

    def delete_student(self, student_id: int) -> None:
        self.service.delete_student(student_id)
        self.show_admin_view()

    def handle_admin_save(self, e: ft.ControlEvent) -> None:
        if not self.admin_name_field or not self.admin_student_id_field or not self.admin_dob_field or not self.admin_gender_field or not self.admin_address_field or not self.admin_email_field or not self.admin_phone_field or not self.admin_major_field or not self.admin_year_field or not self.admin_status_text:
            return
        student_id_text = self.admin_student_id_field.value.strip()
        phone_text = self.admin_phone_field.value.strip()
        if not self.admin_name_field.value.strip() or not student_id_text or not self.admin_dob_field.value.strip() or not self.admin_gender_field.value or not self.admin_major_field.value or not phone_text:
            self.admin_status_text.value = "Họ tên, MSSV, SĐT, ngày sinh, giới tính và chuyên ngành là bắt buộc"
            self.page.update()
            return

        if not (student_id_text.isdigit() and len(student_id_text) == 5):
            self.admin_status_text.value = "MSSV phải đúng 5 chữ số"
            self.page.update()
            return

        if not (phone_text.isdigit() and 1 <= len(phone_text) <= 11):
            self.admin_status_text.value = "SĐT phải là số, dài từ 1 đến 11 chữ số"
            self.page.update()
            return

        date_text = self.admin_dob_field.value.strip()
        try:
            datetime.strptime(date_text, "%d-%m-%Y")
        except ValueError:
            self.admin_status_text.value = "Ngày sinh phải đúng định dạng DD-MM-YYYY"
            self.page.update()
            return

        gender_value = self.admin_gender_field.value
        if gender_value not in ("Nam", "Nữ"):
            self.admin_status_text.value = "Giới tính phải là Nam hoặc Nữ"
            self.page.update()
            return

        try:
            year = int(self.admin_year_field.value or "0")
        except ValueError:
            self.admin_status_text.value = "Năm nhập học phải là số"
            self.page.update()
            return

        student = Student(
            id=self.selected_student_id or 0,
            user_id=None,
            student_id=self.admin_student_id_field.value.strip(),
            full_name=self.admin_name_field.value.strip(),
            date_of_birth=date_text,
            gender=gender_value,
            address=self.admin_address_field.value.strip(),
            email=self.admin_email_field.value.strip(),
            phone=self.admin_phone_field.value.strip(),
            major=self.admin_major_field.value,
            enrollment_year=year,
        )
        if self.selected_student_id:
            student.id = self.selected_student_id
            self.service.update_student(student)
            self.admin_status_text.value = "Đã cập nhật sinh viên"
        else:
            self.service.add_student(student)
            self.admin_status_text.value = "Đã thêm sinh viên"
        self.show_admin_view()

    def show_lecturer_view(self) -> None:
        self.page.clean()
        self.grade_course_dropdown = ft.Dropdown(
            label="Chọn môn học",
            width=400,
            options=self.build_course_options(),
        )
        self.course_student_status = ft.Text("Chọn môn để hiển thị sinh viên")
        self.course_student_list = ft.Column([], spacing=8)
        self.grade_status_text = ft.Text("")
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Bảng điều khiển Giảng viên", size=24, weight="bold"),
                                ft.ElevatedButton("Đăng xuất", on_click=lambda _: self.build_login_view()),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text("Chọn môn và nhập điểm"),
                        self.grade_course_dropdown,
                        ft.Row(
                            [
                                ft.ElevatedButton("Hiển thị sinh viên", on_click=self.load_course_students),
                                self.course_student_status,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.course_student_list,
                        self.grade_status_text,
                    ],
                    expand=True,
                ),
                padding=20,
                expand=True,
            )
        )
        self.page.update()

    def build_course_options(self) -> list[ft.dropdown.DropdownOption]:
        return [
            ft.dropdown.DropdownOption(key=str(course.id), text=f"{course.course_id} - {course.course_name}")
            for course in self.service.list_courses()
        ]

    def load_course_students(self, e: ft.ControlEvent) -> None:
        if not self.grade_course_dropdown or not self.course_student_list or not self.course_student_status:
            return
        if not self.grade_course_dropdown.value:
            self.course_student_status.value = "Vui lòng chọn môn học"
            self.page.update()
            return
        try:
            self.selected_course_id = int(self.grade_course_dropdown.value)
        except ValueError:
            self.course_student_status.value = "Môn học không hợp lệ"
            self.page.update()
            return
        self.course_student_list.controls = [self.build_course_student_row(student) for student in self.service.list_course_students(self.selected_course_id)]
        if self.course_student_list.controls:
            self.course_student_status.value = f"{len(self.course_student_list.controls)} sinh viên trong môn"
        else:
            self.course_student_status.value = "Chưa có sinh viên đăng ký môn này"
        self.page.update()

    def build_course_student_row(self, student: Student) -> ft.Control:
        course_id = self.selected_course_id or 0
        grade = self.service.get_grade_by_student_and_course(student.id, course_id)
        midterm_value = str(grade.midterm_score) if grade else ""
        final_value = str(grade.final_score) if grade else ""
        midterm_field = ft.TextField(label="Giữa kỳ", width=120, value=midterm_value)
        final_field = ft.TextField(label="Cuối kỳ", width=120, value=final_value)
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(student.student_id, width=100),
                    ft.Text(student.full_name, expand=True),
                    midterm_field,
                    final_field,
                    ft.ElevatedButton(
                        "Lưu",
                        on_click=lambda e, sid=student.id, mid=midterm_field, fin=final_field: self.handle_grade_save(sid, mid, fin),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10,
            ),
            border=ft.Border.all(1, "#e0e0e0"),
            padding=10,
        )

    def handle_grade_save(self, student_id: int, midterm_field: ft.TextField, final_field: ft.TextField) -> None:
        if self.selected_course_id is None or not self.grade_status_text:
            return
        if not midterm_field.value or not final_field.value:
            self.grade_status_text.value = "Vui lòng nhập đủ điểm giữa kỳ và cuối kỳ"
            self.page.update()
            return
        try:
            midterm = float(midterm_field.value)
            final = float(final_field.value)
        except ValueError:
            self.grade_status_text.value = "Điểm phải là số"
            self.page.update()
            return
        if not (0 <= midterm <= 10 and 0 <= final <= 10):
            self.grade_status_text.value = "Điểm phải từ 0 đến 10"
            self.page.update()
            return
        self.service.update_grade(student_id, self.selected_course_id, midterm, final)
        self.grade_status_text.value = f"Đã lưu điểm cho {student_id}"
        self.page.update()


def main(page: ft.Page):
    StudentManagementApp(page)
