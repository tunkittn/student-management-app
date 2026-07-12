import flet as ft

from .ui import StudentManagementApp


def main():
    ft.app(target=lambda page: StudentManagementApp(page))
