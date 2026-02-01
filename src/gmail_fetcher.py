"""Gmail API integration for fetching Lose It! email attachments."""
import os
import base64
import io
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailFetcher:
    """Fetches emails and attachments from Gmail."""
    
    def __init__(self):
        self.label_name = os.getenv('GMAIL_LABEL_NAME', 'Lose It! Weekly Summary')
        self.credentials_file = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json')
        self.token_file = os.getenv('GMAIL_TOKEN_FILE', 'token.json')
        self.service = None
        
    def authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.credentials_file}\n"
                        "Please download OAuth 2.0 credentials from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        print(f"✓ Authenticated with Gmail API")
        return True
    
    def get_label_id(self) -> Optional[str]:
        """Get the Gmail label ID for the specified label name."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                if label['name'] == self.label_name:
                    return label['id']
            
            print(f"✗ Label '{self.label_name}' not found in Gmail")
            return None
        except Exception as e:
            print(f"✗ Error getting label ID: {e}")
            return None
    
    def fetch_messages(self, days_back: int = 90) -> List[Dict]:
        """
        Fetch messages with the specified label.
        
        Args:
            days_back: Number of days to look back for messages
            
        Returns:
            List of message data with attachments
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        label_id = self.get_label_id()
        if not label_id:
            return []
        
        # Calculate date filter
        after_date = datetime.now() - timedelta(days=days_back)
        query = f"after:{after_date.strftime('%Y/%m/%d')}"
        
        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[label_id],
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            print(f"✓ Found {len(messages)} messages with label '{self.label_name}'")
            
            message_data = []
            for msg in messages:
                msg_detail = self._get_message_with_attachments(msg['id'])
                if msg_detail:
                    message_data.append(msg_detail)
            
            return message_data
            
        except Exception as e:
            print(f"✗ Error fetching messages: {e}")
            return []
    
    def _get_message_with_attachments(self, msg_id: str) -> Optional[Dict]:
        """Get message details including CSV attachments."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract date
            headers = message['payload'].get('headers', [])
            date_str = None
            for header in headers:
                if header['name'].lower() == 'date':
                    date_str = header['value']
                    break
            
            attachments = []
            
            # Check for attachments in parts
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part.get('filename') and part['filename'].endswith('.csv'):
                        attachment_data = self._get_attachment(msg_id, part['body']['attachmentId'])
                        if attachment_data:
                            attachments.append({
                                'filename': part['filename'],
                                'data': attachment_data
                            })
            
            if attachments:
                return {
                    'id': msg_id,
                    'date': date_str,
                    'attachments': attachments
                }
            
            return None
            
        except Exception as e:
            print(f"✗ Error getting message {msg_id}: {e}")
            return None
    
    def _get_attachment(self, msg_id: str, attachment_id: str) -> Optional[bytes]:
        """Download attachment data."""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=msg_id,
                id=attachment_id
            ).execute()
            
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            return file_data
            
        except Exception as e:
            print(f"✗ Error downloading attachment: {e}")
            return None
