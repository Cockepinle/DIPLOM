from locust import HttpUser, task, between
import json


class BaseUser(HttpUser):
    """Базовый класс для всех пользователей"""
    abstract = True
    wait_time = between(1, 3)
    token = None
    user_email = None
    user_password = "Password123!"

def on_start(self):
    """Авторизация через API с JWT токеном"""
    if not self.user_email:
        return

    response = self.client.post(
        "/api/auth/token/",
        json={
            "email": self.user_email,
            "password": self.user_password
        },
        catch_response=True
    )

    if response.status_code == 200:
        try:
            data = response.json()
            self.token = data.get("access") or data.get("token")
            if self.token:
                self.client.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                response.success()
                return
        except Exception:
            pass

    response.success()

class EmployeeUser(BaseUser):
    """Симуляция поведения сотрудника"""
    user_email = "employee@test.com"

    @task(5)
    def employee_dashboard(self):
        """Главная панель сотрудника"""
        self.client.get("/employee/", name="/employee/")

    @task(4)
    def employee_progress(self):
        """Просмотр прогресса"""
        self.client.get("/employee/progress/", name="/employee/progress/")

    @task(3)
    def employee_courses(self):
        """Просмотр курсов"""
        for course_id in range(1, 4):
            self.client.get(f"/employee/courses/{course_id}/", name="/employee/courses/[id]/")

    @task(2)
    def employee_tasks(self):
        """Просмотр заданий"""
        for task_id in range(1, 4):
            self.client.get(f"/employee/tasks/{task_id}/", name="/employee/tasks/[id]/")

    @task(2)
    def employee_lessons(self):
        """Просмотр уроков"""
        for lesson_id in range(1, 3):
            self.client.get(f"/employee/lessons/{lesson_id}/", name="/employee/lessons/[id]/")

    @task(1)
    def profile(self):
        """Профиль сотрудника"""
        self.client.get("/profile/", name="/profile/")


class ManagerUser(BaseUser):
    """Симуляция поведения менеджера"""
    user_email = "manager@test.com"

    @task(5)
    def manager_dashboard(self):
        """Главная панель менеджера"""
        self.client.get("/manager/", name="/manager/")

    @task(4)
    def manager_course_list(self):
        """Список курсов"""
        self.client.get("/manager/courses/", name="/manager/courses/")

    @task(3)
    def manager_course_detail(self):
        """Детали курсов"""
        for course_id in range(1, 3):
            self.client.get(f"/manager/courses/{course_id}/", name="/manager/courses/[id]/")

    @task(3)
    def manager_task_list(self):
        """Список заданий"""
        self.client.get("/manager/tasks/", name="/manager/tasks/")

    @task(2)
    def manager_task_edit(self):
        """Редактирование заданий"""
        for task_id in range(1, 4):
            self.client.get(f"/manager/tasks/{task_id}/edit/", name="/manager/tasks/[id]/edit/")

    @task(2)
    def manager_task_assign(self):
        """Назначение заданий"""
        for task_id in range(1, 4):
            self.client.get(f"/manager/tasks/{task_id}/assign/", name="/manager/tasks/[id]/assign/")

    @task(2)
    def manager_students(self):
        """Список сотрудников"""
        self.client.get("/manager/students/", name="/manager/students/")

    @task(2)
    def manager_materials(self):
        """Управление материалами"""
        self.client.get("/manager/materials/", name="/manager/materials/")

    @task(1)
    def manager_material_create(self):
        """Страница создания материала"""
        self.client.get("/manager/materials/create/", name="/manager/materials/create/")

    @task(1)
    def manager_tests(self):
        """Список тестов (создание)"""
        self.client.get("/manager/tests/create/", name="/manager/tests/create/")

    @task(1)
    def manager_drafts(self):
        """Черновики"""
        self.client.get("/manager/drafts/", name="/manager/drafts/")

    @task(1)
    def profile(self):
        """Профиль менеджера"""
        self.client.get("/profile/", name="/profile/")


class AnalystUser(BaseUser):
    """Симуляция поведения аналитика"""
    user_email = "analyst@test.com"
    wait_time = between(2, 5)

    @task(5)
    def analyst_dashboard(self):
        """Аналитическая панель"""
        self.client.get("/analytics/", name="/analytics/")

    @task(3)
    def analyst_export_csv(self):
        """Экспорт CSV"""
        self.client.get("/analytics/export/csv/", name="/analytics/export/csv/")

    @task(2)
    def analyst_export_xlsx(self):
        """Экспорт XLSX"""
        self.client.get("/analytics/export/xlsx/", name="/analytics/export/xlsx/")

    @task(2)
    def analyst_export_pdf(self):
        """Экспорт PDF"""
        self.client.get("/analytics/export/pdf/", name="/analytics/export/pdf/")

    @task(1)
    def profile(self):
        """Профиль аналитика"""
        self.client.get("/profile/", name="/profile/")