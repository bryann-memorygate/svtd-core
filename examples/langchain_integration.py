#!/usr/bin/env python3
"""
SVTD LangChain Integration Example

This example shows how to integrate SVTD with LangChain's retrieval pipeline.
Run with: python examples/langchain_integration.py

Requirements:
    pip install langchain langchain-community
"""

from typing import List, Dict, Any
from svtd import TrustLedger, CorrectionHandler, rerank_results

# Mock LangChain components for the example
class MockDocument:
    """Mock LangChain Document."""
    def __init__(self, page_content: str, metadata: Dict[str, Any]):
        self.page_content = page_content
        self.metadata = metadata


class SVTDRetriever:
    """
    Custom retriever that adds SVTD trust weighting to LangChain.
    
    This wraps any existing LangChain retriever and adds trust-weighted
    reranking on top of the retrieved results.
    """
    
    def __init__(self, base_retriever, trust_db_path: str = "svtd_trust.db"):
        """
        Initialize SVTD retriever.
        
        Args:
            base_retriever: The underlying LangChain retriever
            trust_db_path: Path to SQLite database for trust weights
        """
        self.base_retriever = base_retriever
        self.ledger = TrustLedger(trust_db_path)
        self.handler = CorrectionHandler(self.ledger)
        self.client_id = "default"
    
    def get_relevant_documents(self, query: str) -> List[MockDocument]:
        """
        Retrieve documents with trust-weighted reranking.
        
        Args:
            query: The search query
            
        Returns:
            List of documents reranked by trust-weighted relevance
        """
        # Step 1: Get documents from base retriever
        docs = self.base_retriever.get_relevant_documents(query)
        
        # Step 2: Convert to SVTD format
        svtd_results = []
        for i, doc in enumerate(docs):
            result = {
                "memory_id": doc.metadata.get("id", f"doc_{i}"),
                "content": doc.page_content,
                "relevance_score": doc.metadata.get("score", 0.8),
                "metadata": doc.metadata,
                "_original_doc": doc,  # Keep reference for reconstruction
            }
            svtd_results.append(result)
        
        # Step 3: Apply SVTD reranking
        reranked = rerank_results(svtd_results, self.ledger, self.client_id)
        
        # Step 4: Convert back to LangChain documents
        output_docs = []
        for result in reranked:
            doc = result["_original_doc"]
            # Add trust metadata
            doc.metadata["trust_weight"] = result.get("trust_weight", 1.0)
            doc.metadata["is_ghost"] = result.get("is_ghost", False)
            output_docs.append(doc)
        
        return output_docs
    
    def flag_as_incorrect(self, document_id: str, reason: str = "user_flagged"):
        """
        Flag a document as incorrect, triggering trust decay.
        
        Args:
            document_id: ID of the document to flag
            reason: Reason for flagging
        """
        self.handler.flag_memory_as_correction(
            memory_id=document_id,
            client_id=self.client_id,
            reason=reason
        )
        print(f"Flagged {document_id} as incorrect (reason: {reason})")
    
    def close(self):
        """Clean up resources."""
        self.ledger.close()


class MockBaseRetriever:
    """Mock base retriever for demonstration."""
    
    def __init__(self, documents: List[MockDocument]):
        self.documents = documents
    
    def get_relevant_documents(self, query: str) -> List[MockDocument]:
        """Simple mock retrieval - returns all documents."""
        return self.documents


def main():
    print("=" * 60)
    print("SVTD LangChain Integration Example")
    print("=" * 60)
    
    # Setup: Create some mock documents
    documents = [
        MockDocument(
            page_content="The company offers 15 days of vacation annually.",
            metadata={"id": "handbook_2024", "score": 0.95, "source": "handbook.pdf"}
        ),
        MockDocument(
            page_content="Effective 2025: Vacation days increased to 20 annually.",
            metadata={"id": "policy_update_2025", "score": 0.82, "source": "update.pdf"}
        ),
    ]
    
    # Create base retriever
    base_retriever = MockBaseRetriever(documents)
    
    # Wrap with SVTD
    print("\n[1] Creating SVTD-wrapped retriever...")
    svtd_retriever = SVTDRetriever(base_retriever, trust_db_path="langchain_demo.db")
    print("    [OK] SVTD retriever ready")
    
    # First query
    print("\n[2] Query: 'How many vacation days do we have?'")
    results = svtd_retriever.get_relevant_documents("vacation days")
    print("\n    Results (before correction):")
    for i, doc in enumerate(results, 1):
        print(f"    {i}. {doc.page_content}")
        print(f"       Source: {doc.metadata['id']}, Trust: {doc.metadata.get('trust_weight', 1.0)}")
    
    # User correction
    print("\n[3] User provides correction:")
    print("    'Actually, the 2024 handbook is outdated'")
    svtd_retriever.flag_as_incorrect("handbook_2024", "outdated_information")
    
    # Second query (same query)
    print("\n[4] Same query after correction:")
    results = svtd_retriever.get_relevant_documents("vacation days")
    print("\n    Results (after correction):")
    for i, doc in enumerate(results, 1):
        trust = doc.metadata.get('trust_weight', 1.0)
        is_ghost = doc.metadata.get('is_ghost', False)
        status = "[GHOST]" if is_ghost else "[OK] ACTIVE"
        print(f"    {i}. {doc.page_content}")
        print(f"       Source: {doc.metadata['id']}, Trust: {trust} {status}")
    
    # Cleanup
    svtd_retriever.close()
    import os
    if os.path.exists("langchain_demo.db"):
        os.remove("langchain_demo.db")
    
    print("\n" + "=" * 60)
    print("Integration complete!")
    print("=" * 60)
    print("\nTo use with real LangChain:")
    print("  1. Install: pip install langchain")
    print("  2. Replace MockBaseRetriever with your actual retriever")
    print("  3. Use SVTDRetriever to wrap it")
    print("\nLearn more: https://memorygate.io/docs/langchain")


if __name__ == "__main__":
    main()
