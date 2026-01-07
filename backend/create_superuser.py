#!/usr/bin/env python
"""
Quick script to create a Django superuser for RIMS
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    username = "admin"
    email = "admin@rims.local"
    password = "admin123"
    
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"✓ Updated existing user: {username} / {password}")
    else:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✓ Created superuser: {username} / {password}")
    
    print(f"\nYou can now login with:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")

if __name__ == "__main__":
    create_superuser()
