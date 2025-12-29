import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import CREDENTIALS_FILE, TOKEN_FILE, DOC_ID

SCOPES = ["https://www.googleapis.com/auth/documents"]

class DocsClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Handle Google OAuth authentication."""
        if TOKEN_FILE.exists():
            self.creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"credentials.json not found at {CREDENTIALS_FILE}\n"
                        "Download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, "w") as f:
                f.write(self.creds.to_json())
        
        self.service = build("docs", "v1", credentials=self.creds)
    
    def read_document(self, doc_id: str = DOC_ID) -> str:
        """Read entire document as plain text."""
        doc = self.service.documents().get(documentId=doc_id).execute()
        
        text = ""
        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        text += elem["textRun"].get("content", "")
        
        return text
    
    def get_document_structure(self, doc_id: str = DOC_ID) -> dict:
        """Get document with position info for editing."""
        return self.service.documents().get(documentId=doc_id).execute()
    
    def find_marker_position(self, doc_id: str, marker: str) -> tuple[int, int] | None:
        """Find start and end index of a marker in the document."""
        doc = self.get_document_structure(doc_id)
        full_text = ""
        
        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        full_text += elem["textRun"].get("content", "")
        
        start = full_text.find(marker)
        if start == -1:
            return None
        
        return (start, start + len(marker))
    
    def find_section_end(self, doc_id: str, marker: str, all_markers: list[str]) -> int | None:
        """Find where to insert content (before next marker or end of doc)."""
        doc = self.get_document_structure(doc_id)
        full_text = ""
        
        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        full_text += elem["textRun"].get("content", "")
        
        marker_pos = full_text.find(marker)
        if marker_pos == -1:
            return None
        
        # Find next marker after this one
        next_marker_pos = len(full_text)
        for m in all_markers:
            if m == marker:
                continue
            pos = full_text.find(m, marker_pos + len(marker))
            if pos != -1 and pos < next_marker_pos:
                next_marker_pos = pos
        
        # Back up to before any newlines preceding the next marker
        insert_pos = next_marker_pos
        while insert_pos > marker_pos + len(marker) and full_text[insert_pos - 1] in "\n\r":
            insert_pos -= 1
        
        return insert_pos
    
    def append_to_section(self, doc_id: str, marker: str, content: str, all_markers: list[str]) -> bool:
        """Append content to the end of a section (before next marker)."""
        insert_pos = self.find_section_end(doc_id, marker, all_markers)
        if insert_pos is None:
            print(f"Marker not found: {marker}")
            return False
        
        # Add newlines for formatting
        formatted_content = f"\n\n{content}"
        
        requests = [
            {
                "insertText": {
                    "location": {"index": insert_pos},
                    "text": formatted_content
                }
            }
        ]
        
        self.service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()
        
        return True


# Quick test
if __name__ == "__main__":
    client = DocsClient()
    text = client.read_document()
    print(f"Document length: {len(text)} characters")
    print(f"First 500 chars:\n{text[:500]}")
