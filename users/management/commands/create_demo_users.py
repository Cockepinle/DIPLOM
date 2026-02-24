from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from users.models import Specialty, Position


class Command(BaseCommand):
    help = "Create demo users for API testing (employee, manager, admin)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="Test12345!",
            help="Password for all demo users (default: Test12345!)",
        )

    def handle(self, *args, **options):
        password = options["password"]
        User = get_user_model()
        specialty, _ = Specialty.objects.get_or_create(
            name="Общая",
            defaults={"description": "Общая специализация"},
        )
        position, _ = Position.objects.get_or_create(
            name="Сотрудник",
            defaults={"description": "Базовая должность"},
        )

        users_data = [
            {
                "email": "employee@example.com",
                "first_name": "Employee",
                "last_name": "User",
                "role": "EMPLOYEE",
                "specialty": specialty,
                "position": position,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "manager@example.com",
                "first_name": "Manager",
                "last_name": "User",
                "role": "MANAGER",
                "position": position,
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "role": "ADMIN",
                "position": position,
                "is_staff": True,
                "is_superuser": True,
            },
        ]

        created = 0
        updated = 0

        for data in users_data:
            user, was_created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": data["role"],
                    "specialty": data.get("specialty"),
                    "position": data.get("position"),
                    "is_staff": data["is_staff"],
                    "is_superuser": data["is_superuser"],
                },
            )

            if was_created:
                user.set_password(password)
                user.save()
                created += 1
            else:
                changed = False
                for key, value in data.items():
                    if getattr(user, key) != value:
                        setattr(user, key, value)
                        changed = True
                if not user.check_password(password):
                    user.set_password(password)
                    changed = True
                if changed:
                    user.save()
                    updated += 1

        self.stdout.write(self.style.SUCCESS("Demo users ready."))
        self.stdout.write(f"Created: {created}, Updated: {updated}")
        self.stdout.write("Credentials (email):")
        self.stdout.write("  employee@example.com")
        self.stdout.write("  manager@example.com")
        self.stdout.write("  admin@example.com")
        self.stdout.write(f"Password: {password}")
