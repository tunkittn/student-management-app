from __future__ import annotations

from datetime import datetime

import flet as ft

from .models import Course, Lecturer, Student
from .services import AppService


NAVY = "#0F172A"
SLATE = "#475569"
MUTED = "#94A3B8"
SURFACE = "#FFFFFF"
BACKGROUND = "#F4F7FB"
PRIMARY = "#4F46E5"
PRIMARY_LIGHT = "#EEF2FF"
CYAN = "#0891B2"
GREEN = "#16A34A"
AMBER = "#D97706"
RED = "#DC2626"
BORDER = "#E2E8F0"


class StudentManagementApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "EduFlow • Student Management"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.bgcolor = BACKGROUND
        self.page.window.width = 1280
        self.page.window.height = 820
        self.page.window.min_width = 980
        self.page.window.min_height = 680

        self.service = AppService()
        self.current_user = None
        self.current_student: Student | None = None
        self.current_lecturer: Lecturer | None = None
        self.active_section = "overview"
        self.selected_course_id: int | None = None
        self.selected_student_id: int | None = None
        self.selected_lecturer_id: int | None = None

        self.username_field: ft.TextField | None = None
        self.password_field: ft.TextField | None = None
        self.login_status: ft.Text | None = None
        self.grade_course_dropdown: ft.Dropdown | None = None
        self.course_student_list: ft.Column | None = None
        self.grade_status_text: ft.Text | None = None

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
        self.lecturer_name_field: ft.TextField | None = None
        self.lecturer_code_field: ft.TextField | None = None
        self.lecturer_phone_field: ft.TextField | None = None
        self.lecturer_email_field: ft.TextField | None = None
        self.lecturer_department_field: ft.Dropdown | None = None
        self.lecturer_specialization_field: ft.TextField | None = None
        self.lecturer_status_text: ft.Text | None = None

        self.build_login_view()

    # ---------- Shared UI ----------

    def _icon_data(self, name: str):
        """Resolve an icon name to the typed IconData required by modern Flet."""
        icons = getattr(ft, "Icons", None)
        if icons is not None:
            return getattr(icons, name.upper(), icons.CIRCLE_OUTLINED)
        legacy_icons = getattr(ft, "icons")
        return getattr(legacy_icons, name.upper(), legacy_icons.CIRCLE_OUTLINED)

    def _icon(self, name: str, color: str = SLATE, size: int = 22) -> ft.Icon:
        return ft.Icon(self._icon_data(name), color=color, size=size)

    def _card(self, content: ft.Control, padding: int = 20, expand: bool = False) -> ft.Container:
        return ft.Container(
            content=content,
            bgcolor=SURFACE,
            border=ft.Border.all(1, BORDER),
            border_radius=16,
            padding=padding,
            expand=expand,
        )

    def _stat_card(self, title: str, value: str, icon: str, color: str, note: str) -> ft.Container:
        return self._card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                self._icon(icon, color, 24),
                                bgcolor=color + "18",
                                border_radius=12,
                                padding=10,
                            ),
                            ft.Text(value, size=28, weight="bold", color=NAVY),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(title, size=14, weight="bold", color=SLATE),
                    ft.Text(note, size=12, color=MUTED),
                ],
                spacing=8,
            ),
            padding=18,
            expand=True,
        )

    def _section_title(self, title: str, subtitle: str, action: ft.Control | None = None) -> ft.Row:
        controls: list[ft.Control] = [
            ft.Column(
                [
                    ft.Text(title, size=26, weight="bold", color=NAVY),
                    ft.Text(subtitle, size=13, color=SLATE),
                ],
                spacing=2,
                expand=True,
            )
        ]
        if action:
            controls.append(action)
        return ft.Row(controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def _empty_state(self, icon: str, title: str, description: str) -> ft.Container:
        return self._card(
            ft.Column(
                [
                    self._icon(icon, MUTED, 42),
                    ft.Text(title, size=17, weight="bold", color=NAVY),
                    ft.Text(description, size=13, color=SLATE, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=30,
        )

    def _responsive_cards(self, cards: list[ft.Control]) -> ft.ResponsiveRow:
        """Lay cards out responsively without Row.wrap, which is broken on Flet 0.84."""
        for card in cards:
            card.expand = None
            card.col = {"sm": 12, "md": 6, "lg": 4}
        return ft.ResponsiveRow(
            controls=cards,
            columns=12,
            spacing=14,
            run_spacing=14,
        )

    def _notify(self, message: str, success: bool = True) -> None:
        self.page.overlay.append(
            ft.SnackBar(
                content=ft.Text(message, color="#FFFFFF"),
                bgcolor=GREEN if success else RED,
                open=True,
            )
        )
        self.page.update()

    def _nav_item(self, label: str, icon: str, section: str) -> ft.Container:
        active = self.active_section == section
        return ft.Container(
            content=ft.Row(
                [self._icon(icon, "#FFFFFF" if active else "#94A3B8", 20), ft.Text(label, color="#FFFFFF" if active else "#CBD5E1", weight="bold" if active else None)],
                spacing=12,
            ),
            bgcolor="#FFFFFF18" if active else None,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            on_click=lambda _, key=section: self.navigate(key),
        )

    def _shell(self, role_name: str, role_icon: str, navigation: list[tuple[str, str, str]], content: ft.Control) -> None:
        display_name = self.current_user.username if self.current_user else ""
        if self.current_student:
            display_name = self.current_student.full_name
        elif self.current_lecturer:
            display_name = self.current_lecturer.full_name

        sidebar = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(self._icon("school_rounded", "#FFFFFF", 26), bgcolor=PRIMARY, border_radius=12, padding=9),
                            ft.Column([ft.Text("EduFlow", size=20, weight="bold", color="#FFFFFF"), ft.Text("Student Manager", size=11, color="#94A3B8")], spacing=0),
                        ],
                        spacing=10,
                    ),
                    ft.Container(height=18),
                    ft.Text("KHÔNG GIAN LÀM VIỆC", size=10, color="#64748B", weight="bold"),
                    ft.Column([self._nav_item(label, icon, key) for label, icon, key in navigation], spacing=6),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(self._icon(role_icon, PRIMARY, 22), bgcolor="#FFFFFF", border_radius=20, padding=8),
                                ft.Column([ft.Text(display_name, color="#FFFFFF", weight="bold", size=13), ft.Text(role_name, color="#94A3B8", size=11)], spacing=1, expand=True),
                            ],
                            spacing=10,
                        ),
                        border=ft.Border.all(1, "#334155"),
                        border_radius=12,
                        padding=10,
                    ),
                    ft.Container(
                        content=ft.Row([self._icon("logout_rounded", "#FCA5A5", 19), ft.Text("Đăng xuất", color="#FCA5A5", weight="bold")], spacing=10),
                        padding=12,
                        border_radius=10,
                        on_click=lambda _: self.logout(),
                    ),
                ],
                spacing=12,
                expand=True,
            ),
            width=245,
            bgcolor=NAVY,
            padding=20,
        )

        body = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Hệ thống quản lý sinh viên", color=SLATE, size=13),
                            ft.Row([self._icon("notifications_none_rounded", SLATE), ft.Container(width=8), ft.Text(datetime.now().strftime("%d/%m/%Y"), color=SLATE, size=13)], spacing=4),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, color=BORDER),
                    content,
                ],
                spacing=20,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.Padding.symmetric(horizontal=28, vertical=20),
            expand=True,
        )
        self.page.clean()
        self.page.add(ft.Row([sidebar, body], spacing=0, expand=True))
        self.page.update()

    # ---------- Authentication ----------

    def build_login_view(self) -> None:
        self.current_user = None
        self.current_student = None
        self.current_lecturer = None
        self.active_section = "overview"
        self.username_field = ft.TextField(label="Tên đăng nhập", prefix_icon=self._icon_data("person_outline_rounded"), width=360, border_radius=10)
        self.password_field = ft.TextField(label="Mật khẩu", prefix_icon=self._icon_data("lock_outline_rounded"), password=True, can_reveal_password=True, width=360, border_radius=10, on_submit=self.handle_login)
        self.login_status = ft.Text("", color=RED, size=12)

        hero = ft.Container(
            content=ft.Column(
                [
                    ft.Container(self._icon("school_rounded", "#FFFFFF", 34), bgcolor="#FFFFFF22", border_radius=16, padding=14),
                    ft.Text("Quản lý học tập\nnhẹ nhàng hơn.", size=38, weight="bold", color="#FFFFFF"),
                    ft.Text("Một không gian tập trung cho sinh viên, giảng viên và nhà trường.", size=15, color="#C7D2FE", width=420),
                    ft.Container(height=12),
                    ft.Row([self._icon("check_circle_rounded", "#A5F3FC", 19), ft.Text("Dữ liệu tập trung, thao tác nhanh", color="#E0E7FF")]),
                    ft.Row([self._icon("check_circle_rounded", "#A5F3FC", 19), ft.Text("Dashboard riêng cho từng vai trò", color="#E0E7FF")]),
                    ft.Row([self._icon("check_circle_rounded", "#A5F3FC", 19), ft.Text("Theo dõi kết quả học tập trực quan", color="#E0E7FF")]),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
            bgcolor=PRIMARY,
            padding=60,
            expand=True,
        )
        login_card = self._card(
            ft.Column(
                [
                    ft.Text("Chào mừng trở lại", size=27, weight="bold", color=NAVY),
                    ft.Text("Đăng nhập để truy cập dashboard của bạn", color=SLATE, size=13),
                    ft.Container(height=8),
                    self.username_field,
                    self.password_field,
                    self.login_status,
                    ft.ElevatedButton("Đăng nhập", icon=self._icon_data("login_rounded"), width=360, height=48, bgcolor=PRIMARY, color="#FFFFFF", on_click=self.handle_login),
                    ft.Divider(color=BORDER),
                    ft.Text("Tài khoản dùng thử", size=12, weight="bold", color=SLATE),
                    ft.Text("admin / admin123  •  student / student123  •  lecturer / lecturer123", size=11, color=MUTED, width=360),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=34,
        )
        form_area = ft.Container(content=login_card, alignment=ft.Alignment.CENTER, expand=True, padding=40)
        self.page.clean()
        self.page.add(ft.Row([hero, form_area], spacing=0, expand=True))
        self.page.update()

    def handle_login(self, _: ft.ControlEvent) -> None:
        username = (self.username_field.value or "").strip() if self.username_field else ""
        password = self.password_field.value or "" if self.password_field else ""
        if not username or not password:
            if self.login_status:
                self.login_status.value = "Vui lòng nhập tên đăng nhập và mật khẩu."
                self.page.update()
            return
        user = self.service.authenticate(username, password)
        if not user:
            if self.login_status:
                self.login_status.value = "Tên đăng nhập hoặc mật khẩu không chính xác."
                self.page.update()
            return
        self.current_user = user
        self.active_section = "overview"
        if user.role == "admin":
            self.show_admin_view()
        elif user.role == "lecturer":
            self.current_lecturer = self.service.get_lecturer_profile(user.id)
            self.show_lecturer_view()
        else:
            self.current_student = self.service.get_student_profile(user.id)
            self.show_student_view()

    def logout(self) -> None:
        self.selected_course_id = None
        self.selected_student_id = None
        self.selected_lecturer_id = None
        self.build_login_view()

    def navigate(self, section: str) -> None:
        self.active_section = section
        if not self.current_user:
            self.build_login_view()
        elif self.current_user.role == "admin":
            self.show_admin_view()
        elif self.current_user.role == "lecturer":
            self.show_lecturer_view()
        else:
            self.show_student_view()

    # ---------- Admin ----------

    def show_admin_view(self) -> None:
        builders = {
            "overview": self._admin_overview,
            "students": self._admin_students,
            "lecturers": self._admin_lecturers,
            "courses": self._admin_courses,
        }
        content = builders.get(self.active_section, self._admin_overview)()
        self._shell(
            "Quản trị viên",
            "admin_panel_settings_rounded",
            [("Tổng quan", "dashboard_rounded", "overview"), ("Sinh viên", "groups_rounded", "students"), ("Giảng viên", "co_present_rounded", "lecturers"), ("Môn học", "menu_book_rounded", "courses")],
            content,
        )

    def _admin_overview(self) -> ft.Control:
        stats = self.service.get_admin_stats()
        students = self.service.list_students()
        courses = self.service.list_courses()
        recent_students = students[:5]
        student_rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(s.student_id, color=PRIMARY, weight="bold")), ft.DataCell(ft.Text(s.full_name)), ft.DataCell(ft.Text(s.major or "—")), ft.DataCell(ft.Text(str(s.enrollment_year or "—")))])
            for s in recent_students
        ]
        return ft.Column(
            [
                self._section_title("Tổng quan hệ thống", "Theo dõi nhanh hoạt động đào tạo hôm nay"),
                ft.Row(
                    [
                        self._stat_card("Sinh viên", str(stats["students"]), "groups_rounded", PRIMARY, "Hồ sơ đang quản lý"),
                        self._stat_card("Môn học", str(stats["courses"]), "menu_book_rounded", CYAN, "Môn học đang mở"),
                        self._stat_card("Lượt đăng ký", str(stats["enrollments"]), "how_to_reg_rounded", GREEN, "Đăng ký đang hoạt động"),
                        self._stat_card("Giảng viên", str(stats["lecturers"]), "co_present_rounded", AMBER, "Tài khoản giảng viên"),
                    ],
                    spacing=14,
                ),
                ft.Row(
                    [
                        self._card(
                            ft.Column(
                                [
                                    ft.Row([ft.Text("Sinh viên mới", size=17, weight="bold", color=NAVY), ft.TextButton("Xem tất cả", on_click=lambda _: self.navigate("students"))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.DataTable(columns=[ft.DataColumn(ft.Text("MSSV")), ft.DataColumn(ft.Text("Họ tên")), ft.DataColumn(ft.Text("Ngành")), ft.DataColumn(ft.Text("Khóa"))], rows=student_rows),
                                ],
                                spacing=10,
                            ),
                            expand=True,
                        ) if recent_students else self._empty_state("person_add_alt_rounded", "Chưa có sinh viên", "Thêm hồ sơ đầu tiên để bắt đầu."),
                        self._card(
                            ft.Column(
                                [ft.Text("Môn học đang mở", size=17, weight="bold", color=NAVY)]
                                + [self._compact_course(course) for course in courses[:4]],
                                spacing=12,
                            ),
                            padding=18,
                        ),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=18,
        )

    def _compact_course(self, course: Course) -> ft.Control:
        enrolled = self.service.get_course_enrollment_count(course.id)
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(self._icon("book_rounded", PRIMARY, 20), bgcolor=PRIMARY_LIGHT, border_radius=10, padding=9),
                    ft.Column([ft.Text(course.course_name, weight="bold", color=NAVY, size=13), ft.Text(f"{course.course_id} • {course.credit_hours} tín chỉ", size=11, color=SLATE)], spacing=2, expand=True),
                    ft.Text(f"{enrolled}/{course.capacity}", color=PRIMARY, weight="bold", size=12),
                ],
                spacing=10,
            ),
            padding=10,
            bgcolor=BACKGROUND,
            border_radius=10,
        )

    def _admin_students(self) -> ft.Control:
        self._create_admin_fields()
        students = self.service.list_students()
        cards: list[ft.Control] = []
        for student in students:
            selected = student.id == self.selected_student_id
            cards.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(self._icon("person_rounded", PRIMARY, 20), bgcolor=PRIMARY_LIGHT, border_radius=20, padding=9),
                            ft.Column([ft.Text(student.full_name, weight="bold", color=NAVY), ft.Text(f"{student.student_id} • {student.major or 'Chưa cập nhật'}", size=12, color=SLATE)], spacing=2, expand=True),
                            ft.IconButton(icon=self._icon_data("edit_rounded"), icon_color=PRIMARY, tooltip="Chỉnh sửa", on_click=lambda _, sid=student.id: self.edit_student(sid)),
                            ft.IconButton(icon=self._icon_data("delete_outline_rounded"), icon_color=RED, tooltip="Xóa", on_click=lambda _, sid=student.id: self.delete_student(sid)),
                        ],
                        spacing=6,
                    ),
                    bgcolor=PRIMARY_LIGHT if selected else SURFACE,
                    border=ft.Border.all(1, PRIMARY if selected else BORDER),
                    border_radius=12,
                    padding=10,
                )
            )
        student_list: ft.Control = ft.Column(cards, spacing=8) if cards else self._empty_state("group_off_rounded", "Chưa có sinh viên", "Sử dụng biểu mẫu bên cạnh để thêm sinh viên.")
        form = ft.Column(
            [
                ft.Row([ft.Text("Chỉnh sửa hồ sơ" if self.selected_student_id else "Thêm sinh viên", size=18, weight="bold", color=NAVY), ft.TextButton("Làm mới", on_click=lambda _: self.reset_admin_form())], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=ft.Row(
                        [
                            self._icon("info_outline_rounded", PRIMARY, 20),
                            ft.Column(
                                [
                                    ft.Text("Tài khoản sinh viên được tạo tự động", weight="bold", color=NAVY, size=12),
                                    ft.Text("Tên đăng nhập: MSSV  •  Mật khẩu: Số điện thoại", color=SLATE, size=11),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    bgcolor=PRIMARY_LIGHT,
                    border_radius=10,
                    padding=12,
                ),
                ft.Row([self.admin_name_field, self.admin_student_id_field], spacing=12),
                ft.Row([self.admin_dob_field, self.admin_gender_field], spacing=12),
                ft.Row([self.admin_phone_field, self.admin_email_field], spacing=12),
                self.admin_address_field,
                ft.Row([self.admin_major_field, self.admin_year_field], spacing=12),
                self.admin_status_text,
                ft.ElevatedButton("Cập nhật" if self.selected_student_id else "Thêm sinh viên", icon=self._icon_data("save_rounded"), height=45, bgcolor=PRIMARY, color="#FFFFFF", on_click=self.handle_admin_save),
            ],
            spacing=12,
        )
        return ft.Column(
            [
                self._section_title("Quản lý sinh viên", "Thêm mới, cập nhật và quản lý hồ sơ sinh viên"),
                ft.Row(
                    [self._card(ft.Column([ft.Text(f"Danh sách sinh viên ({len(students)})", size=17, weight="bold", color=NAVY), student_list], spacing=14), expand=True), self._card(form, expand=True)],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=18,
        )

    def _create_admin_fields(self) -> None:
        self.admin_name_field = ft.TextField(label="Họ và tên *", expand=True, border_radius=10)
        self.admin_student_id_field = ft.TextField(label="MSSV (5 chữ số) *", expand=True, border_radius=10)
        self.admin_dob_field = ft.TextField(label="Ngày sinh *", hint_text="DD-MM-YYYY", expand=True, border_radius=10)
        self.admin_gender_field = ft.Dropdown(label="Giới tính *", expand=True, border_radius=10, options=[ft.dropdown.DropdownOption(key="Nam", text="Nam"), ft.dropdown.DropdownOption(key="Nữ", text="Nữ")])
        self.admin_address_field = ft.TextField(label="Địa chỉ", border_radius=10)
        self.admin_email_field = ft.TextField(label="Email", expand=True, border_radius=10)
        self.admin_phone_field = ft.TextField(label="Số điện thoại *", expand=True, border_radius=10)
        self.admin_major_field = ft.Dropdown(label="Chuyên ngành *", expand=True, border_radius=10, options=[ft.dropdown.DropdownOption(key="CNTT", text="Công nghệ thông tin"), ft.dropdown.DropdownOption(key="KT", text="Kinh tế"), ft.dropdown.DropdownOption(key="QTKD", text="Quản trị kinh doanh")])
        self.admin_year_field = ft.TextField(label="Năm nhập học", expand=True, border_radius=10)
        self.admin_status_text = ft.Text("", color=RED, size=12)
        if self.selected_student_id:
            student = self.service.get_student_by_id(self.selected_student_id)
            if student:
                self._fill_admin_form(student)

    def _fill_admin_form(self, student: Student) -> None:
        self.admin_name_field.value = student.full_name
        self.admin_student_id_field.value = student.student_id
        self.admin_dob_field.value = student.date_of_birth or ""
        self.admin_gender_field.value = student.gender or ""
        self.admin_address_field.value = student.address or ""
        self.admin_email_field.value = student.email or ""
        self.admin_phone_field.value = student.phone or ""
        self.admin_major_field.value = student.major or ""
        self.admin_year_field.value = str(student.enrollment_year or "")

    def edit_student(self, student_id: int) -> None:
        self.selected_student_id = student_id
        self.active_section = "students"
        self.show_admin_view()

    def delete_student(self, student_id: int) -> None:
        success = self.service.delete_student(student_id)
        if self.selected_student_id == student_id:
            self.selected_student_id = None
        self.show_admin_view()
        self._notify("Đã xóa sinh viên và dữ liệu liên quan." if success else "Không tìm thấy sinh viên.", success)

    def reset_admin_form(self) -> None:
        self.selected_student_id = None
        self.show_admin_view()

    def handle_admin_save(self, _: ft.ControlEvent) -> None:
        fields = [self.admin_name_field, self.admin_student_id_field, self.admin_dob_field, self.admin_gender_field, self.admin_phone_field, self.admin_major_field]
        if any(field is None for field in fields):
            return
        name = (self.admin_name_field.value or "").strip()
        student_code = (self.admin_student_id_field.value or "").strip()
        dob = (self.admin_dob_field.value or "").strip()
        phone = (self.admin_phone_field.value or "").strip()
        gender = self.admin_gender_field.value
        major = self.admin_major_field.value
        if not all([name, student_code, dob, phone, gender, major]):
            self._set_admin_error("Vui lòng điền đầy đủ các trường có dấu *.")
            return
        if not (student_code.isdigit() and len(student_code) == 5):
            self._set_admin_error("MSSV phải gồm đúng 5 chữ số.")
            return
        if not (phone.isdigit() and len(phone) <= 11):
            self._set_admin_error("Số điện thoại phải gồm tối đa 11 chữ số.")
            return
        try:
            datetime.strptime(dob, "%d-%m-%Y")
            year = int(self.admin_year_field.value or "0")
        except ValueError:
            self._set_admin_error("Ngày sinh hoặc năm nhập học chưa đúng định dạng.")
            return
        student = Student(
            id=self.selected_student_id or 0,
            student_id=student_code,
            full_name=name,
            date_of_birth=dob,
            gender=gender,
            address=(self.admin_address_field.value or "").strip(),
            email=(self.admin_email_field.value or "").strip(),
            phone=phone,
            major=major,
            enrollment_year=year,
        )
        editing = self.selected_student_id is not None
        success = self.service.update_student(student) if editing else self.service.add_student(student)
        if not success:
            self._set_admin_error("Không thể lưu. MSSV có thể đã tồn tại.")
            return
        self.selected_student_id = None
        self.show_admin_view()
        action = "Đã cập nhật hồ sơ" if editing else "Đã thêm sinh viên"
        self._notify(f"{action}. Đăng nhập: {student_code} / {phone}")

    def _set_admin_error(self, message: str) -> None:
        if self.admin_status_text:
            self.admin_status_text.value = message
            self.page.update()

    def _admin_lecturers(self) -> ft.Control:
        self._create_lecturer_fields()
        lecturers = self.service.list_lecturers()
        lecturer_cards: list[ft.Control] = []
        for lecturer in lecturers:
            selected = lecturer.id == self.selected_lecturer_id
            course_count = len(self.service.list_courses_by_lecturer(lecturer.user_id or 0))
            lecturer_cards.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(self._icon("co_present_rounded", CYAN, 20), bgcolor="#ECFEFF", border_radius=20, padding=9),
                            ft.Column(
                                [
                                    ft.Text(lecturer.full_name, weight="bold", color=NAVY),
                                    ft.Text(f"{lecturer.lecturer_id} • {lecturer.department or 'Chưa cập nhật'}", size=12, color=SLATE),
                                    ft.Text(f"Đang phụ trách {course_count} môn", size=11, color=MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(icon=self._icon_data("edit_rounded"), icon_color=PRIMARY, tooltip="Chỉnh sửa", on_click=lambda _, lid=lecturer.id: self.edit_lecturer(lid)),
                            ft.IconButton(icon=self._icon_data("delete_outline_rounded"), icon_color=RED, tooltip="Xóa", on_click=lambda _, lid=lecturer.id: self.delete_lecturer(lid)),
                        ],
                        spacing=6,
                    ),
                    bgcolor=PRIMARY_LIGHT if selected else SURFACE,
                    border=ft.Border.all(1, PRIMARY if selected else BORDER),
                    border_radius=12,
                    padding=10,
                )
            )

        lecturer_list: ft.Control = ft.Column(lecturer_cards, spacing=8) if lecturer_cards else self._empty_state("person_add_alt_rounded", "Chưa có giảng viên", "Sử dụng biểu mẫu bên cạnh để tạo tài khoản giảng viên.")
        form = ft.Column(
            [
                ft.Row([ft.Text("Chỉnh sửa giảng viên" if self.selected_lecturer_id else "Thêm giảng viên", size=18, weight="bold", color=NAVY), ft.TextButton("Làm mới", on_click=lambda _: self.reset_lecturer_form())], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=ft.Row(
                        [
                            self._icon("info_outline_rounded", CYAN, 20),
                            ft.Column([ft.Text("Tài khoản được tạo tự động", weight="bold", color=NAVY, size=12), ft.Text("Tên đăng nhập: Mã GV  •  Mật khẩu: Số điện thoại", color=SLATE, size=11)], spacing=2, expand=True),
                        ],
                        spacing=10,
                    ),
                    bgcolor="#ECFEFF",
                    border_radius=10,
                    padding=12,
                ),
                ft.Row([self.lecturer_name_field, self.lecturer_code_field], spacing=12),
                ft.Row([self.lecturer_phone_field, self.lecturer_email_field], spacing=12),
                self.lecturer_department_field,
                self.lecturer_specialization_field,
                self.lecturer_status_text,
                ft.ElevatedButton("Cập nhật" if self.selected_lecturer_id else "Thêm giảng viên", icon=self._icon_data("save_rounded"), height=45, bgcolor=PRIMARY, color="#FFFFFF", on_click=self.handle_lecturer_save),
            ],
            spacing=12,
        )

        assignment_rows = [self._course_assignment_row(course, lecturers) for course in self.service.list_courses()]
        assignments: ft.Control = self._card(
            ft.Column(
                [
                    ft.Text("Phân công giảng dạy", size=18, weight="bold", color=NAVY),
                    ft.Text("Chọn giảng viên phụ trách cho từng môn học. Thay đổi được lưu ngay.", size=12, color=SLATE),
                ]
                + (assignment_rows or [ft.Text("Chưa có môn học để phân công.", color=MUTED)]),
                spacing=10,
            )
        )
        return ft.Column(
            [
                self._section_title("Quản lý giảng viên", "Tạo tài khoản, cập nhật hồ sơ và phân công giảng dạy"),
                ft.Row(
                    [self._card(ft.Column([ft.Text(f"Danh sách giảng viên ({len(lecturers)})", size=17, weight="bold", color=NAVY), lecturer_list], spacing=14), expand=True), self._card(form, expand=True)],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                assignments,
            ],
            spacing=18,
        )

    def _create_lecturer_fields(self) -> None:
        self.lecturer_name_field = ft.TextField(label="Họ và tên *", expand=True, border_radius=10)
        self.lecturer_code_field = ft.TextField(label="Mã giảng viên *", expand=True, border_radius=10)
        self.lecturer_phone_field = ft.TextField(label="Số điện thoại *", expand=True, border_radius=10)
        self.lecturer_email_field = ft.TextField(label="Email", expand=True, border_radius=10)
        self.lecturer_department_field = ft.Dropdown(
            label="Khoa/Bộ môn *",
            border_radius=10,
            options=[
                ft.dropdown.DropdownOption(key="CNTT", text="Công nghệ thông tin"),
                ft.dropdown.DropdownOption(key="Giáo dục", text="Giáo dục"),
                ft.dropdown.DropdownOption(key="Ngoại ngữ", text="Ngoại ngữ"),
                ft.dropdown.DropdownOption(key="Kinh tế", text="Kinh tế"),
                ft.dropdown.DropdownOption(key="QTKD", text="Quản trị kinh doanh"),
            ],
        )
        self.lecturer_specialization_field = ft.TextField(label="Chuyên môn", border_radius=10)
        self.lecturer_status_text = ft.Text("", color=RED, size=12)
        if self.selected_lecturer_id:
            lecturer = self.service.get_lecturer_by_id(self.selected_lecturer_id)
            if lecturer:
                self._fill_lecturer_form(lecturer)

    def _fill_lecturer_form(self, lecturer: Lecturer) -> None:
        self.lecturer_name_field.value = lecturer.full_name
        self.lecturer_code_field.value = lecturer.lecturer_id
        self.lecturer_phone_field.value = lecturer.phone
        self.lecturer_email_field.value = lecturer.email or ""
        self.lecturer_department_field.value = lecturer.department or ""
        self.lecturer_specialization_field.value = lecturer.specialization or ""

    def edit_lecturer(self, lecturer_id: int) -> None:
        self.selected_lecturer_id = lecturer_id
        self.active_section = "lecturers"
        self.show_admin_view()

    def reset_lecturer_form(self) -> None:
        self.selected_lecturer_id = None
        self.show_admin_view()

    def delete_lecturer(self, lecturer_id: int) -> None:
        success = self.service.delete_lecturer(lecturer_id)
        if success and self.selected_lecturer_id == lecturer_id:
            self.selected_lecturer_id = None
        self.show_admin_view()
        self._notify("Đã xóa giảng viên và tài khoản liên quan." if success else "Không thể xóa giảng viên đang được phân công môn học.", success)

    def handle_lecturer_save(self, _: ft.ControlEvent) -> None:
        if not all([self.lecturer_name_field, self.lecturer_code_field, self.lecturer_phone_field, self.lecturer_email_field, self.lecturer_department_field, self.lecturer_specialization_field, self.lecturer_status_text]):
            return
        name = (self.lecturer_name_field.value or "").strip()
        code = (self.lecturer_code_field.value or "").strip().upper()
        phone = (self.lecturer_phone_field.value or "").strip()
        department = self.lecturer_department_field.value or ""
        if not all([name, code, phone, department]):
            self._set_lecturer_error("Vui lòng điền đầy đủ các trường có dấu *.")
            return
        if not (code.isalnum() and 3 <= len(code) <= 12):
            self._set_lecturer_error("Mã giảng viên phải gồm 3-12 chữ hoặc số, không chứa khoảng trắng.")
            return
        if not (phone.isdigit() and 1 <= len(phone) <= 11):
            self._set_lecturer_error("Số điện thoại phải gồm tối đa 11 chữ số.")
            return
        lecturer = Lecturer(
            id=self.selected_lecturer_id or 0,
            lecturer_id=code,
            full_name=name,
            email=(self.lecturer_email_field.value or "").strip(),
            phone=phone,
            department=department,
            specialization=(self.lecturer_specialization_field.value or "").strip(),
        )
        editing = self.selected_lecturer_id is not None
        success = self.service.update_lecturer(lecturer) if editing else self.service.add_lecturer(lecturer)
        if not success:
            self._set_lecturer_error("Không thể lưu. Mã giảng viên có thể đã tồn tại.")
            return
        self.selected_lecturer_id = None
        self.show_admin_view()
        action = "Đã cập nhật giảng viên" if editing else "Đã thêm giảng viên"
        self._notify(f"{action}. Đăng nhập: {code} / {phone}")

    def _set_lecturer_error(self, message: str) -> None:
        if self.lecturer_status_text:
            self.lecturer_status_text.value = message
            self.page.update()

    def _course_assignment_row(self, course: Course, lecturers: list[Lecturer]) -> ft.Container:
        options = [ft.dropdown.DropdownOption(key=str(item.user_id), text=f"{item.lecturer_id} • {item.full_name}") for item in lecturers if item.user_id is not None]
        valid_user_ids = {item.user_id for item in lecturers}
        dropdown = ft.Dropdown(
            label="Giảng viên phụ trách",
            width=330,
            border_radius=9,
            value=str(course.lecturer_id) if course.lecturer_id in valid_user_ids else None,
            options=options,
        )
        handler = lambda _, cid=course.id, control=dropdown: self.assign_course_lecturer(cid, control)
        if hasattr(dropdown, "on_select"):
            dropdown.on_select = handler
        else:
            dropdown.on_change = handler
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(self._icon("menu_book_rounded", PRIMARY, 19), bgcolor=PRIMARY_LIGHT, border_radius=9, padding=8),
                    ft.Column([ft.Text(course.course_name, weight="bold", color=NAVY), ft.Text(f"{course.course_id} • {course.department}", size=11, color=SLATE)], spacing=2, expand=True),
                    dropdown,
                ],
                spacing=12,
            ),
            border=ft.Border.all(1, BORDER),
            border_radius=11,
            padding=10,
        )

    def assign_course_lecturer(self, course_id: int, dropdown: ft.Dropdown) -> None:
        try:
            lecturer_user_id = int(dropdown.value) if dropdown.value else 0
        except ValueError:
            lecturer_user_id = 0
        success = self.service.assign_course_lecturer(course_id, lecturer_user_id)
        self._notify("Đã cập nhật phân công giảng dạy." if success else "Không thể cập nhật phân công.", success)

    def _admin_courses(self) -> ft.Control:
        courses = self.service.list_courses()
        tiles = []
        for course in courses:
            lecturer = self.service.get_lecturer_profile(course.lecturer_id)
            tiles.append(self._card(
                ft.Column(
                    [
                        ft.Row([ft.Container(self._icon("menu_book_rounded", PRIMARY), bgcolor=PRIMARY_LIGHT, padding=10, border_radius=12), ft.Column([ft.Text(course.course_name, size=16, weight="bold", color=NAVY), ft.Text(course.course_id, color=PRIMARY, weight="bold", size=12)], spacing=2, expand=True)], spacing=12),
                        ft.Divider(color=BORDER),
                        ft.Row([ft.Text(f"{course.credit_hours} tín chỉ", color=SLATE), ft.Text(course.department, color=SLATE)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"Học kỳ {course.semester}", size=12, color=MUTED),
                        ft.Text(f"Giảng viên: {lecturer.full_name if lecturer else 'Chưa phân công'}", size=12, color=SLATE),
                        ft.ProgressBar(value=min(self.service.get_course_enrollment_count(course.id) / max(course.capacity, 1), 1), color=PRIMARY, bgcolor=PRIMARY_LIGHT),
                        ft.Text(f"{self.service.get_course_enrollment_count(course.id)}/{course.capacity} sinh viên", size=12, color=SLATE),
                    ],
                    spacing=10,
                ),
                expand=True,
            ))
        return ft.Column([self._section_title("Danh sách môn học", "Theo dõi sĩ số và thông tin các môn đang mở"), self._responsive_cards(tiles) if tiles else self._empty_state("book_rounded", "Chưa có môn học", "Dữ liệu môn học chưa được khởi tạo.")], spacing=18)

    # ---------- Student ----------

    def show_student_view(self) -> None:
        self.current_student = self.service.get_student_profile(self.current_user.id) if self.current_user else None
        builders = {"overview": self._student_overview, "courses": self._student_courses, "results": self._student_results, "profile": self._student_profile}
        content = builders.get(self.active_section, self._student_overview)()
        self._shell("Sinh viên", "person_rounded", [("Tổng quan", "dashboard_rounded", "overview"), ("Đăng ký môn", "library_add_rounded", "courses"), ("Kết quả học tập", "insights_rounded", "results"), ("Hồ sơ cá nhân", "badge_rounded", "profile")], content)

    def _student_missing(self) -> ft.Control:
        return self._empty_state("person_search_rounded", "Tài khoản chưa có hồ sơ", "Vui lòng liên hệ quản trị viên để liên kết hồ sơ sinh viên.")

    def _student_overview(self) -> ft.Control:
        if not self.current_student:
            return ft.Column([self._section_title("Dashboard sinh viên", "Tổng quan học tập của bạn"), self._student_missing()], spacing=18)
        stats = self.service.get_student_stats(self.current_student.id)
        enrollments = self.service.list_enrollments(self.current_student.id)
        available = self._available_courses()
        return ft.Column(
            [
                self._section_title(f"Xin chào, {self.current_student.full_name}", "Chúc bạn một ngày học tập hiệu quả!"),
                ft.Row([self._stat_card("Môn đang học", str(stats["courses"]), "auto_stories_rounded", PRIMARY, "Trong học kỳ hiện tại"), self._stat_card("Môn đã đạt", str(stats["passed"]), "verified_rounded", GREEN, "Kết quả PASS"), self._stat_card("Điểm trung bình", f"{stats['average']:.2f}", "workspace_premium_rounded", AMBER, "Thang điểm 10")], spacing=14),
                ft.Row(
                    [
                        self._card(ft.Column([ft.Row([ft.Text("Tiến độ học tập", size=17, weight="bold", color=NAVY), ft.TextButton("Xem điểm", on_click=lambda _: self.navigate("results"))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)] + self._enrollment_summary(enrollments), spacing=12), expand=True),
                        self._card(ft.Column([ft.Text("Gợi ý cho bạn", size=17, weight="bold", color=NAVY), ft.Text(f"Còn {len(available)} môn học bạn có thể đăng ký.", color=SLATE, size=13), ft.ElevatedButton("Đăng ký môn học", icon=self._icon_data("arrow_forward_rounded"), bgcolor=PRIMARY, color="#FFFFFF", on_click=lambda _: self.navigate("courses"))], spacing=14), padding=22),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=18,
        )

    def _enrollment_summary(self, enrollments) -> list[ft.Control]:
        if not enrollments:
            return [ft.Text("Bạn chưa đăng ký môn học nào.", color=MUTED)]
        controls: list[ft.Control] = []
        for enrollment in enrollments[:5]:
            course = self.service.get_course_by_id(enrollment.course_id)
            if course:
                grade = self.service.get_grade_by_student_and_course(self.current_student.id, course.id)
                controls.append(ft.Row([ft.Container(self._icon("book_rounded", PRIMARY, 18), bgcolor=PRIMARY_LIGHT, border_radius=8, padding=7), ft.Column([ft.Text(course.course_name, weight="bold", color=NAVY, size=13), ft.Text(course.course_id, color=MUTED, size=11)], spacing=1, expand=True), ft.Text(f"{grade.total_score:.1f}" if grade else "Đang học", color=GREEN if grade and grade.result == "PASS" else SLATE, weight="bold", size=12)], spacing=10))
        return controls

    def _available_courses(self) -> list[Course]:
        if not self.current_student:
            return []
        enrolled = {item.course_id for item in self.service.list_enrollments(self.current_student.id)}
        return [course for course in self.service.list_courses() if course.id not in enrolled]

    def _student_courses(self) -> ft.Control:
        if not self.current_student:
            return ft.Column([self._section_title("Đăng ký môn học", "Lựa chọn môn học phù hợp"), self._student_missing()], spacing=18)
        available = self._available_courses()
        enrollments = self.service.list_enrollments(self.current_student.id)
        registered = [self.service.get_course_by_id(item.course_id) for item in enrollments]
        available_cards = [self._course_registration_card(course) for course in available]
        registered_cards = [self._compact_course(course) for course in registered if course]
        return ft.Column(
            [
                self._section_title("Đăng ký môn học", "Khám phá và đăng ký các môn đang mở"),
                self._card(ft.Column([ft.Text(f"Môn đang học ({len(registered_cards)})", size=17, weight="bold", color=NAVY)] + (registered_cards or [ft.Text("Chưa có môn đã đăng ký.", color=MUTED)]), spacing=10)),
                ft.Text(f"Có thể đăng ký ({len(available_cards)})", size=17, weight="bold", color=NAVY),
                self._responsive_cards(available_cards) if available_cards else self._empty_state("task_alt_rounded", "Bạn đã đăng ký tất cả môn", "Không còn môn học khả dụng trong học kỳ này."),
            ],
            spacing=16,
        )

    def _course_registration_card(self, course: Course) -> ft.Container:
        enrolled = self.service.get_course_enrollment_count(course.id)
        return self._card(ft.Column([ft.Row([ft.Container(self._icon("library_books_rounded", PRIMARY), bgcolor=PRIMARY_LIGHT, border_radius=10, padding=9), ft.Text(course.course_id, color=PRIMARY, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Text(course.course_name, size=16, weight="bold", color=NAVY), ft.Text(f"{course.credit_hours} tín chỉ • {course.department}", size=12, color=SLATE), ft.Text(f"Còn {max(course.capacity - enrolled, 0)} chỗ", size=12, color=GREEN if enrolled < course.capacity else RED), ft.ElevatedButton("Đăng ký ngay", icon=self._icon_data("add_rounded"), bgcolor=PRIMARY, color="#FFFFFF", disabled=enrolled >= course.capacity, on_click=lambda _, cid=course.id: self.register_course(cid))], spacing=11), padding=18)

    def register_course(self, course_id: int) -> None:
        if not self.current_student:
            return
        success = self.service.register_course(self.current_student.id, course_id)
        self.show_student_view()
        self._notify("Đăng ký môn học thành công." if success else "Không thể đăng ký môn học này.", success)

    def _student_results(self) -> ft.Control:
        if not self.current_student:
            return ft.Column([self._section_title("Kết quả học tập", "Theo dõi điểm số của bạn"), self._student_missing()], spacing=18)
        rows = []
        for enrollment in self.service.list_enrollments(self.current_student.id):
            course = self.service.get_course_by_id(enrollment.course_id)
            grade = self.service.get_grade_by_student_and_course(self.current_student.id, enrollment.course_id)
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(course.course_id if course else "—", color=PRIMARY, weight="bold")), ft.DataCell(ft.Text(course.course_name if course else "—")), ft.DataCell(ft.Text(f"{grade.midterm_score:.1f}" if grade else "—")), ft.DataCell(ft.Text(f"{grade.final_score:.1f}" if grade else "—")), ft.DataCell(ft.Text(f"{grade.total_score:.2f}" if grade else "—", weight="bold")), ft.DataCell(ft.Text(grade.result if grade else "ĐANG HỌC", color=GREEN if grade and grade.result == "PASS" else RED if grade else SLATE, weight="bold"))]))
        table = ft.DataTable(columns=[ft.DataColumn(ft.Text("Mã môn")), ft.DataColumn(ft.Text("Môn học")), ft.DataColumn(ft.Text("Giữa kỳ")), ft.DataColumn(ft.Text("Cuối kỳ")), ft.DataColumn(ft.Text("Tổng")), ft.DataColumn(ft.Text("Kết quả"))], rows=rows)
        return ft.Column([self._section_title("Kết quả học tập", "Điểm tổng kết = 40% giữa kỳ + 60% cuối kỳ"), self._card(table) if rows else self._empty_state("query_stats_rounded", "Chưa có kết quả", "Kết quả sẽ xuất hiện sau khi giảng viên nhập điểm.")], spacing=18)

    def _student_profile(self) -> ft.Control:
        if not self.current_student:
            return ft.Column([self._section_title("Hồ sơ cá nhân", "Thông tin sinh viên"), self._student_missing()], spacing=18)
        s = self.current_student
        details = [("Mã sinh viên", s.student_id), ("Họ và tên", s.full_name), ("Ngày sinh", s.date_of_birth or "—"), ("Giới tính", s.gender or "—"), ("Chuyên ngành", s.major or "—"), ("Năm nhập học", str(s.enrollment_year or "—")), ("Email", s.email or "—"), ("Số điện thoại", s.phone or "—"), ("Địa chỉ", s.address or "—")]
        rows = [ft.Container(ft.Row([ft.Text(label, width=160, color=SLATE), ft.Text(value, weight="bold", color=NAVY, expand=True)]), padding=ft.Padding.symmetric(vertical=10), border=ft.Border(bottom=ft.BorderSide(1, BORDER))) for label, value in details]
        return ft.Column([self._section_title("Hồ sơ cá nhân", "Thông tin được quản lý bởi phòng đào tạo"), self._card(ft.Column([ft.Row([ft.Container(self._icon("person_rounded", "#FFFFFF", 38), bgcolor=PRIMARY, border_radius=35, padding=15), ft.Column([ft.Text(s.full_name, size=22, weight="bold", color=NAVY), ft.Text(f"{s.student_id} • {s.major}", color=SLATE)], spacing=3)], spacing=16), ft.Divider(color=BORDER)] + rows, spacing=4))], spacing=18)

    # ---------- Lecturer ----------

    def _lecturer_courses(self) -> list[Course]:
        return self.service.list_courses_by_lecturer(self.current_user.id) if self.current_user else []

    def show_lecturer_view(self) -> None:
        self.current_lecturer = self.service.get_lecturer_profile(self.current_user.id) if self.current_user else None
        builders = {"overview": self._lecturer_overview, "grading": self._lecturer_grading}
        content = builders.get(self.active_section, self._lecturer_overview)()
        self._shell("Giảng viên", "co_present_rounded", [("Tổng quan", "dashboard_rounded", "overview"), ("Quản lý điểm", "grading_rounded", "grading")], content)

    def _lecturer_overview(self) -> ft.Control:
        stats = self.service.get_lecturer_stats(self.current_user.id)
        courses = self._lecturer_courses()
        course_cards = [self._lecturer_course_card(course) for course in courses]
        return ft.Column([self._section_title("Dashboard giảng viên", "Theo dõi lớp học và tiến độ nhập điểm"), ft.Row([self._stat_card("Môn phụ trách", str(stats["courses"]), "menu_book_rounded", PRIMARY, "Trong học kỳ này"), self._stat_card("Sinh viên", str(stats["students"]), "groups_rounded", CYAN, "Tổng sinh viên các lớp"), self._stat_card("Đã nhập điểm", str(stats["graded"]), "task_alt_rounded", GREEN, "Bài điểm đã hoàn tất")], spacing=14), ft.Text("Lớp học của tôi", size=18, weight="bold", color=NAVY), self._responsive_cards(course_cards) if course_cards else self._empty_state("event_busy_rounded", "Chưa được phân công môn", "Liên hệ quản trị viên để cập nhật phân công giảng dạy.")], spacing=18)

    def _lecturer_course_card(self, course: Course) -> ft.Container:
        students = self.service.list_course_students(course.id)
        graded = sum(1 for student in students if self.service.get_grade_by_student_and_course(student.id, course.id))
        progress = graded / len(students) if students else 0
        return self._card(ft.Column([ft.Row([ft.Container(self._icon("class_rounded", PRIMARY), bgcolor=PRIMARY_LIGHT, border_radius=11, padding=10), ft.Text(course.course_id, color=PRIMARY, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Text(course.course_name, size=16, weight="bold", color=NAVY), ft.Text(f"{len(students)} sinh viên • {course.semester}", color=SLATE, size=12), ft.ProgressBar(value=progress, color=GREEN, bgcolor="#DCFCE7"), ft.Text(f"Đã nhập điểm {graded}/{len(students)}", color=MUTED, size=11), ft.OutlinedButton("Mở sổ điểm", icon=self._icon_data("arrow_forward_rounded"), on_click=lambda _, cid=course.id: self.open_grading(cid))], spacing=11), padding=18)

    def open_grading(self, course_id: int) -> None:
        self.selected_course_id = course_id
        self.active_section = "grading"
        self.show_lecturer_view()

    def _lecturer_grading(self) -> ft.Control:
        courses = self._lecturer_courses()
        valid_ids = {course.id for course in courses}
        if self.selected_course_id not in valid_ids:
            self.selected_course_id = None
        self.grade_course_dropdown = ft.Dropdown(label="Chọn môn học", width=430, border_radius=10, value=str(self.selected_course_id) if self.selected_course_id else None, options=[ft.dropdown.DropdownOption(key=str(course.id), text=f"{course.course_id} • {course.course_name}") for course in courses])
        if hasattr(self.grade_course_dropdown, "on_select"):
            self.grade_course_dropdown.on_select = self.select_grading_course
        else:
            self.grade_course_dropdown.on_change = self.select_grading_course
        self.grade_status_text = ft.Text("", color=GREEN, size=12)
        if not courses:
            content: ft.Control = self._empty_state("event_busy_rounded", "Chưa có môn phụ trách", "Không có dữ liệu để nhập điểm.")
        elif not self.selected_course_id:
            content = self._empty_state("touch_app_rounded", "Chọn một môn học", "Danh sách sinh viên sẽ hiển thị tại đây để bạn nhập điểm.")
        else:
            students = self.service.list_course_students(self.selected_course_id)
            rows = [self._grade_student_row(student) for student in students]
            content = self._card(ft.Column(rows, spacing=10)) if rows else self._empty_state("group_off_rounded", "Lớp chưa có sinh viên", "Sinh viên cần đăng ký môn trước khi nhập điểm.")
        return ft.Column([self._section_title("Quản lý điểm", "Nhập điểm giữa kỳ, cuối kỳ và lưu kết quả"), self._card(ft.Row([self.grade_course_dropdown, ft.Container(expand=True), ft.Text("Công thức: 40% giữa kỳ + 60% cuối kỳ", color=SLATE, size=12)])), content, self.grade_status_text], spacing=16)

    def select_grading_course(self, _: ft.ControlEvent) -> None:
        try:
            self.selected_course_id = int(self.grade_course_dropdown.value) if self.grade_course_dropdown and self.grade_course_dropdown.value else None
        except ValueError:
            self.selected_course_id = None
        self.show_lecturer_view()

    def _grade_student_row(self, student: Student) -> ft.Container:
        grade = self.service.get_grade_by_student_and_course(student.id, self.selected_course_id)
        midterm = ft.TextField(label="Giữa kỳ", width=115, value=str(grade.midterm_score) if grade else "", border_radius=9)
        final = ft.TextField(label="Cuối kỳ", width=115, value=str(grade.final_score) if grade else "", border_radius=9)
        return ft.Container(content=ft.Row([ft.Container(self._icon("person_rounded", PRIMARY, 18), bgcolor=PRIMARY_LIGHT, border_radius=18, padding=8), ft.Column([ft.Text(student.full_name, weight="bold", color=NAVY), ft.Text(student.student_id, size=11, color=MUTED)], spacing=1, expand=True), midterm, final, ft.Container(ft.Text(f"{grade.total_score:.2f}" if grade else "—", color=GREEN if grade and grade.result == "PASS" else SLATE, weight="bold"), width=55, alignment=ft.Alignment.CENTER), ft.ElevatedButton("Lưu", icon=self._icon_data("save_rounded"), bgcolor=PRIMARY, color="#FFFFFF", on_click=lambda _, sid=student.id, mid=midterm, fin=final: self.handle_grade_save(sid, mid, fin))], spacing=10), border=ft.Border.all(1, BORDER), border_radius=12, padding=10)

    def handle_grade_save(self, student_id: int, midterm_field: ft.TextField, final_field: ft.TextField) -> None:
        if self.selected_course_id is None or not self.grade_status_text:
            return
        try:
            midterm = float(midterm_field.value)
            final = float(final_field.value)
        except (TypeError, ValueError):
            self.grade_status_text.value = "Điểm phải là số hợp lệ."
            self.grade_status_text.color = RED
            self.page.update()
            return
        if not (0 <= midterm <= 10 and 0 <= final <= 10):
            self.grade_status_text.value = "Điểm phải nằm trong khoảng từ 0 đến 10."
            self.grade_status_text.color = RED
            self.page.update()
            return
        self.service.update_grade(student_id, self.selected_course_id, midterm, final)
        self.show_lecturer_view()
        self._notify("Đã lưu điểm thành công.")


def main(page: ft.Page):
    StudentManagementApp(page)
