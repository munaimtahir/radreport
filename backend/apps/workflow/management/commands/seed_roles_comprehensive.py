"""
Comprehensive role seeding command.
Creates roles: receptionist, radiologist, technologist, manager
with appropriate permissions mapping.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


REQUIRED_ROLES = [
    "receptionist",      # Can register patients, create visits
    "technologist",      # Can perform scans, start reports, save drafts
    "radiologist",       # Can verify, publish, return reports
    "manager",          # Can access admin settings, backups, etc.
]

# Legacy role names for backward compatibility
LEGACY_ROLE_MAPPING = {
    "registration_desk": "receptionist",
    "performance_desk": "technologist",
    "verification_desk": "radiologist",
    "registration": "receptionist",
    "performance": "technologist",
    "verification": "radiologist",
}


class Command(BaseCommand):
    help = "Seed comprehensive RBAC roles (receptionist, radiologist, technologist, manager)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-demo-users",
            action="store_true",
            help="Create demo users and assign to roles.",
        )
        parser.add_argument(
            "--migrate-legacy",
            action="store_true",
            help="Migrate users from legacy roles to new roles.",
        )

    def handle(self, *args, **options):
        with_demo = options["with_demo_users"]
        migrate_legacy = options["migrate_legacy"]

        created_groups = []
        for role_name in REQUIRED_ROLES:
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                created_groups.append(role_name)
            else:
                self.stdout.write(f"Role '{role_name}' already exists.")

        self.stdout.write(self.style.SUCCESS("Role seeding complete."))
        if created_groups:
            self.stdout.write(self.style.SUCCESS(f"Created roles: {', '.join(created_groups)}"))
        else:
            self.stdout.write("All roles already exist.")

        # Migrate legacy roles if requested
        if migrate_legacy:
            user_model = get_user_model()
            migrated_count = 0
            for legacy_name, new_name in LEGACY_ROLE_MAPPING.items():
                try:
                    legacy_group = Group.objects.get(name=legacy_name)
                    new_group = Group.objects.get(name=new_name)
                    users = user_model.objects.filter(groups=legacy_group)
                    for user in users:
                        if new_group not in user.groups.all():
                            user.groups.add(new_group)
                            migrated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Migrated {users.count()} users from '{legacy_name}' to '{new_name}'"
                        )
                    )
                except Group.DoesNotExist:
                    self.stdout.write(f"Legacy group '{legacy_name}' not found, skipping.")

            if migrated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Total users migrated: {migrated_count}")
                )

        if with_demo:
            user_model = get_user_model()
            demo_users = [
                ("receptionist_user", "receptionist_user", "receptionist"),
                ("technologist_user", "technologist_user", "technologist"),
                ("radiologist_user", "radiologist_user", "radiologist"),
                ("manager_user", "manager_user", "manager"),
            ]
            created_users = []
            for username, password, role_name in demo_users:
                user = user_model.objects.filter(username=username).first()
                if not user:
                    user = user_model.objects.create_user(username=username, password=password)
                    created_users.append(username)
                group = Group.objects.get(name=role_name)
                if group not in user.groups.all():
                    user.groups.add(group)
            if created_users:
                self.stdout.write(
                    self.style.SUCCESS(f"Created demo users: {', '.join(created_users)}")
                )
            for username, password, role_name in demo_users:
                self.stdout.write(f"  - {username} / {password} (role: {role_name})")
