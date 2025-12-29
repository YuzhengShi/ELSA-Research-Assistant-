import sqlite3
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from brain import SecondBrain
from llm import extract_remember_content
from config import BASE_DIR

# === Database Setup ===
DB_PATH = BASE_DIR / "history.db"

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# === FastAPI App ===
app = FastAPI(title="Second Brain")

# Serve static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Global brain instance
brain: SecondBrain = None
current_conversation_id: int = None
pending_remember: dict = None

# === Request/Response Models ===
class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    pending_confirmation: bool = False
    classification: dict | None = None

class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: str
    message_count: int

# === Startup ===
@app.on_event("startup")
async def startup():
    global brain
    print("Initializing Second Brain...")
    init_db()
    brain = SecondBrain()
    brain.index_document()
    print("Ready!")

# === Routes ===
@app.get("/")
async def root():
    return FileResponse(static_dir / "index.html")

@app.get("/api/conversations")
async def list_conversations() -> list[ConversationSummary]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.id, c.title, c.created_at,
                   COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT 50
        """).fetchall()
    
    return [
        ConversationSummary(
            id=r["id"],
            title=r["title"] or "Untitled",
            created_at=r["created_at"],
            message_count=r["message_count"]
        )
        for r in rows
    ]

@app.get("/api/conversations/{conv_id}/messages")
async def get_messages(conv_id: int):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT role, content, timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """, (conv_id,)).fetchall()
    
    return [dict(r) for r in rows]

@app.post("/api/conversations")
async def create_conversation():
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            ("New Conversation",)
        )
        conv_id = cursor.lastrowid
    return {"id": conv_id}

@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    return {"status": "deleted"}

@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    global current_conversation_id, pending_remember
    
    message = request.message.strip()
    conv_id = request.conversation_id
    
    # Create conversation if needed
    if not conv_id:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (title) VALUES (?)",
                (message[:50] + "..." if len(message) > 50 else message,)
            )
            conv_id = cursor.lastrowid
    
    # Save user message
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conv_id, "user", message)
        )
    
    # Handle pending confirmation
    if pending_remember and pending_remember.get("conversation_id") == conv_id:
        response_text, pending_confirmation, classification = handle_confirmation(message)
        if not pending_confirmation:
            pending_remember = None
    else:
        response_text, pending_confirmation, classification = process_message(message, conv_id)
    
    # Save assistant response
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conv_id, "assistant", response_text)
        )
    
    return ChatResponse(
        response=response_text,
        conversation_id=conv_id,
        pending_confirmation=pending_confirmation,
        classification=classification
    )

def handle_confirmation(message: str) -> tuple[str, bool, dict | None]:
    global pending_remember
    
    lower = message.lower()
    
    if lower == "yes":
        result = brain.confirm_remember(
            pending_remember["content"],
            pending_remember["marker"]
        )
        return result["message"], False, None
    
    elif lower == "no":
        return "Cancelled.", False, None
    
    elif message.startswith("[") and message.endswith("]"):
        result = brain.confirm_remember(pending_remember["content"], message)
        return result["message"], False, None
    
    else:
        return "Please type 'yes', 'no', or a specific marker like [D2:DEFINITION]", True, None

def process_message(message: str, conv_id: int) -> tuple[str, bool, dict | None]:
    global pending_remember
    
    # Commands
    if message.startswith("/"):
        return handle_command(message), False, None
    
    # Remember (natural language detection)
    remember_content = extract_remember_content(message)
    if remember_content:
        content = remember_content
        
        if " in [" in content and content.endswith("]"):
            parts = content.rsplit(" in ", 1)
            result = brain.confirm_remember(parts[0], parts[1])
            return result["message"], False, None
        else:
            result = brain.remember(content, confirm=True)
            if result["status"] == "pending_confirmation":
                pending_remember = {
                    "content": result["content"],
                    "marker": result["classification"]["marker"],
                    "conversation_id": conv_id
                }
                return result["message"], True, result["classification"]
            return result["message"], False, None
    
    # Regular query
    return brain.query(message), False, None

def handle_command(message: str) -> str:
    cmd = message.lower().split()
    
    if cmd[0] == "/help":
        return """**Available commands:**
• /index - Re-index the document
• /stats - Show document statistics
• /gaps - Analyze missing content
• /gaps D1 - Analyze gaps in specific domain
• /markers - List all section markers

**Adding content (natural language):**
• "remember [note]"
• "add this: [note]"
• "save [note]"
• "note that [note]"
• "don't forget [note]"
• "make a note of [note]"
• To specify section: "add [note] in [D2:DEFINITION]"

Or just ask questions naturally."""
    
    elif cmd[0] == "/index":
        stats = brain.index_document()
        return f"Re-indexed! {stats['complete_sections']}/{stats['total_sections']} sections have content."
    
    elif cmd[0] == "/stats":
        stats = brain.get_stats()
        lines = [
            f"**Document Statistics**",
            f"Total sections: {stats['total_sections']}",
            f"Complete: {stats['complete_sections']}",
            f"Empty: {stats['empty_sections']}",
            "",
            "**By Domain:**"
        ]
        for d, s in stats['domains'].items():
            lines.append(f"• {d}: {s['complete']}/{s['total']} complete")
        return "\n".join(lines)
    
    elif cmd[0] == "/gaps":
        domain = cmd[1].upper() if len(cmd) > 1 else None
        if domain and domain not in ["D1", "D2", "D3", "D4", "D5", "D6"]:
            return f"Invalid domain: {domain}. Use D1-D6."
        return brain.gaps(domain)
    
    elif cmd[0] == "/markers":
        return brain.list_markers()
    
    return f"Unknown command: {cmd[0]}. Type /help for available commands."

@app.post("/api/reindex")
async def reindex():
    stats = brain.index_document()
    return {"status": "success", "stats": stats}

# Run with: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
