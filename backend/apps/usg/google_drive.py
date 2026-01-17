"""
Google Drive integration for USG report PDF storage.
Uses Google Drive API with Service Account authentication.
"""
import os
import json
import hashlib
from datetime import datetime
from django.conf import settings


# Check if google libraries are available
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    print("Warning: Google Drive API libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")


def get_drive_service():
    """
    Get authenticated Google Drive service instance.
    
    Returns:
        Resource - Google Drive API service or None if not configured
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        return None
    
    # Get service account credentials from environment
    credentials_json = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON')
    credentials_path = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH')
    
    credentials = None
    
    if credentials_json:
        # Parse JSON string
        try:
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
        except Exception as e:
            print(f"Error parsing GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON: {e}")
            return None
    elif credentials_path and os.path.exists(credentials_path):
        # Load from file
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
        except Exception as e:
            print(f"Error loading credentials from {credentials_path}: {e}")
            return None
    else:
        print("Google Drive credentials not configured")
        return None
    
    # Build Drive service
    try:
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error building Drive service: {e}")
        return None


def get_or_create_folder(service, folder_name, parent_folder_id=None):
    """
    Get or create a folder in Google Drive.
    
    Args:
        service: Drive service instance
        folder_name: str - Folder name to create
        parent_folder_id: str - Parent folder ID (optional)
    
    Returns:
        str - Folder ID or None
    """
    if not service:
        return None
    
    try:
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]['id']
        
        # Create new folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    
    except Exception as e:
        print(f"Error creating folder {folder_name}: {e}")
        return None


def upload_pdf_to_drive(pdf_content, filename, study):
    """
    Upload PDF to Google Drive with year/month folder structure.
    
    Args:
        pdf_content: ContentFile - PDF file content
        filename: str - Filename for the PDF
        study: UsgStudy - Study instance for metadata
    
    Returns:
        dict - {
            'file_id': str,
            'folder_id': str,
            'sha256': str
        } or None if failed
    """
    service = get_drive_service()
    if not service:
        print("Drive service not available, skipping upload")
        return None
    
    try:
        # Get base folder from environment
        base_folder_id = os.getenv('GOOGLE_DRIVE_USG_FOLDER_ID')
        
        # Create year/month folder structure
        now = datetime.now()
        year_folder = now.strftime('%Y')
        month_folder = now.strftime('%m')
        
        # Get or create year folder
        year_folder_id = get_or_create_folder(service, year_folder, base_folder_id)
        if not year_folder_id:
            year_folder_id = base_folder_id
        
        # Get or create month folder
        month_folder_id = get_or_create_folder(service, month_folder, year_folder_id)
        if not month_folder_id:
            month_folder_id = year_folder_id
        
        # Calculate SHA256 hash
        pdf_bytes = pdf_content.read()
        pdf_content.seek(0)  # Reset for upload
        sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
        
        # Upload file
        file_metadata = {
            'name': filename,
            'parents': [month_folder_id] if month_folder_id else []
        }
        
        media = MediaIoBaseUpload(
            pdf_content,
            mimetype='application/pdf',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        
        return {
            'file_id': file_id,
            'folder_id': month_folder_id,
            'sha256': sha256_hash
        }
    
    except Exception as e:
        print(f"Error uploading PDF to Drive: {e}")
        return None


def get_pdf_from_drive(file_id):
    """
    Retrieve PDF content from Google Drive.
    
    Args:
        file_id: str - Google Drive file ID
    
    Returns:
        bytes - PDF content or None
    """
    service = get_drive_service()
    if not service:
        return None
    
    try:
        request = service.files().get_media(fileId=file_id)
        pdf_bytes = request.execute()
        return pdf_bytes
    except Exception as e:
        print(f"Error retrieving PDF from Drive: {e}")
        return None


def delete_pdf_from_drive(file_id):
    """
    Delete a PDF from Google Drive (use with caution).
    
    Args:
        file_id: str - Google Drive file ID
    
    Returns:
        bool - Success status
    """
    service = get_drive_service()
    if not service:
        return False
    
    try:
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting PDF from Drive: {e}")
        return False
