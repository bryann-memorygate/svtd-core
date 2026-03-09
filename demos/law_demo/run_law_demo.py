# Copyright 2026 The SVTD Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SVTD Law Demo - Side-by-side comparison of Vanilla RAG vs. SVTD.
Shows how SVTD correctly handles stale legal information after a correction.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to sys.path to import svtd package
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from svtd import TrustLedger, rerank_results, CorrectionHandler

# Constants
CORPUS_PATH = Path(__file__).resolve().parent / "corpus.json"
DB_PATH = "law_demo_trust.db"
CLIENT_ID = "law_firm_demo"

DEMO_QUERY = (
    "Under the Fair Labor Standards Act EAP exemption, what is the current "
    "standard weekly salary level required, and what is the highly compensated "
    "employee annual threshold? Provide citations."
)

def mock_search(query, corpus):
    """
    Simulates a vector search engine returning results with relevance scores.
    In this demo, we'll assign scores manually to simulate 'semantic' matching
    where the stale rule looks more relevant than the vacatur order because it
    contains more keywords matching the query.
    """
    results = []
    for item in corpus:
        # Simulate relevance scores where stale rule looks 'better' to vanilla RAG
        # because it explicitly lists the levels the query asks for ($844/$1128)
        if item["memory_id"] == "flsa_rule_2024_1":
            score = 0.95
        elif item["memory_id"] == "flsa_ecfr_1":
            score = 0.92
        elif item["memory_id"] == "flsa_vacatur_1":
            score = 0.85
        elif item["memory_id"] == "flsa_dol_enforcement_1":
            score = 0.82
        else:
            score = 0.5
            
        results.append({
            "memory_id": item["memory_id"],
            "content": item["content"],
            "relevance_score": score,
            "metadata": item.get("metadata", {})
        })
    
    # Sort by relevance score descending
    return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

def main():
    print("=" * 80)
    print(" SVTD LAW DEMO: FLSA Overtime Exemption ($844/$1128 vs $684)")
    print("=" * 80)
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    ledger = TrustLedger(DB_PATH)
    handler = CorrectionHandler(ledger)
    
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
        
    print(f"\n[QUERY]: {DEMO_QUERY}")
    
    # --- PHASE 1: VANILLA RAG ---
    print("\n" + "-" * 40)
    print(" PHASE 1: Vanilla RAG (Before Correction)")
    print("-" * 40)
    
    vanilla_results = mock_search(DEMO_QUERY, corpus)
    for i, res in enumerate(vanilla_results[:3], 1):
        status = res["metadata"].get("status", "unknown")
        print(f"{i}. [{res['memory_id']}] Score: {res['relevance_score']:.3f} | Status: {status}")
        print(f"   Content: {res['content'][:120]}...")
        
    top_vanilla = vanilla_results[0]
    if "844" in top_vanilla["content"] or "1,128" in top_vanilla["content"]:
        print("\n[FAIL] RESULT: RAG returned the STALE rule ($844/$1128).")
    else:
        print("\n[PASS] RESULT: RAG returned the CONTROLLING rule.")

    # --- PHASE 2: APPLY CORRECTION ---
    print("\n" + "-" * 40)
    print(" PHASE 2: Applying SVTD Correction")
    print("-" * 40)
    
    print("User Action: Flagging stale rule 'flsa_rule_2024_1' as incorrect.")
    handler.flag_memory_as_correction(memory_id="flsa_rule_2024_1", client_id=CLIENT_ID, reason="explicit_correction")
    
    print("User Action: Flagging stale eCFR 'flsa_ecfr_1' as incorrect.")
    handler.flag_memory_as_correction(memory_id="flsa_ecfr_1", client_id=CLIENT_ID, reason="explicit_correction")

    # --- PHASE 3: SVTD RERANKED RAG ---
    print("\n" + "-" * 40)
    print(" PHASE 3: SVTD Reranked RAG (After Correction)")
    print("-" * 40)
    
    # Step 1: Get initial RAG results (same as vanilla)
    initial_results = mock_search(DEMO_QUERY, corpus)
    
    # Step 2: Rerank using SVTD Ledger
    svtd_results = rerank_results(initial_results, ledger, CLIENT_ID)
    
    for i, res in enumerate(svtd_results[:3], 1):
        status = res["metadata"].get("status", "unknown")
        trust = res.get("trust_weight", 1.0)
        final_score = res.get("trust_weighted_relevance", res["relevance_score"])
        print(f"{i}. [{res['memory_id']}] Trust: {trust:.3f} | Weighted Score: {final_score:.3f} | Status: {status}")
        print(f"   Content: {res['content'][:120]}...")
        
    top_svtd = svtd_results[0]
    if "684" in top_svtd["content"]:
        print("\n[PASS] SUCCESS: SVTD reranking promoted the CONTROLLING rule ($684).")
    else:
        print("\n[FAIL] FAILURE: SVTD did not promote the correct rule.")

    print("\n" + "=" * 80)
    print(" DEMO COMPLETE: Trust-weighted retrieval ensures truth over time.")
    print("=" * 80)
    
    # Cleanup
    ledger.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

if __name__ == "__main__":
    main()
