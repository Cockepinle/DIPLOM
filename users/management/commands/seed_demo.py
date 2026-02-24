from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from users.models import Competency, UserCompetency, CompetencyAssessment, Specialty, Position
from courses.models import (
    Course,
    CourseMaterial,
    Enrollment,
    Task,
    TaskAssignment,
    TaskSubmission,
)
from tests.models import Test, Question, Answer
from results.models import TestResult
from feedback.models import Feedback, TaskReview
from analytics.models import AuditLog, TrainingEvent, Dashboard, Report, ReportExport, BackupRecord


class Command(BaseCommand):
    help = "Create demo data for the admin panel"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Add demo data even if it already exists",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get("force", False)
        User = get_user_model()

        if User.objects.filter(email="admin@example.com").exists() and not force:
            self.stdout.write(self.style.WARNING(
                "Demo data already exists. Use --force to add more."
            ))
            return

        def get_or_create_user(email, password, role, **extra):
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "role": role,
                    **extra,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            return user

        admin = get_or_create_user(
            "admin@example.com",
            "Admin12345!",
            "ADMIN",
            is_staff=True,
            is_superuser=True,
            first_name="Admin",
            last_name="User",
        )
        manager = get_or_create_user(
            "manager@example.com",
            "Password123!",
            "MANAGER",
            first_name="Мария",
            last_name="Смирнова",
        )
        analyst = get_or_create_user(
            "analyst@example.com",
            "Password123!",
            "ANALYST",
            first_name="Илья",
            last_name="Кузнецов",
        )
        employees = [
            get_or_create_user(
                f"employee{i}@example.com",
                "Password123!",
                "EMPLOYEE",
                first_name=name,
                last_name=last,
            )
            for i, (name, last) in enumerate(
                [
                    ("Анна", "Петрова"),
                    ("Егор", "Николаев"),
                    ("Ольга", "Иванова"),
                ],
                start=1,
            )
        ]

        specialties = []
        for name in ["Продавец", "Кассир", "Кухня", "Маркетинг"]:
            spec, _ = Specialty.objects.get_or_create(name=name)
            specialties.append(spec)

        positions = []
        for name in ["Программист", "Менеджер", "Аналитик", "Кассир"]:
            pos, _ = Position.objects.get_or_create(name=name)
            positions.append(pos)

        competencies = []
        for name in ["Коммуникация", "Аналитика", "Продажи", "Python", "Безопасность"]:
            comp, _ = Competency.objects.get_or_create(name=name)
            competencies.append(comp)

        courses = []
        for idx, (title, desc) in enumerate([
            ("Введение в продукт", "Базовый курс по продукту"),
            ("Стандарты сервиса", "Правила общения и качество"),
            ("Безопасность данных", "Основы защиты информации"),
        ]):
            course, _ = Course.objects.get_or_create(
                title=title,
                defaults={
                    "description": desc,
                    "created_by": manager,
                    "specialty": specialties[idx % len(specialties)],
                },
            )
            courses.append(course)

        for idx, emp in enumerate(employees):
            emp.specialty = specialties[idx % len(specialties)]
            emp.position = positions[idx % len(positions)]
            emp.save()

        manager.position = positions[1 % len(positions)]
        manager.save()
        analyst.position = positions[2 % len(positions)]
        analyst.save()

        for course in courses:
            CourseMaterial.objects.get_or_create(
                course=course,
                title=f"Материалы: {course.title}",
                defaults={"material_type": "TEXT", "content": "Описание и инструкции"},
            )

        for emp in employees:
            for course in courses:
                Enrollment.objects.get_or_create(
                    user=emp,
                    course=course,
                    defaults={
                        "assigned_by": manager,
                        "status": "ASSIGNED",
                        "progress": 0,
                        "completed": False,
                    },
                )
        for course in courses:
            test, _ = Test.objects.get_or_create(
                course=course,
                title=f"Тест: {course.title}",
                defaults={"passing_score": 70, "created_by": manager},
            )
            if not test.questions.exists():
                for q_idx in range(1, 4):
                    q = Question.objects.create(
                        test=test,
                        text=f"Вопрос {q_idx} по курсу {course.title}",
                    )
                    for a_idx in range(1, 5):
                        Answer.objects.create(
                            question=q,
                            text=f"Вариант {a_idx}",
                            is_correct=(a_idx == 1),
                        )

        for course in courses:
            task, _ = Task.objects.get_or_create(
                course=course,
                title=f"Задание: {course.title}",
                defaults={
                    "description": "Выполнить практическое задание",
                    "criteria": "Полнота и точность",
                    "task_type": "PRACTICAL",
                    "created_by": manager,
                },
            )
            for emp in employees:
                assignment, _ = TaskAssignment.objects.get_or_create(
                    task=task,
                    user=emp,
                    defaults={
                        "assigned_by": manager,
                        "status": "ASSIGNED",
                        "priority": 3,
                    },
                )
                submission, _ = TaskSubmission.objects.get_or_create(
                    assignment=assignment,
                    defaults={
                        "content": "Ответ на задание",
                        "status": "SUBMITTED",
                    },
                )
                TaskReview.objects.get_or_create(
                    manager=manager,
                    task_submission=submission,
                    defaults={"comment": "Хорошая работа", "rating": 5},
                )

        for emp in employees:
            for comp in competencies[:3]:
                UserCompetency.objects.get_or_create(
                    user=emp,
                    competency=comp,
                    defaults={"level": 6, "source": "MANAGER"},
                )

        for emp in employees:
            test = Test.objects.filter(course=courses[0]).first()
            if not test:
                continue
            test_result, _ = TestResult.objects.get_or_create(
                user=emp,
                test=test,
                defaults={"score": 85, "passed": True},
            )
            Feedback.objects.get_or_create(
                manager=manager,
                test_result=test_result,
                defaults={"comment": "Отличный результат", "rating": 5},
            )
            comp = competencies[0]
            CompetencyAssessment.objects.get_or_create(
                user=emp,
                competency=comp,
                assessor=manager,
                defaults={
                    "level": 7,
                    "comment": "Хороший уровень",
                    "test_result": test_result,
                },
            )

        for emp in employees:
            TrainingEvent.objects.get_or_create(
                user=emp,
                event_type="COURSE_STARTED",
                course=courses[0],
                defaults={"created_at": timezone.now()},
            )

        Dashboard.objects.get_or_create(
            owner=analyst,
            title="Дашборд аналитики",
            defaults={"config": {"widgets": ["progress", "scores"]}},
        )

        report, _ = Report.objects.get_or_create(
            owner=analyst,
            title="Отчет по прогрессу",
            defaults={"report_type": "PROGRESS", "filters": {"period": "month"}},
        )

        ReportExport.objects.get_or_create(
            report=report,
            export_format="PDF",
            defaults={"status": "READY", "file_path": "reports/progress.pdf"},
        )

        BackupRecord.objects.get_or_create(
            created_by=admin,
            defaults={"status": "CREATED", "file_path": "backups/db.sqlite3"},
        )

        AuditLog.objects.get_or_create(
            actor=admin,
            action="seed_demo",
            defaults={"object_type": "system", "message": "Demo data created"},
        )

        self.stdout.write(self.style.SUCCESS("Demo data created."))
