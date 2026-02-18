# Comprehensive Roles and Permissions Update

## Overview
This document describes the comprehensive update to the role-based access control (RBAC) system, replacing desk-based roles with clear, role-based permissions.

## New Roles

### 1. Receptionist
- **Purpose**: Patient registration and visit creation
- **Permissions**:
  - Create service visits
  - Register patients
  - View patient workflow
  - Print reports
- **Legacy Mapping**: `registration_desk`, `registration` → `receptionist`

### 2. Technologist
- **Purpose**: Perform scans and create reports
- **Permissions**:
  - Start reports
  - Save draft reports
  - Submit reports for verification
  - View reporting worklist
  - View patient workflow
  - Print reports
- **Legacy Mapping**: `performance_desk`, `performance` → `technologist`

### 3. Radiologist
- **Purpose**: Verify and publish reports
- **Permissions**:
  - Verify submitted reports
  - Publish verified reports
  - Return reports for correction
  - Create service visits (can also register)
  - View all workflow pages
  - View reporting worklist
  - Print reports
- **Legacy Mapping**: `verification_desk`, `verification` → `radiologist`

### 4. Manager
- **Purpose**: Administrative access
- **Permissions**:
  - Access backup operations
  - All workflow permissions (inherited)
  - Admin settings (if also superuser)
- **Legacy Mapping**: `admin` → `manager`

## Backend Changes

### Permission Classes (`backend/apps/workflow/permissions.py`)

#### New Permission Classes
- `IsReceptionist`: Checks for receptionist role
- `IsTechnologist`: Checks for technologist role
- `IsRadiologist`: Checks for radiologist role
- `IsManager`: Checks for manager role

#### Updated Permission Classes
- All legacy permission classes (`IsRegistrationDesk`, `IsPerformanceDesk`, `IsVerificationDesk`) now delegate to new classes for backward compatibility
- `IsAnyDesk`: Updated to check for all workflow roles (receptionist, technologist, radiologist)

#### Helper Functions
- `_get_user_group_names()`: Gets lowercase group names for a user
- `_has_role()`: Checks if user has any of the specified roles (case-insensitive)

### API Endpoints Updated

#### Workflow API (`backend/apps/workflow/api.py`)
- `ServiceVisitViewSet`: Uses `IsAnyDesk` (all workflow roles)
- `ServiceVisitItemViewSet`: Uses `IsAnyDesk` (all workflow roles)
- `create_visit` action: Uses `IsRegistrationOrVerificationDesk` (receptionist or radiologist)

#### Reporting API (`backend/apps/reporting/views.py`)
- `ReportTemplateV2ViewSet`: Uses `IsAdminUser` (admin only)
- `ServiceReportTemplateV2ViewSet`: Uses `IsAdminUser` (admin only)
- `ReportBlockLibraryViewSet`: Uses `IsAdminUser` (admin only)
- `ReportWorkItemViewSet`: Uses `IsAnyDesk` (all workflow roles)
  - `save` action: Uses `IsTechnologist` (technologists can save drafts)
  - `submit` action: Uses `IsTechnologist` (technologists can submit)
  - `verify` action: Uses `IsRadiologist` (radiologists can verify)
  - `publish` action: Uses `IsRadiologist` (radiologists can publish)
  - `return_for_correction` action: Uses `IsRadiologist` (radiologists can return)

#### Backup Operations (`backend/apps/workflow/backup_ops.py`)
- All endpoints: Use `IsManager` (managers can access backups)

### Seed Command (`backend/apps/workflow/management/commands/seed_roles_comprehensive.py`)

New comprehensive seed command that:
- Creates all four roles: receptionist, technologist, radiologist, manager
- Supports `--with-demo-users` flag to create demo users
- Supports `--migrate-legacy` flag to migrate users from legacy roles

## Frontend Changes

### Route Protection (`frontend/src/ui/App.tsx`)

#### Role Checks
- Updated to use new role names with backward compatibility
- Helper function `hasRole()` checks for roles case-insensitively

#### Navigation Menu
- **Registration**: Visible to Receptionist and Radiologist
- **Patient Workflow**: Visible to all workflow roles
- **Reporting Worklist**: Visible to Technologist and Radiologist
- **Print Reports**: Visible to all workflow roles
- **Settings**: Visible to superusers only
- **Backups**: Visible to Manager and superusers

#### Route Guards
All routes are protected with appropriate permission checks:
- `/registration`: Receptionist or Radiologist
- `/patients/workflow`: Any workflow role
- `/reporting/worklist`: Technologist or Radiologist
- `/reports`: Any workflow role
- `/settings/*`: Superuser only
- `/settings/backups`: Manager or superuser

## Migration Path

### For Existing Users

1. **Run the seed command**:
   ```bash
   python manage.py seed_roles_comprehensive
   ```

2. **Migrate existing users** (optional):
   ```bash
   python manage.py seed_roles_comprehensive --migrate-legacy
   ```

3. **Create demo users** (optional):
   ```bash
   python manage.py seed_roles_comprehensive --with-demo-users
   ```

### Role Mapping
- Users with `registration_desk` or `registration` → Add `receptionist` role
- Users with `performance_desk` or `performance` → Add `technologist` role
- Users with `verification_desk` or `verification` → Add `radiologist` role
- Users with `admin` → Add `manager` role

## Backward Compatibility

The system maintains full backward compatibility:
- Legacy role names are still recognized
- All existing permission classes continue to work
- Frontend checks for both new and legacy role names
- No breaking changes to existing API endpoints

## Testing Checklist

### Receptionist Role
- [ ] Can access `/registration`
- [ ] Can create service visits
- [ ] Can view `/patients/workflow`
- [ ] Can view `/reports`
- [ ] Cannot access `/reporting/worklist`
- [ ] Cannot verify or publish reports

### Technologist Role
- [ ] Can access `/reporting/worklist`
- [ ] Can start reports
- [ ] Can save draft reports
- [ ] Can submit reports
- [ ] Can view `/patients/workflow`
- [ ] Can view `/reports`
- [ ] Cannot verify or publish reports
- [ ] Cannot access `/registration`

### Radiologist Role
- [ ] Can access all workflow pages
- [ ] Can access `/registration`
- [ ] Can access `/reporting/worklist`
- [ ] Can verify submitted reports
- [ ] Can publish verified reports
- [ ] Can return reports for correction
- [ ] Can view `/patients/workflow`
- [ ] Can view `/reports`

### Manager Role
- [ ] Can access `/settings/backups`
- [ ] Can perform backup operations
- [ ] Has all workflow permissions (if also assigned workflow role)

## Files Changed

### Backend
- `backend/apps/workflow/permissions.py` - Updated permission classes
- `backend/apps/workflow/api.py` - Updated API permissions
- `backend/apps/reporting/views.py` - Updated reporting permissions
- `backend/apps/workflow/backup_ops.py` - Updated backup permissions
- `backend/apps/workflow/management/commands/seed_roles_comprehensive.py` - New seed command

### Frontend
- `frontend/src/ui/App.tsx` - Updated role checks and navigation

## Notes

- All role checks are case-insensitive
- Superusers have all permissions regardless of role
- Legacy role names are supported for smooth migration
- The system checks for both new and legacy role names simultaneously
