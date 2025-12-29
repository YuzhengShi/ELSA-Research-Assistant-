import ollama
from config import EMBEDDING_MODEL
from parser import Section

def get_embedding(text: str) -> list[float]:
    """Generate embedding for a piece of text."""
    response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return response["embedding"]

def prepare_chunk_text(section: Section) -> str:
    """Prepare section for embedding with metadata prefix.
    
    Adding marker/domain info helps retrieval accuracy.
    """
    domain_info = f"Domain: {section.domain}" if section.domain else ""
    
    return f"""
{section.marker}
{domain_info}
Section: {section.section_type}

{section.content}
""".strip()

def embed_sections(sections: list[Section]) -> list[dict]:
    """Generate embeddings for all sections.
    
    Returns list of dicts with:
        - id: unique identifier
        - embedding: vector
        - metadata: marker, domain, section_type
        - document: original text
    """
    results = []
    
    for i, section in enumerate(sections):
        # Skip empty sections (nothing to embed)
        if not section.content or len(section.content.strip()) < 10:
            continue
        
        chunk_text = prepare_chunk_text(section)
        embedding = get_embedding(chunk_text)
        
        results.append({
            "id": f"section_{i}_{section.marker}",
            "embedding": embedding,
            "metadata": {
                "marker": section.marker,
                "domain": section.domain or "none",
                "section_type": section.section_type,
            },
            "document": chunk_text
        })
        
        print(f"Embedded: {section.marker}")
    
    return results


# Test
if __name__ == "__main__":
    # Quick test of embedding
    test_text = "This is a test of the embedding model."
    emb = get_embedding(test_text)
    print(f"Embedding dimension: {len(emb)}")
    print(f"First 5 values: {emb[:5]}")
