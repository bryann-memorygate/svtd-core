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
Tests for SVTD Trust Engine core calculations.

Run with: pytest tests/test_trust_engine.py -v
"""

import pytest
from svtd import (
    apply_decay,
    calculate_trust_weight,
    GHOST_STATE_THRESHOLD,
    DEFAULT_TRUST_WEIGHT,
    DECAY_FACTOR,
)


class TestApplyDecay:
    """Test the trust decay calculation."""
    
    def test_default_decay_factor(self):
        """Default decay should reduce weight by factor of 0.01."""
        result = apply_decay(1.0)
        assert result == 0.01
    
    def test_custom_decay_factor(self):
        """Custom decay factor should work correctly."""
        result = apply_decay(1.0, factor=0.5)
        assert result == 0.5
    
    def test_decay_respects_minimum(self):
        """Decay should not go below 0.01 minimum."""
        result = apply_decay(0.02)
        assert result == 0.01  # Max(0.01, 0.02 * 0.01 = 0.0002)
    
    def test_decay_partial_weight(self):
        """Decay should work on partial weights (respecting minimum)."""
        result = apply_decay(0.5)
        assert result == 0.01  # Max(0.01, 0.5 * 0.01 = 0.005) -> clamped to 0.01
    
    def test_decay_already_at_minimum(self):
        """Decay at minimum should stay at minimum."""
        result = apply_decay(0.01)
        assert result == 0.01


class TestCalculateTrustWeight:
    """Test the trust-weighted relevance calculation."""
    
    def test_perfect_trust(self):
        """With trust=1.0, relevance should be unchanged."""
        result = calculate_trust_weight(0.9, 1.0)
        assert result == 0.9
    
    def test_no_trust(self):
        """With trust=0.0, relevance should be zero."""
        result = calculate_trust_weight(0.9, 0.0)
        assert result == 0.0
    
    def test_partial_trust(self):
        """Partial trust should reduce relevance proportionally."""
        result = calculate_trust_weight(0.8, 0.5)
        assert result == 0.4
    
    def test_high_relevance_low_trust(self):
        """High relevance with low trust should be suppressed."""
        result = calculate_trust_weight(0.95, 0.1)
        assert result == 0.095


class TestConstants:
    """Test that constants have expected values."""
    
    def test_ghost_state_threshold(self):
        """Ghost state threshold should be 0.1."""
        assert GHOST_STATE_THRESHOLD == 0.1
    
    def test_default_trust_weight(self):
        """Default trust weight should be 1.0."""
        assert DEFAULT_TRUST_WEIGHT == 1.0
    
    def test_decay_factor(self):
        """Decay factor should be 0.01."""
        assert DECAY_FACTOR == 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
