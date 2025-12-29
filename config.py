from pathlib import Path

# === PATHS ===
BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
CHROMA_DIR = BASE_DIR / "chroma_db"

# === GOOGLE DOCS ===
# Find this in your doc URL: https://docs.google.com/document/d/{DOC_ID}/edit
DOC_ID = "YOUR_GOOGLE_DOC_ID_HERE"

# === MODELS ===
LLM_MODEL = "qwen2.5:14b"
EMBEDDING_MODEL = "nomic-embed-text"

# === TEMPLATE MARKERS ===
DOMAINS = {
    "D1": "SOMATIC/INTEROCEPTIVE REGULATION",
    "D2": "AFFECTIVE/EMOTION REGULATION",
    "D3": "COGNITIVE REGULATION/REPETITIVE THOUGHT",
    "D4": "MEANING/COHERENCE/IDENTITY INTEGRATION",
    "D5": "RELATIONAL ATTUNEMENT/MENTALIZATION",
    "D6": "MORAL-EVALUATIVE INTEGRATION",
}

DOMAIN_SECTIONS = [
    "DEFINITION",
    "MECHANISTIC EXPLANATION",
    "ADAPTIVE FUNCTIONING",
    "MALADAPTIVE FUNCTIONING",
    "CLINICAL RELEVANCE",
    "CLINICAL EXAMPLE: MALADAPTIVE",
    "CLINICAL EXAMPLE: ADAPTIVE",
    "CROSS-DOMAIN INTERACTIONS",
    "SUMMARY TABLE",
    "REFERENCES",
]

CONCLUSION_SECTIONS = [
    "ELSA AS INTEGRATED MECHANISTIC ARCHITECTURE",
    "CLINICAL IMPLICATIONS",
    "EVIDENCE GAPS AND FUTURE DIRECTIONS",
    "SUMMARY",
]

# Build all valid markers
def get_all_markers():
    markers = ["[INTRODUCTION]"]
    
    for domain_key in DOMAINS:
        for section in DOMAIN_SECTIONS:
            markers.append(f"[{domain_key}:{section}]")
    
    for section in CONCLUSION_SECTIONS:
        markers.append(f"[CONCLUSION:{section}]")
    
    markers.append("[TABLE 7]")
    
    return markers

ALL_MARKERS = get_all_markers()
