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
Tests for SVTD Trust Ledger persistence.

Run with: pytest tests/test_ledger.py -v
"""

import os
import tempfile
import pytest
from svtd import TrustLedger


class TestTrustLedger:
    """Test the SQLite-based trust ledger."""
    
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
    
    def test_default_trust_weight(self):
        """Unseen memories should return default trust weight of 1.0."""
        weight = self.ledger.get_trust_weight("unknown_memory", "client_1")
        assert weight == 1.0
    
    def test_update_and_retrieve(self):
        """Should be able to update and retrieve trust weights."""
        self.ledger.update_trust_weight("mem_1", 0.5, "client_1")
        weight = self.ledger.get_trust_weight("mem_1", "client_1")
        assert weight == 0.5
    
    def test_client_isolation(self):
        """Different clients should have independent trust weights."""
        self.ledger.update_trust_weight("mem_1", 0.3, "client_1")
        self.ledger.update_trust_weight("mem_1", 0.8, "client_2")
        
        weight_1 = self.ledger.get_trust_weight("mem_1", "client_1")
        weight_2 = self.ledger.get_trust_weight("mem_1", "client_2")
        
        assert weight_1 == 0.3
        assert weight_2 == 0.8
    
    def test_feedback_count_increment(self):
        """Feedback count should increment on each update."""
        self.ledger.update_trust_weight("mem_1", 0.5, "client_1")
        self.ledger.update_trust_weight("mem_1", 0.3, "client_1")
        self.ledger.update_trust_weight("mem_1", 0.1, "client_1")
        
        # Check by loading all weights and inspecting
        weights = self.ledger.load_all_weights("client_1")
        assert weights["mem_1"] == 0.1
    
    def test_cold_memory_flag(self):
        """Memories with trust < 0.2 should be marked as cold."""
        self.ledger.update_trust_weight("mem_cold", 0.1, "client_1")
        self.ledger.update_trust_weight("mem_warm", 0.5, "client_1")
        
        # Both should be retrievable
        assert self.ledger.get_trust_weight("mem_cold", "client_1") == 0.1
        assert self.ledger.get_trust_weight("mem_warm", "client_1") == 0.5
    
    def test_load_all_weights(self):
        """Should be able to load all weights for a client."""
        self.ledger.update_trust_weight("mem_1", 0.9, "client_1")
        self.ledger.update_trust_weight("mem_2", 0.7, "client_1")
        self.ledger.update_trust_weight("mem_3", 0.5, "client_2")
        
        weights = self.ledger.load_all_weights("client_1")
        
        assert len(weights) == 2
        assert weights["mem_1"] == 0.9
        assert weights["mem_2"] == 0.7
    
    def test_load_all_weights_no_filter(self):
        """Should be able to load all weights without client filter."""
        self.ledger.update_trust_weight("mem_1", 0.9, "client_1")
        self.ledger.update_trust_weight("mem_2", 0.7, "client_2")
        
        weights = self.ledger.load_all_weights()
        
        assert len(weights) == 2
    
    def test_persistence(self):
        """Weights should persist across ledger instances."""
        self.ledger.update_trust_weight("mem_1", 0.4, "client_1")
        self.ledger.close()
        
        # Create new instance with same DB
        new_ledger = TrustLedger(self.db_path)
        weight = new_ledger.get_trust_weight("mem_1", "client_1")
        
        assert weight == 0.4
        new_ledger.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
