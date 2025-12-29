import chromadb
from chromadb.config import Settings
from config import CHROMA_DIR, EMBEDDING_MODEL
from embeddings import get_embedding

class VectorStore:
    def __init__(self, collection_name: str = "elsa_docs"):
        # Persistent storage
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def clear(self):
        """Clear all documents from collection."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, embedded_sections: list[dict]):
        """Add embedded sections to the store."""
        if not embedded_sections:
            return
        
        self.collection.add(
            ids=[s["id"] for s in embedded_sections],
            embeddings=[s["embedding"] for s in embedded_sections],
            metadatas=[s["metadata"] for s in embedded_sections],
            documents=[s["document"] for s in embedded_sections]
        )
        print(f"Added {len(embedded_sections)} sections to vector store")
    
    def search(self, query: str, n_results: int = 5, domain_filter: str = None) -> list[dict]:
        """Search for relevant sections.
        
        Args:
            query: Natural language query
            n_results: Number of results to return
            domain_filter: Optional filter by domain (e.g., "D1")
        
        Returns:
            List of matching sections with scores
        """
        query_embedding = get_embedding(query)
        
        where_filter = None
        if domain_filter:
            where_filter = {"domain": domain_filter}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],  # Lower = more similar
            })
        
        return formatted
    
    def get_all_documents(self) -> list[dict]:
        """Retrieve all documents (for debugging/overview)."""
        results = self.collection.get(include=["documents", "metadatas"])
        
        formatted = []
        for i in range(len(results["ids"])):
            formatted.append({
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i],
            })
        
        return formatted
    
    def count(self) -> int:
        """Return number of documents in store."""
        return self.collection.count()


# Test
if __name__ == "__main__":
    store = VectorStore()
    print(f"Documents in store: {store.count()}")
    
    # Test search if there are documents
    if store.count() > 0:
        results = store.search("emotion regulation")
        for r in results:
            print(f"\n{r['metadata']['marker']} (distance: {r['distance']:.3f})")
            print(r['document'][:200])
