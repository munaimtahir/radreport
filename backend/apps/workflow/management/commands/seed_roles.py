"""
Seed RBAC groups only (no demo users by default).
Use --with-demo-users to create demo users.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


REQUIRED_GROUPS = [
    "registration_desk",
    "performance_desk",
    "verification_desk",
    "doctor",
]


class Command(BaseCommand):
    help = "Seed required RBAC groups (registration_desk, performance_desk, verification_desk, doctor)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-demo-users",
            action="store_true",
            help="Create demo users and assign to groups.",
        )

    def handle(self, *args, **options):
        with_demo = options["with_demo_users"]

        created_groups = []
        for name in REQUIRED_GROUPS:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                created_groups.append(name)

        self.stdout.write(self.style.SUCCESS("Role seeding complete."))
        if created_groups:
            self.stdout.write(self.style.SUCCESS(f"Created groups: {', '.join(created_groups)}"))
        else:
            self.stdout.write("Groups already exist.")

        if with_demo:
            user_model = get_user_model()
            demo_users = [
                ("reg_user", "reg_user", "registration_desk"),
                ("perf_user", "perf_user", "performance_desk"),
                ("ver_user", "ver_user", "verification_desk"),
                ("doctor_user", "doctor_user", "doctor"),
            ]
            created_users = []
            for username, password, group_name in demo_users:
                user = user_model.objects.filter(username=username).first()
                if not user:
                    user = user_model.objects.create_user(username=username, password=password)
                    created_users.append(username)
                group = Group.objects.get(name=group_name)
                if group not in user.groups.all():
                    user.groups.add(group)
            if created_users:
                self.stdout.write(self.style.SUCCESS(f"Created demo users: {', '.join(created_users)}"))
            for username, password, group_name in demo_users:
                self.stdout.write(f"  - {username} / {password} (group: {group_name})")
