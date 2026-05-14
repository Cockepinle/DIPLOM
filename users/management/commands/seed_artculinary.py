from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from analytics.models import AuditLog, BackupRecord, Dashboard, Report, ReportExport, TrainingEvent
from courses.models import (
    Course,
    CourseMaterial,
    Enrollment,
    Lesson,
    Task,
    TaskAssignment,
    TaskSubmission,
)
from feedback.models import Feedback, TaskReview
from results.models import TestResult
from tests.models import Answer, Question, Test
from users.models import Competency, CompetencyAssessment, Position, Specialty, UserCompetency


class Command(BaseCommand):
    help = "Seed demo data for АРТ КУЛИНАРИЯ (готовая продукция): сотрудники, обучение, оценки, аналитика."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete ALL data (flush) before seeding.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Required confirmation flag for --reset.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Seed even if demo users already exist.",
        )

    def handle(self, *args, **options):
        reset = bool(options.get("reset"))
        yes = bool(options.get("yes"))
        force = bool(options.get("force"))

        if reset and not yes:
            self.stdout.write(
                self.style.WARNING(
                    "Флаг --reset удалит ВСЕ данные из БД. Запусти команду с --reset --yes, если уверен."
                )
            )
            return

        if reset:
            self.stdout.write(self.style.WARNING("Flush БД..."))
            call_command("flush", interactive=False)
            call_command("migrate", interactive=False)

        User = get_user_model()
        if User.objects.filter(email="admin@artkulinary.local").exists() and not force and not reset:
            self.stdout.write(
                self.style.WARNING(
                    "Демо-данные уже существуют (admin@artkulinary.local). Используй --force или --reset."
                )
            )
            return

        self._seed()
        self.stdout.write(self.style.SUCCESS("АРТ КУЛИНАРИЯ demo data created."))

    @transaction.atomic
    def _seed(self):
        User = get_user_model()
        now = timezone.now()
        today = timezone.localdate()
        user_password_hash = make_password("Password123!")
        admin_password_hash = make_password("Admin12345!")

        def mk_user(email, password_hash, role, **extra):
            defaults = {
                "role": role,
                "is_active": True,
                "registration_status": User.RegistrationStatus.APPROVED,
                "registration_requested_at": now,
                "registration_reviewed_at": now,
                "password": password_hash,
                **extra,
            }
            user, created = User.objects.get_or_create(email=email, defaults=defaults)
            return user

        admin = mk_user(
            "admin@artkulinary.local",
            admin_password_hash,
            "ADMIN",
            is_staff=True,
            is_superuser=True,
            first_name="Админ",
            last_name="АртКулинария",
            department="Администрация",
        )
        manager_quality = mk_user(
            "manager.quality@artkulinary.local",
            user_password_hash,
            "MANAGER",
            first_name="Екатерина",
            last_name="Соколова",
            department="Контроль качества",
        )
        manager_prod = mk_user(
            "manager.production@artkulinary.local",
            user_password_hash,
            "MANAGER",
            first_name="Андрей",
            last_name="Воробьёв",
            department="Производство",
        )
        analyst = mk_user(
            "analyst@artkulinary.local",
            user_password_hash,
            "ANALYST",
            first_name="Олег",
            last_name="Мельников",
            department="Аналитика",
        )

        specialties = {}
        for name in [
            "Производство готовой продукции",
            "Контроль качества (ОТК)",
            "Разработка рецептур (R&D)",
            "Логистика и склад",
            "Продажи и маркетинг",
        ]:
            specialties[name], _ = Specialty.objects.get_or_create(name=name, defaults={"is_active": True})

        positions = {}
        for name in [
            "Технолог",
            "Оператор линии",
            "Контролёр качества",
            "Лаборант",
            "Логист",
            "Кладовщик",
            "Менеджер по продажам",
            "Специалист по упаковке",
        ]:
            positions[name], _ = Position.objects.get_or_create(name=name, defaults={"is_active": True})

        competencies = {}
        for name, category, description in [
            ("Пищевая безопасность", "Качество", "Знание санитарии, рисков и критических точек."),
            ("HACCP/ССР", "Качество", "Понимание принципов HACCP и контрольных процедур."),
            ("Технологические карты", "Технологии", "Умение оформлять и вести техкарты, нормы, выход."),
            ("Маркировка и состав", "Регламенты", "Знание требований к маркировке и составу."),
            ("Оборудование линии", "Производство", "Безопасная работа и настройка оборудования."),
            ("Контроль качества", "Качество", "Отбор проб, чек-листы, несоответствия."),
            ("Командная работа", "Soft skills", "Взаимодействие, коммуникация, ответственность."),
        ]:
            comp, _ = Competency.objects.get_or_create(
                name=name,
                defaults={"category": category, "description": description, "is_active": True},
            )
            competencies[name] = comp

        employees_data = [
            ("ivanova@artkulinary.local", "Ирина", "Иванова", "Производство", "Производство готовой продукции", "Оператор линии"),
            ("petrov@artkulinary.local", "Павел", "Петров", "Производство", "Производство готовой продукции", "Специалист по упаковке"),
            ("smirnova@artkulinary.local", "Мария", "Смирнова", "Контроль качества", "Контроль качества (ОТК)", "Контролёр качества"),
            ("kuznetsov@artkulinary.local", "Дмитрий", "Кузнецов", "Контроль качества", "Контроль качества (ОТК)", "Лаборант"),
            ("egorov@artkulinary.local", "Алексей", "Егоров", "R&D", "Разработка рецептур (R&D)", "Технолог"),
            ("fedorova@artkulinary.local", "Наталья", "Фёдорова", "Логистика", "Логистика и склад", "Логист"),
            ("sidorov@artkulinary.local", "Сергей", "Сидоров", "Логистика", "Логистика и склад", "Кладовщик"),
            ("orlov@artkulinary.local", "Илья", "Орлов", "Продажи", "Продажи и маркетинг", "Менеджер по продажам"),
        ]
        employees = []
        for email, first, last, dept, spec_name, pos_name in employees_data:
            user = mk_user(
                email,
                user_password_hash,
                "EMPLOYEE",
                first_name=first,
                last_name=last,
                department=dept,
                specialty=specialties[spec_name],
                position=positions[pos_name],
            )
            employees.append(user)

        # Add a few pending registration requests (for demo of approval workflow)
        pending_people = [
            ("candidate1@artkulinary.local", "Виктор", "Кравцов", "Производство", "Производство готовой продукции", "Оператор линии"),
            ("candidate2@artkulinary.local", "Алина", "Громова", "Контроль качества", "Контроль качества (ОТК)", "Контролёр качества"),
        ]
        for email, first, last, dept, spec_name, pos_name in pending_people:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "role": "EMPLOYEE",
                    "is_active": False,
                    "registration_status": User.RegistrationStatus.PENDING,
                    "registration_requested_at": now - timedelta(hours=2),
                    "password": user_password_hash,
                    "first_name": first,
                    "last_name": last,
                    "department": dept,
                    "specialty": specialties[spec_name],
                    "position": positions[pos_name],
                },
            )

        courses_data = [
            (
                "Санитария и гигиена на производстве",
                "Обязательные требования: личная гигиена, уборка, контроль чистоты.",
                specialties["Производство готовой продукции"],
                manager_quality,
            ),
            (
                "HACCP: критические контрольные точки",
                "Принципы HACCP/ССР, риски и действия при отклонениях.",
                specialties["Контроль качества (ОТК)"],
                manager_quality,
            ),
            (
                "Технологические карты: структура и расчёт выхода",
                "Как оформлять техкарту, нормы сырья, потери и выход готового продукта.",
                specialties["Разработка рецептур (R&D)"],
                manager_prod,
            ),
            (
                "Маркировка и состав: требования к этикетке",
                "Состав, пищевая ценность, аллергены, сроки годности, условия хранения.",
                specialties["Контроль качества (ОТК)"],
                manager_quality,
            ),
            (
                "Холодовая цепь и склад",
                "Температурные режимы, FIFO/FEFO, контроль сроков и остатков.",
                specialties["Логистика и склад"],
                manager_prod,
            ),
            (
                "Продуктовая линейка и стандарты презентации",
                "Как презентовать продукцию, УТП, работа с возражениями.",
                specialties["Продажи и маркетинг"],
                manager_prod,
            ),
        ]

        courses = []
        for title, desc, spec, creator in courses_data:
            course, _ = Course.objects.get_or_create(
                title=title,
                defaults={
                    "description": desc,
                    "created_by": creator,
                    "specialty": spec,
                    "is_active": True,
                },
            )
            courses.append(course)
            CourseMaterial.objects.get_or_create(
                course=course,
                title=f"Материал: {title}",
                defaults={"material_type": "TEXT", "content": desc},
            )
            # Add multiple lessons per course
            lessons_data = [
                {
                    "title": f"Введение в {title}",
                    "description": "Основные понятия и принципы.",
                    "pages": [
                        {
                            "title": "Теория",
                            "blocks": [
                                {"type": "text", "content": desc},
                                {"type": "text", "content": "Изучите основные принципы и требования."},
                            ],
                        }
                    ],
                    "order": 1,
                },
                {
                    "title": f"Практика: {title}",
                    "description": "Примеры и кейсы из производства.",
                    "pages": [
                        {
                            "title": "Примеры",
                            "blocks": [
                                {"type": "text", "content": "Рассмотрим реальные ситуации на производстве АртКулинарии."},
                                {"type": "text", "content": "Пройдите тест для закрепления материала."},
                            ],
                        }
                    ],
                    "order": 2,
                },
            ]
            for lesson_data in lessons_data:
                Lesson.objects.get_or_create(
                    course=course,
                    title=lesson_data["title"],
                    defaults={
                        "description": lesson_data["description"],
                        "pages": lesson_data["pages"],
                        "order": lesson_data["order"],
                        "is_published": True,
                        "created_by": creator,
                    },
                )

        # Create tests and tasks per course (published) with deadlines
        for course_idx, course in enumerate(courses):
            due = today + timedelta(days=(course_idx % 5) - 2)  # some overdue, some soon
            test, _ = Test.objects.get_or_create(
                course=course,
                title=f"Тест: {course.title}",
                defaults={
                    "description": "Контроль понимания материалов.",
                    "passing_score": 70,
                    "attempts": 2,
                    "due_date": due,
                    "is_published": True,
                    "created_by": course.created_by,
                },
            )
            # Add test to course materials
            CourseMaterial.objects.get_or_create(
                course=course,
                test=test,
                defaults={
                    "title": f"Тест: {course.title}",
                    "material_type": "TEST",
                    "order": 10,
                    "is_required": True,
                },
            )
            if not test.questions.exists():
                # Add realistic questions based on course
                if "Санитария" in course.title:
                    # Single choice
                    q1 = Question.objects.create(
                        test=test,
                        text="Какой температурный режим должен поддерживаться при хранении готовой продукции?",
                        question_type='SINGLE',
                        points=10,
                    )
                    Answer.objects.create(question=q1, text="0-4°C", is_correct=True)
                    Answer.objects.create(question=q1, text="10-15°C", is_correct=False)
                    Answer.objects.create(question=q1, text="20-25°C", is_correct=False)

                    # Multi choice
                    q2 = Question.objects.create(
                        test=test,
                        text="Какие меры личной гигиены обязательны на пищевом производстве? (несколько ответов)",
                        question_type='MULTI',
                        points=15,
                    )
                    Answer.objects.create(question=q2, text="Мыть руки перед работой", is_correct=True)
                    Answer.objects.create(question=q2, text="Носить чистую одежду", is_correct=True)
                    Answer.objects.create(question=q2, text="Курить в цеху", is_correct=False)
                    Answer.objects.create(question=q2, text="Носить украшения", is_correct=False)

                    # Short answer
                    q3 = Question.objects.create(
                        test=test,
                        text="Назовите три основных принципа санитарии на производстве.",
                        question_type='SHORT',
                        points=20,
                    )
                    # No answers for short/long

                elif "HACCP" in course.title:
                    q1 = Question.objects.create(
                        test=test,
                        text="Что означает HACCP?",
                        question_type='SINGLE',
                        points=10,
                    )
                    Answer.objects.create(question=q1, text="Hazard Analysis and Critical Control Points", is_correct=True)
                    Answer.objects.create(question=q1, text="Health and Safety Control Program", is_correct=False)

                    q2 = Question.objects.create(
                        test=test,
                        text="Какие шаги включает анализ рисков в HACCP?",
                        question_type='MULTI',
                        points=15,
                    )
                    Answer.objects.create(question=q2, text="Идентификация потенциальных опасностей", is_correct=True)
                    Answer.objects.create(question=q2, text="Определение критических контрольных точек", is_correct=True)

                elif "Технологические карты" in course.title:
                    q1 = Question.objects.create(
                        test=test,
                        text="Что обязательно указывается в технологической карте?",
                        question_type='MULTI',
                        points=15,
                    )
                    Answer.objects.create(question=q1, text="Норма выхода готового продукта", is_correct=True)
                    Answer.objects.create(question=q1, text="Состав ингредиентов", is_correct=True)
                    Answer.objects.create(question=q1, text="Цвет упаковки", is_correct=False)

                elif "Маркировка" in course.title:
                    q1 = Question.objects.create(
                        test=test,
                        text="Какая информация обязательна на этикетке пищевого продукта?",
                        question_type='MULTI',
                        points=15,
                    )
                    Answer.objects.create(question=q1, text="Состав", is_correct=True)
                    Answer.objects.create(question=q1, text="Срок годности", is_correct=True)
                    Answer.objects.create(question=q1, text="Цена", is_correct=False)

                elif "Холодовая цепь" in course.title:
                    q1 = Question.objects.create(
                        test=test,
                        text="Какой принцип используется для управления запасами на складе?",
                        question_type='SINGLE',
                        points=10,
                    )
                    Answer.objects.create(question=q1, text="FIFO (первым поступил - первым ушел)", is_correct=True)
                    Answer.objects.create(question=q1, text="LIFO (последним поступил - первым ушел)", is_correct=False)

                elif "Продуктовая линейка" in course.title:
                    q1 = Question.objects.create(
                        test=test,
                        text="Что такое УТП?",
                        question_type='SHORT',
                        points=20,
                    )

                else:
                    # Fallback simple questions
                    for q_idx in range(1, 4):
                        q = Question.objects.create(
                            test=test,
                            text=f"Вопрос {q_idx}: {course.title}",
                        )
                        Answer.objects.create(question=q, text="Правильный ответ", is_correct=True)
                        Answer.objects.create(question=q, text="Неправильный ответ 1", is_correct=False)
                        Answer.objects.create(question=q, text="Неправильный ответ 2", is_correct=False)

            task, _ = Task.objects.get_or_create(
                course=course,
                title=f"Практика: {course.title}",
                defaults={
                    "description": "Выполните практическое задание по материалу курса.",
                    "criteria": "Полнота, корректность, соответствие стандартам.",
                    "task_type": "PRACTICAL",
                    "max_score": 100,
                    "created_by": course.created_by,
                    "due_date": due,
                    "is_active": True,
                    "is_published": True,
                },
            )

        # Enrollments with different progress and due dates (for reminders + progress graphs)
        for emp_idx, emp in enumerate(employees):
            for course_idx, course in enumerate(courses):
                due = today + timedelta(days=((course_idx + emp_idx) % 7) - 2)
                progress = ((emp_idx * 13 + course_idx * 17) % 101)
                completed = progress >= 100
                status = "COMPLETED" if completed else "IN_PROGRESS" if progress > 0 else "ASSIGNED"
                if due < today and not completed:
                    status = "OVERDUE"
                Enrollment.objects.get_or_create(
                    user=emp,
                    course=course,
                    defaults={
                        "assigned_by": manager_prod,
                        "due_date": due,
                        "status": status,
                        "progress": progress,
                        "completed": completed,
                    },
                )

        # Task assignments and submissions
        for emp_idx, emp in enumerate(employees):
            for course_idx, course in enumerate(courses[:3]):  # First 3 courses
                task = Task.objects.filter(course=course).first()
                if not task:
                    continue
                due = today + timedelta(days=((course_idx + emp_idx) % 7) - 2)
                assignment, _ = TaskAssignment.objects.get_or_create(
                    task=task,
                    user=emp,
                    defaults={
                        "assigned_by": manager_prod,
                        "due_date": due,
                        "status": "COMPLETED" if (emp_idx + course_idx) % 2 == 0 else "SUBMITTED",
                    },
                )
                if assignment.status == "COMPLETED":
                    TaskSubmission.objects.get_or_create(
                        assignment=assignment,
                        defaults={
                            "content": "Выполнено задание по курсу. Приложены фото и описание процесса.",
                            "score": 85 + ((emp_idx * 5) % 16),  # 85-100
                            "reviewer": manager_quality,
                            "reviewed_at": now - timedelta(days=1),
                        },
                    )
                    TaskReview.objects.get_or_create(
                        manager=manager_quality,
                        task_submission=TaskSubmission.objects.filter(assignment=assignment).first(),
                        defaults={
                            "comment": "Отличная работа, все критерии соблюдены.",
                            "rating": 5,
                            "created_at": now - timedelta(days=1),
                        },
                    )

        # Results, feedback, reviews and competency assessments (spread across months)
        for emp_idx, emp in enumerate(employees):
            for course_idx, course in enumerate(courses[:4]):
                test = Test.objects.filter(course=course).first()
                if not test:
                    continue
                months_ago = (emp_idx + course_idx) % 5
                completed_at = now - timedelta(days=30 * months_ago + (emp_idx * 2))
                score = 55 + ((emp_idx * 9 + course_idx * 11) % 46)  # 55..100
                passed = score >= test.passing_score
                status = TestResult.Status.PASSED if passed else TestResult.Status.FAILED
                result = TestResult.objects.create(
                    user=emp,
                    test=test,
                    score=score,
                    passed=passed,
                    status=status,
                    attempt_number=1,
                    completed_at=completed_at,
                )
                Feedback.objects.create(
                    manager=manager_quality,
                    test_result=result,
                    comment="Комментарий менеджера по результату теста.",
                    rating=5 if passed else 3,
                    created_at=completed_at,
                )
                TrainingEvent.objects.create(
                    user=emp,
                    event_type="TEST_COMPLETED",
                    course=course,
                    test=test,
                    created_at=completed_at,
                )

                comp = competencies["Пищевая безопасность"] if course_idx in {0, 1, 3} else competencies["Технологические карты"]
                CompetencyAssessment.objects.create(
                    user=emp,
                    competency=comp,
                    assessor=manager_quality,
                    level=min(10, max(0, int(score / 10))),
                    comment="Оценка компетенции на основе результатов обучения.",
                    test_result=result,
                    assessed_at=completed_at,
                )

        # Add some audit logs
        for emp in employees[:3]:
            AuditLog.objects.create(
                actor=emp,
                action="LOGIN",
                message="Пользователь вошел в систему",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                created_at=now - timedelta(hours=2),
            )
            AuditLog.objects.create(
                actor=emp,
                action="COURSE_COMPLETED",
                message=f"Завершен курс: {courses[0].title}",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                created_at=now - timedelta(days=1),
            )

        # Add dashboard data
        Dashboard.objects.get_or_create(
            title="Общая статистика обучения",
            defaults={
                "config": {"charts": ["progress", "completion", "scores"]},
                "owner": analyst,
            },
        )

        # Add reports
        Report.objects.get_or_create(
            title="Отчет по прохождению курсов",
            defaults={
                "report_type": "COURSE_COMPLETION",
                "filters": {"filters": ["department", "date_range"]},
                "owner": analyst,
            },
        )

        for emp_idx, emp in enumerate(employees):
            # One reviewed submission per employee for first course
            course = courses[0]
            task = Task.objects.filter(course=course).first()
            if not task:
                continue
            assignment, _ = TaskAssignment.objects.get_or_create(
                task=task,
                user=emp,
                defaults={
                    "assigned_by": manager_prod,
                    "due_date": today + timedelta(days=2),
                    "status": "ASSIGNED",
                    "priority": 3,
                },
            )
            submitted_at = now - timedelta(days=3 + emp_idx)
            submission, _ = TaskSubmission.objects.get_or_create(
                assignment=assignment,
                defaults={
                    "content": "Практическая работа (пример) — чек-лист и выводы.",
                    "status": TaskSubmission.Status.SUBMITTED,
                    "submitted_at": submitted_at,
                },
            )
            submission.status = TaskSubmission.Status.APPROVED if emp_idx % 3 != 0 else TaskSubmission.Status.NEEDS_CHANGES
            submission.score = 80 if submission.status == TaskSubmission.Status.APPROVED else 55
            submission.reviewed_at = submitted_at + timedelta(days=1)
            submission.reviewer = manager_prod
            submission.save(update_fields=["status", "score", "reviewed_at", "reviewer"])

            TaskReview.objects.get_or_create(
                manager=manager_prod,
                task_submission=submission,
                defaults={"comment": "Отзыв по практическому заданию.", "rating": 4},
            )
            TrainingEvent.objects.create(
                user=emp,
                event_type="TASK_SUBMITTED",
                course=course,
                task=task,
                created_at=submitted_at,
            )

            comp = competencies["Командная работа"]
            level = 6 + (emp_idx % 4)
            CompetencyAssessment.objects.create(
                user=emp,
                competency=comp,
                assessor=manager_prod,
                level=level,
                comment="Оценка по практическому заданию.",
                task_submission=submission,
                assessed_at=submission.reviewed_at or now,
            )
            UserCompetency.objects.update_or_create(
                user=emp,
                competency=comp,
                defaults={"level": level, "source": UserCompetency.Source.TASK},
            )

        Dashboard.objects.get_or_create(
            owner=analyst,
            title="АртКулинария — аналитика обучения",
            defaults={
                "config": {
                    "widgets": ["progress", "scores", "departments"],
                    "default_filters": {"period": "month"},
                }
            },
        )
        report, _ = Report.objects.get_or_create(
            owner=analyst,
            title="Отчёт: прогресс обучения (демо)",
            defaults={"report_type": "PROGRESS", "filters": {"period": "month"}},
        )
        ReportExport.objects.get_or_create(
            report=report,
            export_format="PDF",
            defaults={"status": "READY", "file_path": "reports/artculinary_progress.pdf"},
        )
        BackupRecord.objects.get_or_create(
            created_by=admin,
            defaults={"status": "CREATED", "file_path": "backups/demo_db.sqlite3"},
        )
        AuditLog.objects.get_or_create(
            actor=admin,
            action="seed_artculinary",
            defaults={"object_type": "system", "message": "ArtCulinary demo data created"},
        )
