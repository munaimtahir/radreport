from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed Phase 3 desk roles and demo users (registration/performance/verification)."

    def handle(self, *args, **options):
        groups = [
            "registration",
            "performance",
            "verification",
        ]

        created_groups = []
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                created_groups.append(group.name)

        user_model = get_user_model()
        demo_users = [
            ("reg_user", "reg_user", "registration"),
            ("perf_user", "perf_user", "performance"),
            ("ver_user", "ver_user", "verification"),
        ]

        created_users = []
        for username, password, group_name in demo_users:
            user = user_model.objects.filter(username=username).first()
            if not user:
                user = user_model.objects.create_user(username=username, password=password)
                created_users.append(username)
            group = Group.objects.get(name=group_name)
            user.groups.add(group)

        self.stdout.write(self.style.SUCCESS("Phase 3 role seeding complete."))
        if created_groups:
            self.stdout.write(self.style.SUCCESS(f"Created groups: {', '.join(created_groups)}"))
        else:
            self.stdout.write("Groups already exist.")

        if created_users:
            self.stdout.write(self.style.SUCCESS(f"Created users: {', '.join(created_users)}"))
        else:
            self.stdout.write("Demo users already exist.")

        for username, password, group_name in demo_users:
            self.stdout.write(
                f"- {username} / {password} (group: {group_name})"
            )
