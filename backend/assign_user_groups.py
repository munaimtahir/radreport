#!/usr/bin/env python
"""
Script to assign users to groups for RBAC
Usage: python manage.py shell < assign_user_groups.py
Or: python assign_user_groups.py (if Django is in PYTHONPATH)
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from django.contrib.auth.models import User, Group

def assign_user_groups():
    """Assign users to appropriate groups"""
    print("=" * 60)
    print("Assigning Users to Groups for RBAC")
    print("=" * 60)
    
    # Get groups
    registration_group, _ = Group.objects.get_or_create(name="Registration")
    performance_group, _ = Group.objects.get_or_create(name="Performance")
    verification_group, _ = Group.objects.get_or_create(name="Verification")
    
    print(f"\nGroups available:")
    print(f"  - {registration_group.name}")
    print(f"  - {performance_group.name}")
    print(f"  - {verification_group.name}")
    
    # Get all users
    users = User.objects.all()
    print(f"\nUsers found: {users.count()}")
    
    # Assign users to groups
    # For MVP/testing: assign each user to all groups
    # In production, assign users to specific groups based on their role
    for user in users:
        print(f"\nProcessing user: {user.username}")
        
        # Clear existing groups first
        user.groups.clear()
        
        # For admin users, assign to all groups
        if user.is_superuser or user.is_staff:
            user.groups.add(registration_group, performance_group, verification_group)
            print(f"  ✓ Assigned to all groups (admin/staff)")
        else:
            # For regular users, you can customize this logic
            # For now, assign to all groups for testing
            user.groups.add(registration_group, performance_group, verification_group)
            print(f"  ✓ Assigned to all groups (for testing)")
        
        # Show assigned groups
        user_groups = user.groups.all()
        print(f"  Groups: {', '.join([g.name for g in user_groups])}")
    
    print("\n" + "=" * 60)
    print("User group assignment completed!")
    print("=" * 60)
    print("\nNote: In production, assign users to specific groups:")
    print("  - Registration desk users → Registration group")
    print("  - Performance desk users → Performance group")
    print("  - Verification desk users → Verification group")
    print("\nYou can also assign users via Django admin at /admin/auth/user/")

if __name__ == "__main__":
    assign_user_groups()
