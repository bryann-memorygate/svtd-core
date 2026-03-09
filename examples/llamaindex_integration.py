#!/usr/bin/env python3
"""
SVTD LlamaIndex Integration Example

This example shows how to integrate SVTD with LlamaIndex's retrieval pipeline.
Run with: python examples/llamaindex_integration.py

Requirements:
    pip install llama-index
"""

from typing import List
from svtd import TrustLedger, CorrectionHandler, rerank_results


# Mock LlamaIndex components for the example
class MockTextNode:
    """Mock LlamaIndex TextNode."""
    def __init__(self, id_: str, text: str, score: float = 0.8):
        self.id_ = id_
        self.text = text
        self.score = score
        self.metadata = {}


class SVTDReranker:
    """
    Custom reranker for LlamaIndex that adds SVTD trust weighting.
    
    Usage:
        reranker = SVTDReranker()
        nodes = reranker.postprocess_nodes(nodes, query_str="...")
    """
    
    def __init__(self, trust_db_path: str = "svtd_llamaindex.db", top_n: int = 5):
        """
        Initialize SVTD reranker.
        
        Args:
            trust_db_path: Path to SQLite database for trust weights
            top_n: Number of top nodes to return after reranking
        """
        self.ledger = TrustLedger(trust_db_path)
        self.handler = CorrectionHandler(self.ledger)
        self.top_n = top_n
        self.client_id = "default"
    
    def postprocess_nodes(
        self,
        nodes: List[MockTextNode],
        query_str: str = ""
    ) -> List[MockTextNode]:
        """
        Rerank nodes using SVTD trust weights.
        
        Args:
            nodes: List of nodes from retriever
            query_str: Query string (unused but required for interface)
            
        Returns:
            Reranked list of nodes
        """
        # Convert to SVTD format
        svtd_results = []
        for node in nodes:
            result = {
                "memory_id": node.id_,
                "content": node.text,
                "relevance_score": node.score,
                "_original_node": node,
            }
            svtd_results.append(result)
        
        # Apply SVTD reranking
        reranked = rerank_results(svtd_results, self.ledger, self.client_id)
        
        # Convert back to nodes with trust metadata
        output_nodes = []
        for result in reranked[:self.top_n]:
            node = result["_original_node"]
            node.metadata["trust_weight"] = result.get("trust_weight", 1.0)
            node.metadata["is_ghost"] = result.get("is_ghost", False)
            node.score = result["relevance_score"]  # Update score to trust-weighted
            output_nodes.append(node)
        
        return output_nodes
    
    def flag_node_as_incorrect(self, node_id: str, reason: str = "user_flagged"):
        """
        Flag a node as incorrect.
        
        Args:
            node_id: ID of the node to flag
            reason: Reason for flagging
        """
        self.handler.flag_memory_as_correction(
            memory_id=node_id,
            client_id=self.client_id,
            reason=reason
        )
        print(f"Flagged node {node_id} as incorrect")
    
    def close(self):
        """Clean up resources."""
        self.ledger.close()


def main():
    print("=" * 60)
    print("SVTD LlamaIndex Integration Example")
    print("=" * 60)
    
    # Setup: Create some mock nodes
    nodes = [
        MockTextNode(
            id_="doc_001",
            text="Python 2.7 is the recommended version for new projects.",
            score=0.92
        ),
        MockTextNode(
            id_="doc_002",
            text="Python 3.11 is the current recommended version.",
            score=0.85
        ),
        MockTextNode(
            id_="doc_003",
            text="Python was first released in 1991.",
            score=0.75
        ),
    ]
    
    # Create SVTD reranker
    print("\n[1] Creating SVTD reranker...")
    reranker = SVTDReranker(trust_db_path="llamaindex_demo.db", top_n=3)
    print("    [OK] SVTD reranker ready")
    
    # First query
    print("\n[2] Query: 'Which Python version should I use?'")
    reranked = reranker.postprocess_nodes(nodes, query_str="python version")
    print("\n    Results (before correction):")
    for i, node in enumerate(reranked, 1):
        print(f"    {i}. {node.text}")
        print(f"       ID: {node.id_}, Score: {node.score:.2f}")
    
    # User correction
    print("\n[3] User provides correction:")
    print("    'The doc about Python 2.7 is completely outdated'")
    reranker.flag_node_as_incorrect("doc_001", "outdated_information")
    
    # Second query (same nodes, but trust weights changed)
    print("\n[4] Same query after correction:")
    reranked = reranker.postprocess_nodes(nodes, query_str="python version")
    print("\n    Results (after correction):")
    for i, node in enumerate(reranked, 1):
        trust = node.metadata.get('trust_weight', 1.0)
        is_ghost = node.metadata.get('is_ghost', False)
        status = "[GHOST]" if is_ghost else "[OK] ACTIVE"
        print(f"    {i}. {node.text}")
        print(f"       ID: {node.id_}, Trust: {trust} {status}")
    
    # Cleanup
    reranker.close()
    import os
    if os.path.exists("llamaindex_demo.db"):
        os.remove("llamaindex_demo.db")
    
    print("\n" + "=" * 60)
    print("Integration complete!")
    print("=" * 60)
    print("\nTo use with real LlamaIndex:")
    print("  1. Install: pip install llama-index")
    print("  2. Import: from llama_index.core.postprocessor import BaseNodePostprocessor")
    print("  3. Extend BaseNodePostprocessor with SVTD logic")
    print("  4. Add to your query engine: node_postprocessors=[svtd_reranker]")
    print("\nLearn more: https://memorygate.io/docs/llamaindex")


if __name__ == "__main__":
    main()
