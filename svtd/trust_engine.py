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
SVTD Trust Engine - Core trust scoring and decay logic.
"""

from typing import Union

# Constants
GHOST_STATE_THRESHOLD = 0.1
DEFAULT_TRUST_WEIGHT = 1.0
DECAY_FACTOR = 0.01

def apply_decay(current_weight: float, factor: float = DECAY_FACTOR) -> float:
    """
    Apply decay to the current trust weight.
    
    Args:
        current_weight: The current trust weight (usually 0.0 to 1.0).
        factor: The decay factor to multiply by.
        
    Returns:
        The new trust weight.
    """
    return max(0.01, current_weight * factor)

def calculate_trust_weight(relevance: float, trust: float) -> float:
    """
    Calculate the combined trust-weighted relevance score.
    
    Args:
        relevance: The original relevance score (e.g., cosine similarity).
        trust: The trust weight for the memory chunk.
        
    Returns:
        The trust-weighted relevance score.
    """
    return relevance * trust
