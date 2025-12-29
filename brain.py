from docs_client import DocsClient
from parser import parse_document, get_empty_sections, get_document_stats, Section
from embeddings import embed_sections
from vector_store import VectorStore
from llm import chat, classify_section, analyze_gaps
from config import DOC_ID, ALL_MARKERS, DOMAINS

class SecondBrain:
    def __init__(self):
        print("Initializing Second Brain...")
        self.docs = DocsClient()
        self.store = VectorStore()
        self.sections: list[Section] = []
        self.conversation_history = []
        
    def index_document(self):
        """Load document, parse sections, and build vector index."""
        print("Fetching document from Google Docs...")
        text = self.docs.read_document(DOC_ID)
        
        print("Parsing sections...")
        self.sections = parse_document(text)
        print(f"Found {len(self.sections)} sections")
        
        print("Building vector index (this may take a minute)...")
        self.store.clear()
        embedded = embed_sections(self.sections)
        self.store.add_documents(embedded)
        
        print(f"Indexed {self.store.count()} sections")
        return self.get_stats()
    
    def get_stats(self) -> dict:
        """Get document completion statistics."""
        return get_document_stats(self.sections)
    
    def query(self, question: str, n_results: int = 5) -> str:
        """Answer a question using document content."""
        # Search for relevant sections
        results = self.store.search(question, n_results=n_results)
        
        if not results:
            return "No relevant sections found. Try rephrasing your question."
        
        # Build context from search results
        context_parts = []
        for r in results:
            context_parts.append(f"[{r['metadata']['marker']}]\n{r['document']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Get LLM response
        response = chat(question, context=context, history=self.conversation_history)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return response
    
    def remember(self, content: str, confirm: bool = True) -> dict:
        """Classify content and optionally add to document.
        
        Args:
            content: The note/information to add
            confirm: If True, return classification for user confirmation
                     If False, directly append to document
        
        Returns:
            {
                "status": "pending_confirmation" | "added" | "error",
                "classification": {...},
                "message": "..."
            }
        """
        # Classify the content
        classification = classify_section(content)
        
        if not classification.get("marker"):
            return {
                "status": "error",
                "classification": classification,
                "message": "Could not determine appropriate section."
            }
        
        if confirm:
            return {
                "status": "pending_confirmation",
                "classification": classification,
                "content": content,
                "message": f"I'll add this to {classification['marker']}.\n"
                          f"Reasoning: {classification.get('reasoning', 'N/A')}\n"
                          f"Confidence: {classification.get('confidence', 'N/A')}\n\n"
                          f"Type 'yes' to confirm, 'no' to cancel, or specify a different marker."
            }
        
        # Add to document
        return self._append_to_doc(content, classification["marker"])
    
    def confirm_remember(self, content: str, marker: str) -> dict:
        """Confirm and execute adding content to a specific section."""
        if marker not in ALL_MARKERS:
            return {
                "status": "error",
                "message": f"Invalid marker: {marker}\nValid markers: {ALL_MARKERS}"
            }
        
        return self._append_to_doc(content, marker)
    
    def _append_to_doc(self, content: str, marker: str) -> dict:
        """Internal: append content to document section."""
        try:
            success = self.docs.append_to_section(DOC_ID, marker, content, ALL_MARKERS)
            
            if success:
                # Re-index just this section (optimization: could update single chunk)
                # For now, we'll do a full re-index on next query
                return {
                    "status": "added",
                    "marker": marker,
                    "message": f"Added content to {marker}. Run 'reindex' to update search."
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to add content. Marker {marker} not found in document."
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error writing to document: {str(e)}"
            }
    
    def gaps(self, domain: str = None) -> str:
        """Analyze gaps in the document.
        
        Args:
            domain: Optional specific domain (D1-D6) to analyze
        """
        stats = self.get_stats()
        empty = get_empty_sections(self.sections)
        
        if domain:
            empty = [s for s in empty if s.domain == domain]
        
        if not empty:
            target = f"Domain {domain}" if domain else "document"
            return f"No empty sections found in {target}. All sections have content."
        
        # Build summary for LLM
        summary_parts = ["Document Status:"]
        summary_parts.append(f"Total sections: {stats['total_sections']}")
        summary_parts.append(f"Complete: {stats['complete_sections']}")
        summary_parts.append(f"Empty: {stats['empty_sections']}")
        summary_parts.append("\nEmpty sections:")
        
        for section in empty:
            domain_name = DOMAINS.get(section.domain, "General")
            summary_parts.append(f"- {section.marker} ({domain_name})")
        
        summary = "\n".join(summary_parts)
        
        return analyze_gaps(summary)
    
    def list_markers(self) -> str:
        """List all valid markers."""
        output = ["Available markers:\n"]
        
        output.append("[INTRODUCTION]")
        
        for domain_key, domain_name in DOMAINS.items():
            output.append(f"\n=== {domain_key}: {domain_name} ===")
            for marker in ALL_MARKERS:
                if marker.startswith(f"[{domain_key}:"):
                    output.append(f"  {marker}")
        
        output.append("\n=== CONCLUSION ===")
        for marker in ALL_MARKERS:
            if marker.startswith("[CONCLUSION:"):
                output.append(f"  {marker}")
        
        output.append("\n[TABLE 7]")
        
        return "\n".join(output)


# Test
if __name__ == "__main__":
    brain = SecondBrain()
    print("\nDocument stats:")
    stats = brain.index_document()
    print(stats)
