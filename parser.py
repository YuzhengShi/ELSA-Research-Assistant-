import re
from dataclasses import dataclass
from config import ALL_MARKERS, DOMAINS

@dataclass
class Section:
    marker: str
    domain: str | None  # D1, D2, etc. or None for intro/conclusion
    section_type: str   # DEFINITION, MECHANISTIC EXPLANATION, etc.
    content: str
    
    def __str__(self):
        return f"{self.marker}\n{self.content[:100]}..."

def parse_document(text: str, markers: list[str] = ALL_MARKERS) -> list[Section]:
    """Parse document into sections based on markers."""
    sections = []
    
    # Build regex pattern to split on markers
    # Escape brackets for regex
    escaped_markers = [re.escape(m) for m in markers]
    pattern = f"({'|'.join(escaped_markers)})"
    
    # Split and keep delimiters
    parts = re.split(pattern, text)
    
    # Process parts: marker followed by content
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        
        if part in markers:
            marker = part
            content = parts[i + 1] if i + 1 < len(parts) else ""
            content = content.strip()
            
            # Parse marker to extract domain and section type
            domain, section_type = parse_marker(marker)
            
            sections.append(Section(
                marker=marker,
                domain=domain,
                section_type=section_type,
                content=content
            ))
            i += 2
        else:
            i += 1
    
    return sections

def parse_marker(marker: str) -> tuple[str | None, str]:
    """Extract domain and section type from marker.
    
    Examples:
        [D1:DEFINITION] -> ("D1", "DEFINITION")
        [INTRODUCTION] -> (None, "INTRODUCTION")
        [CONCLUSION:SUMMARY] -> (None, "CONCLUSION:SUMMARY")
    """
    # Remove brackets
    inner = marker[1:-1]
    
    # Check if it's a domain marker (D1:, D2:, etc.)
    for domain_key in DOMAINS:
        if inner.startswith(f"{domain_key}:"):
            section_type = inner[len(domain_key) + 1:]
            return (domain_key, section_type)
    
    # Not a domain marker
    return (None, inner)

def get_section_by_marker(sections: list[Section], marker: str) -> Section | None:
    """Find a specific section by its marker."""
    for section in sections:
        if section.marker == marker:
            return section
    return None

def get_sections_by_domain(sections: list[Section], domain: str) -> list[Section]:
    """Get all sections for a specific domain (e.g., 'D1')."""
    return [s for s in sections if s.domain == domain]

def get_empty_sections(sections: list[Section]) -> list[Section]:
    """Find sections with no content (for gap analysis)."""
    return [s for s in sections if not s.content or len(s.content) < 10]

def get_document_stats(sections: list[Section]) -> dict:
    """Get overview statistics of document completeness."""
    total = len(sections)
    empty = len(get_empty_sections(sections))
    
    domain_stats = {}
    for domain_key in DOMAINS:
        domain_sections = get_sections_by_domain(sections, domain_key)
        domain_empty = [s for s in domain_sections if not s.content or len(s.content) < 10]
        domain_stats[domain_key] = {
            "total": len(domain_sections),
            "empty": len(domain_empty),
            "complete": len(domain_sections) - len(domain_empty)
        }
    
    return {
        "total_sections": total,
        "empty_sections": empty,
        "complete_sections": total - empty,
        "domains": domain_stats
    }


# Test
if __name__ == "__main__":
    # Sample test
    sample = """
    [INTRODUCTION]
    This is the introduction to ELSA framework.
    
    [D1:DEFINITION]
    Domain 1 focuses on somatic regulation.
    
    [D1:MECHANISTIC EXPLANATION]
    The mechanism involves interoceptive processing.
    
    [D1:ADAPTIVE FUNCTIONING]
    
    [D2:DEFINITION]
    Domain 2 covers emotion regulation.
    """
    
    sections = parse_document(sample)
    for s in sections:
        print(f"{s.marker} -> Domain: {s.domain}, Type: {s.section_type}")
        print(f"  Content: {s.content[:50] if s.content else '(empty)'}...")
        print()
    
    print("Empty sections:", [s.marker for s in get_empty_sections(sections)])
