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
SVTD Integration - Drop-in reranking functions for RAG pipelines.
"""

from typing import List, Dict, Any, Optional
from .trust_engine import calculate_trust_weight, GHOST_STATE_THRESHOLD
from .trust_ledger import TrustLedger

def multiply_relevance_by_trust(results: List[Dict[str, Any]], 
                               ledger: Optional[TrustLedger] = None,
                               client_id: str = "default") -> List[Dict[str, Any]]:
    """
    Multiply each result's relevance score by its trust weight.
    
    Args:
        results: List of retrieved memory objects (must contain 'memory_id' and 'relevance_score').
        ledger: The TrustLedger instance to look up weights. If None, uses default 1.0.
        client_id: Client identifier for weight lookup.
        
    Returns:
        The updated results list.
    """
    # Pre-load all weights for performance if ledger is provided
    weights = ledger.load_all_weights(client_id) if ledger else {}
    
    for item in results:
        memory_id = item.get('memory_id')
        if not memory_id:
            continue
            
        trust = weights.get(memory_id, 1.0)
        relevance = item.get('relevance_score', 0.0)
        
        trust_weighted_relevance = calculate_trust_weight(relevance, trust)
        
        item['original_relevance'] = relevance
        item['trust_weight'] = trust
        item['relevance_score'] = trust_weighted_relevance
        
        # Mark as ghost state if below threshold
        item['is_ghost'] = trust_weighted_relevance < GHOST_STATE_THRESHOLD
        
    return results

def rerank_results(results: List[Dict[str, Any]], 
                   ledger: Optional[TrustLedger] = None,
                   client_id: str = "default") -> List[Dict[str, Any]]:
    """
    Apply trust weighting and rerank results.
    
    Args:
        results: List of retrieved memory objects.
        ledger: The TrustLedger instance.
        client_id: Client identifier.
        
    Returns:
        Reranked list of results (sorted by trust-weighted relevance).
    """
    # First, calculate trust-weighted relevance
    results = multiply_relevance_by_trust(results, ledger, client_id)
    
    # Then sort by relevance_score descending
    results.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
    
    return results
