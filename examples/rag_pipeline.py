#!/usr/bin/env python3
"""
SVTD Custom RAG Pipeline Example

This example shows how to build a complete RAG pipeline with SVTD integration.
Run with: python examples/rag_pipeline.py
"""

import json
import os
from typing import List, Dict, Any, Optional
from svtd import TrustLedger, CorrectionHandler, rerank_results


class SVTDRAGPipeline:
    """
    Complete RAG pipeline with SVTD trust weighting.
    
    This demonstrates how to integrate SVTD into a custom RAG implementation.
    """
    
    def __init__(
        self,
        memory_file_path: str = "memories.jsonl",
        trust_db_path: str = "trust.db",
        min_relevance_threshold: float = 0.5
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            memory_file_path: Path to JSONL file storing memories
            trust_db_path: Path to SQLite database for trust weights
            min_relevance_threshold: Minimum relevance score to include results
        """
        self.memory_file_path = memory_file_path
        self.ledger = TrustLedger(trust_db_path)
        self.handler = CorrectionHandler(self.ledger)
        self.min_relevance_threshold = min_relevance_threshold
        self.client_id = "default"
        
        # Load memories
        self.memories = self._load_memories()
        print(f"[RAG] Loaded {len(self.memories)} memories")
    
    def _load_memories(self) -> List[Dict[str, Any]]:
        """Load memories from JSONL file."""
        if not os.path.exists(self.memory_file_path):
            return []
        
        memories = []
        with open(self.memory_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    memories.append(json.loads(line))
        return memories
    
    def _save_memories(self):
        """Save memories to JSONL file."""
        with open(self.memory_file_path, 'w') as f:
            for memory in self.memories:
                f.write(json.dumps(memory) + '\n')
    
    def _simple_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search (in production, use vector DB).
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of memory dicts with relevance scores
        """
        query_terms = query.lower().split()
        scored_memories = []
        
        for memory in self.memories:
            content = memory.get('content', '').lower()
            # Simple scoring: count matching terms
            score = sum(1 for term in query_terms if term in content)
            # Normalize to 0-1 range (rough approximation)
            if score > 0:
                normalized_score = min(0.95, 0.5 + (score * 0.1))
            else:
                normalized_score = 0.0
            
            result = {
                "memory_id": memory.get('id'),
                "content": memory.get('content'),
                "relevance_score": normalized_score,
                "metadata": memory.get('metadata', {}),
            }
            scored_memories.append(result)
        
        # Sort by score
        scored_memories.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_memories[:top_k]
    
    def query(self, query_str: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Execute a RAG query with trust-weighted reranking.
        
        Args:
            query_str: The query string
            top_k: Number of results to return
            
        Returns:
            List of results with trust-weighted scores
        """
        # Step 1: Retrieve
        raw_results = self._simple_search(query_str, top_k=top_k * 2)
        
        # Step 2: Rerank with SVTD
        reranked = rerank_results(
            raw_results,
            self.ledger,
            self.client_id
        )
        
        # Step 3: Filter by threshold
        filtered = [
            r for r in reranked
            if r['relevance_score'] >= self.min_relevance_threshold
        ]
        
        return filtered[:top_k]
    
    def add_memory(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a new memory to the system.
        
        Args:
            content: Memory content
            metadata: Optional metadata
            
        Returns:
            ID of the new memory
        """
        memory_id = f"mem_{len(self.memories):04d}"
        memory = {
            'id': memory_id,
            'content': content,
            'metadata': metadata or {},
        }
        self.memories.append(memory)
        self._save_memories()
        return memory_id
    
    def flag_as_incorrect(self, memory_id: str, reason: str = "user_flagged"):
        """
        Flag a memory as incorrect.
        
        Args:
            memory_id: ID of the memory to flag
            reason: Reason for flagging
        """
        self.handler.flag_memory_as_correction(
            memory_id=memory_id,
            client_id=self.client_id,
            reason=reason
        )
        print(f"[RAG] Flagged {memory_id} as incorrect (reason: {reason})")
    
    def get_trust_stats(self) -> Dict[str, Any]:
        """Get statistics about trust weights."""
        all_weights = self.ledger.load_all_weights(self.client_id)
        
        if not all_weights:
            return {"total": 0, "cold": 0, "avg_trust": 1.0}
        
        cold_count = sum(1 for w in all_weights.values() if w < 0.2)
        avg_trust = sum(all_weights.values()) / len(all_weights)
        
        return {
            "total": len(all_weights),
            "cold": cold_count,
            "active": len(all_weights) - cold_count,
            "avg_trust": round(avg_trust, 4),
        }
    
    def close(self):
        """Clean up resources."""
        self.ledger.close()


def main():
    print("=" * 60)
    print("SVTD Custom RAG Pipeline Example")
    print("=" * 60)
    
    # Initialize pipeline
    print("\n[1] Initializing RAG pipeline...")
    pipeline = SVTDRAGPipeline(
        memory_file_path="demo_memories.jsonl",
        trust_db_path="demo_trust.db"
    )
    
    # Add some memories
    print("\n[2] Adding memories to the system...")
    pipeline.add_memory(
        "The company headquarters is in New York City.",
        {"category": "location", "date": "2024-01-15"}
    )
    pipeline.add_memory(
        "The company headquarters moved to San Francisco in March 2025.",
        {"category": "location", "date": "2025-03-01"}
    )
    pipeline.add_memory(
        "Office hours are 9 AM to 5 PM Eastern Time.",
        {"category": "policy", "date": "2024-01-15"}
    )
    print("    [OK] Added 3 memories")
    
    # First query
    print("\n[3] Query: 'Where is the company headquarters?'")
    results = pipeline.query("company headquarters location", top_k=3)
    print("\n    Results (before correction):")
    for i, result in enumerate(results, 1):
        print(f"    {i}. {result['content']}")
        print(f"       Trust: {result.get('trust_weight', 1.0):.4f}")
    
    # User correction
    print("\n[4] User provides correction:")
    print("    'Actually, we moved to San Francisco'")
    # Find and flag the NYC memory
    for mem in pipeline.memories:
        if "New York" in mem['content']:
            pipeline.flag_as_incorrect(mem['id'], "location_changed")
    
    # Second query
    print("\n[5] Same query after correction:")
    results = pipeline.query("company headquarters location", top_k=3)
    print("\n    Results (after correction):")
    for i, result in enumerate(results, 1):
        trust = result.get('trust_weight', 1.0)
        is_ghost = result.get('is_ghost', False)
        status = "[GHOST]" if is_ghost else "[OK] ACTIVE"
        print(f"    {i}. {result['content']}")
        print(f"       Trust: {trust:.4f} {status}")
    
    # Show stats
    print("\n[6] Trust statistics:")
    stats = pipeline.get_trust_stats()
    print(f"    Total tracked: {stats['total']}")
    print(f"    Cold memories: {stats['cold']}")
    print(f"    Average trust: {stats['avg_trust']}")
    
    # Cleanup
    pipeline.close()
    
    # Remove demo files
    for f in ["demo_memories.jsonl", "demo_trust.db"]:
        if os.path.exists(f):
            os.remove(f)
    
    print("\n" + "=" * 60)
    print("Pipeline demonstration complete!")
    print("=" * 60)
    print("\nThis example shows:")
    print("  [OK] Adding memories to a RAG system")
    print("  [OK] Retrieving with semantic search")
    print("  [OK] Reranking with SVTD trust weights")
    print("  [OK] Handling user corrections")
    print("  [OK] Automatic suppression of stale info")
    print("\nLearn more: https://memorygate.io/docs/custom-rag")


if __name__ == "__main__":
    main()
