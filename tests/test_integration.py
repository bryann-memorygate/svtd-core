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
Integration tests for SVTD reranking pipeline.

Run with: pytest tests/test_integration.py -v
"""

import os
import tempfile
import pytest
from svtd import (
    TrustLedger,
    CorrectionHandler,
    rerank_results,
    multiply_relevance_by_trust,
)


class TestReranking:
    """Test the reranking integration."""
    
    def setup_method(self):
        """Create a temporary database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_trust.db")
        self.ledger = TrustLedger(self.db_path)
    
    def teardown_method(self):
        """Clean up temporary database."""
        self.ledger.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_rerank_moves_stale_down(self):
        """Reranking should move stale (low trust) results down."""
        # Setup: old info has high semantic relevance but low trust
        results = [
            {"memory_id": "old_info", "content": "Old data", "relevance_score": 0.95},
            {"memory_id": "new_info", "content": "New data", "relevance_score": 0.85},
        ]
        
        # Decay the old info's trust
        self.ledger.update_trust_weight("old_info", 0.01, "default")
        
        # Rerank
        reranked = rerank_results(results, self.ledger, "default")
        
        # New info should now be first
        assert reranked[0]["memory_id"] == "new_info"
        assert reranked[1]["memory_id"] == "old_info"
    
    def test_rerank_preserves_order_with_equal_trust(self):
        """With equal trust, order should be by relevance."""
        results = [
            {"memory_id": "mem_1", "content": "Content 1", "relevance_score": 0.9},
            {"memory_id": "mem_2", "content": "Content 2", "relevance_score": 0.8},
        ]
        
        # Both have default trust (1.0)
        reranked = rerank_results(results, self.ledger, "default")
        
        assert reranked[0]["memory_id"] == "mem_1"
        assert reranked[1]["memory_id"] == "mem_2"
    
    def test_rerank_calculates_trust_weighted_scores(self):
        """Reranking should calculate trust-weighted relevance."""
        results = [
            {"memory_id": "mem_1", "content": "Content", "relevance_score": 0.8},
        ]
        
        self.ledger.update_trust_weight("mem_1", 0.5, "default")
        reranked = rerank_results(results, self.ledger, "default")
        
        assert reranked[0]["trust_weight"] == 0.5
        assert reranked[0]["original_relevance"] == 0.8
        assert reranked[0]["relevance_score"] == 0.4  # 0.8 * 0.5
    
    def test_rerank_marks_ghost_state(self):
        """Memories below ghost threshold should be marked."""
        results = [
            {"memory_id": "ghost_mem", "content": "Ghost", "relevance_score": 0.5},
        ]
        
        self.ledger.update_trust_weight("ghost_mem", 0.05, "default")
        reranked = rerank_results(results, self.ledger, "default")
        
        assert reranked[0]["is_ghost"] is True
    
    def test_multiply_without_ledger(self):
        """Should work without ledger (all trust = 1.0)."""
        results = [
            {"memory_id": "mem_1", "content": "Content", "relevance_score": 0.8},
        ]
        
        multiplied = multiply_relevance_by_trust(results, None, "default")
        
        assert multiplied[0]["trust_weight"] == 1.0
        assert multiplied[0]["relevance_score"] == 0.8


class TestCorrectionHandler:
    """Test the correction handler workflow."""
    
    def setup_method(self):
        """Create a temporary database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_trust.db")
        self.ledger = TrustLedger(self.db_path)
        self.handler = CorrectionHandler(self.ledger)
    
    def teardown_method(self):
        """Clean up temporary database."""
        self.ledger.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_flag_memory_applies_decay(self):
        """Flagging a memory should apply trust decay."""
        # Set initial trust
        self.ledger.update_trust_weight("bad_memory", 1.0, "client_1")
        
        # Flag it
        new_weight = self.handler.flag_memory_as_correction(
            "bad_memory", "client_1"
        )
        
        # Should be decayed
        assert new_weight == 0.01  # 1.0 * 0.01
        
        # Verify in ledger
        stored_weight = self.ledger.get_trust_weight("bad_memory", "client_1")
        assert stored_weight == 0.01
    
    def test_flag_memory_with_reason(self):
        """Flagging should accept a reason parameter."""
        new_weight = self.handler.flag_memory_as_correction(
            "mem_1", "client_1", reason="user_correction"
        )
        
        assert new_weight == 0.01
    
    def test_multiple_corrections_escalate(self):
        """Multiple corrections should continue to decay."""
        # First correction: 1.0 -> 0.01
        w1 = self.handler.flag_memory_as_correction("mem_1", "client_1")
        assert w1 == 0.01
        
        # Second correction: 0.01 stays at 0.01 (minimum)
        w2 = self.handler.flag_memory_as_correction("mem_1", "client_1")
        assert w2 == 0.01


class TestEndToEnd:
    """End-to-end tests simulating real usage."""
    
    def setup_method(self):
        """Create a temporary database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_trust.db")
        self.ledger = TrustLedger(self.db_path)
        self.handler = CorrectionHandler(self.ledger)
    
    def teardown_method(self):
        """Clean up temporary database."""
        self.ledger.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_policy_update_scenario(self):
        """Simulate a policy update scenario."""
        # Initial RAG results - old policy has higher semantic match
        results = [
            {
                "memory_id": "policy_2024",
                "content": "Vacation days: 15",
                "relevance_score": 0.92,
                "metadata": {"year": 2024}
            },
            {
                "memory_id": "policy_2025",
                "content": "Vacation days: 20",
                "relevance_score": 0.85,
                "metadata": {"year": 2025}
            },
        ]
        
        # User corrects: "No, vacation is 20 days now"
        self.handler.flag_memory_as_correction("policy_2024", "hr_dept")
        
        # Rerank
        reranked = rerank_results(results, self.ledger, "hr_dept")
        
        # 2025 policy should now rank higher despite lower semantic score
        assert reranked[0]["memory_id"] == "policy_2025"
        assert reranked[0]["relevance_score"] == 0.85  # Unchanged trust
        assert reranked[1]["relevance_score"] < 0.1  # Decayed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
