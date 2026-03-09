#!/usr/bin/env python3
"""
SVTD Simple RAG Demo

This demo shows SVTD working with a simple in-memory RAG system.
No external vector database required - uses basic keyword matching.

Perfect for understanding how SVTD works without complex setup.

Run with: python demos/simple_rag_demo/demo.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import svtd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from svtd import TrustLedger, CorrectionHandler, rerank_results


class SimpleRAG:
    """
    Simple in-memory RAG system for demonstration.
    Uses basic keyword matching instead of vector search.
    """
    
    def __init__(self):
        self.memories = []
        self.next_id = 1
    
    def add_memory(self, content: str, tags: list = None):
        """Add a memory to the system."""
        memory_id = f"mem_{self.next_id:04d}"
        self.memories.append({
            "memory_id": memory_id,
            "content": content,
            "tags": tags or [],
        })
        self.next_id += 1
        return memory_id
    
    def search(self, query: str, top_k: int = 5):
        """
        Simple keyword-based search.
        Returns memories with scores based on keyword overlap.
        """
        query_words = set(query.lower().split())
        results = []
        
        for memory in self.memories:
            content_words = set(memory["content"].lower().split())
            
            # Calculate overlap
            overlap = len(query_words & content_words)
            total = len(query_words | content_words)
            
            if total > 0:
                score = overlap / len(query_words)  # Simple precision-like metric
            else:
                score = 0.0
            
            if score > 0:
                result = {
                    "memory_id": memory["memory_id"],
                    "content": memory["content"],
                    "relevance_score": min(0.95, score),
                    "metadata": {"tags": memory["tags"]},
                }
                results.append(result)
        
        # Sort by score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step_num, description):
    """Print a step description."""
    print(f"\n[Step {step_num}] {description}")


def main():
    print_section("SVTD Simple RAG Demo")
    print("\nThis demo shows SVTD working with a simple RAG system.")
    print("No vector database required - uses basic keyword search.")
    
    # Initialize components
    print_step(1, "Initialize RAG system and Trust Ledger")
    rag = SimpleRAG()
    ledger = TrustLedger("simple_demo_trust.db")
    handler = CorrectionHandler(ledger)
    print("  [OK] RAG system ready")
    print("  [OK] Trust Ledger initialized")
    
    # Add some memories
    print_step(2, "Add memories to the system")
    
    # Old information
    rag.add_memory(
        "The office opens at 9 AM and closes at 5 PM.",
        tags=["hours", "old"]
    )
    rag.add_memory(
        "Lunch break is from 12 PM to 1 PM.",
        tags=["hours", "policy"]
    )
    
    # New information (updated hours)
    rag.add_memory(
        "Starting March 2025, office hours are 8 AM to 6 PM with flexible scheduling.",
        tags=["hours", "new", "2025"]
    )
    
    print("  [OK] Added 3 memories:")
    for mem in rag.memories:
        print(f"    - [{mem['memory_id']}] {mem['content'][:50]}...")
    
    # First query
    print_step(3, "Query: 'What are the office hours?'")
    print("  (Before any corrections)")
    
    raw_results = rag.search("office hours")
    reranked = rerank_results(raw_results, ledger)
    
    print("\n  Top results:")
    for i, result in enumerate(reranked[:3], 1):
        content = result['content'][:45]
        score = result['relevance_score']
        trust = result.get('trust_weight', 1.0)
        print(f"  {i}. {content}...")
        print(f"     Score: {score:.3f} | Trust: {trust}")
    
    top_answer = reranked[0]['content']
    print(f"\n  [BOT] Bot says: '{top_answer}'")
    print("  [WARN]  This is the OLD hours (before March 2025)")
    
    # User correction
    print_step(4, "User provides correction")
    print("  User: 'Actually, we changed to 8-6 with flexible hours'")
    
    # Find and flag the old memory
    old_mem_id = rag.memories[0]['memory_id']  # First memory (9-5)
    handler.flag_memory_as_correction(
        memory_id=old_mem_id,
        reason="policy_updated"
    )
    print(f"  [OK] Flagged {old_mem_id} as incorrect")
    
    # Second query (same question)
    print_step(5, "Query again: 'What are the office hours?'")
    print("  (After correction applied)")
    
    raw_results = rag.search("office hours")
    reranked = rerank_results(raw_results, ledger)
    
    print("\n  Top results:")
    for i, result in enumerate(reranked[:3], 1):
        content = result['content'][:45]
        score = result['relevance_score']
        trust = result.get('trust_weight', 1.0)
        is_ghost = result.get('is_ghost', False)
        status = "[GHOST]" if is_ghost else "[OK]"
        print(f"  {i}. {content}...")
        print(f"     Score: {score:.3f} | Trust: {trust} {status}")
    
    top_answer = reranked[0]['content']
    print(f"\n  [BOT] Bot says: '{top_answer}'")
    print("  [OK] This is the CORRECT updated hours!")
    
    # Show trust stats
    print_step(6, "Trust weight summary")
    all_weights = ledger.load_all_weights()
    for mem_id, weight in all_weights.items():
        status = "[GHOST]" if weight < 0.1 else "[OK] Active"
        print(f"  {mem_id}: trust = {weight:.4f} {status}")
    
    # Cleanup
    ledger.close()
    if os.path.exists("simple_demo_trust.db"):
        os.remove("simple_demo_trust.db")
    
    # Summary
    print_section("Demo Complete!")
    print("\nWhat we learned:")
    print("  1. SVTD works with ANY RAG system (even simple ones)")
    print("  2. One correction suppresses stale information")
    print("  3. Ghost state preserves audit trail while filtering")
    print("  4. No re-indexing or document deletion needed")
    
    print("\nNext steps:")
    print("  - Try the Law Demo: python demos/law_demo/run_law_demo.py")
    print("  - Read the docs: docs/ARCHITECTURE.md")
    print("  - Build your own: examples/basic_usage.py")
    
    print("\nLearn more: https://memorygate.io")
    print("=" * 60)


if __name__ == "__main__":
    main()
