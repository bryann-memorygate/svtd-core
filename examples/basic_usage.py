#!/usr/bin/env python3
"""
SVTD Basic Usage Example

This example shows the simplest way to integrate SVTD into your RAG pipeline.
Run with: python examples/basic_usage.py
"""

from svtd import TrustLedger, CorrectionHandler, rerank_results


def main():
    print("=" * 60)
    print("SVTD Basic Usage Example")
    print("=" * 60)
    
    # Step 1: Initialize the Trust Ledger
    print("\n[1] Initializing Trust Ledger...")
    ledger = TrustLedger("demo_trust.db")
    handler = CorrectionHandler(ledger)
    print("    [OK] Trust Ledger ready")
    
    # Step 2: Simulate RAG results
    print("\n[2] Simulating RAG retrieval...")
    rag_results = [
        {
            "memory_id": "policy_2024",
            "content": "Vacation policy: 15 days per year",
            "relevance_score": 0.92,
        },
        {
            "memory_id": "policy_2025",
            "content": "Vacation policy: 20 days per year",
            "relevance_score": 0.85,
        },
        {
            "memory_id": "policy_2023",
            "content": "Vacation policy: 10 days per year",
            "relevance_score": 0.65,
        },
    ]
    
    print("    Retrieved documents:")
    for i, doc in enumerate(rag_results, 1):
        print(f"    {i}. [{doc['memory_id']}] {doc['content']}")
        print(f"       Relevance: {doc['relevance_score']:.2f}")
    
    # Step 3: First query (before correction)
    print("\n[3] Query: 'How many vacation days do I have?'")
    initial_results = rerank_results(rag_results.copy(), ledger)
    print(f"    Answer: '{initial_results[0]['content']}'")
    print(f"    Source: {initial_results[0]['memory_id']}")
    print("    ⚠️  WRONG! This is the old policy.")
    
    # Step 4: User correction
    print("\n[4] User correction:")
    print("    User: 'No, we updated to 20 days in 2025'")
    handler.flag_memory_as_correction(
        memory_id="policy_2024",
        client_id="user_1",
        reason="user_correction"
    )
    print("    ✓ Applied trust decay to policy_2024")
    
    # Step 5: Second query (after correction)
    print("\n[5] Same query after correction:")
    corrected_results = rerank_results(rag_results.copy(), ledger)
    print(f"    Answer: '{corrected_results[0]['content']}'")
    print(f"    Source: {corrected_results[0]['memory_id']}")
    print("    ✓ CORRECT! Now returns the updated policy.")
    
    # Show the trust weights
    print("\n[6] Trust weights after correction:")
    for result in corrected_results:
        mem_id = result['memory_id']
        trust = result.get('trust_weight', 1.0)
        is_ghost = result.get('is_ghost', False)
        status = "👻 GHOST" if is_ghost else "✅ ACTIVE"
        print(f"    {mem_id}: trust={trust:.4f} {status}")
    
    # Cleanup
    ledger.close()
    import os
    if os.path.exists("demo_trust.db"):
        os.remove("demo_trust.db")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nKey takeaway:")
    print("  SVTD automatically suppresses stale information")
    print("  after a single user correction.")
    print("\nLearn more: https://memorygate.io")


if __name__ == "__main__":
    main()
