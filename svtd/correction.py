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
SVTD Correction Handling - Manage user corrections and trust decay.
"""

from typing import Optional, Dict, Any
from .trust_ledger import TrustLedger
from .trust_engine import apply_decay, DECAY_FACTOR

class CorrectionHandler:
    """Handles memory corrections and applies trust decay."""
    
    def __init__(self, ledger: TrustLedger):
        """
        Initialize the CorrectionHandler.
        
        Args:
            ledger: The TrustLedger instance.
        """
        self.ledger = ledger
        
    def flag_memory_as_correction(self, memory_id: str, 
                                  client_id: str = "default", 
                                  decay_factor: float = DECAY_FACTOR,
                                  reason: str = "explicit_correction",
                                  corrected_by: Optional[str] = None) -> float:
        """
        Explicitly flag a memory as causing an error (triggers trust decay).
        
        Args:
            memory_id: The ID of the incorrect memory chunk.
            client_id: Client identifier.
            decay_factor: The factor to multiply the current weight by (default 0.01).
            reason: Reason for flagging (default "explicit_correction").
            corrected_by: Optional ID of the memory that replaces/corrects this one.
            
        Returns:
            The new trust weight.
        """
        current_weight = self.ledger.get_trust_weight(memory_id, client_id)
        new_weight = apply_decay(current_weight, decay_factor)
        
        self.ledger.update_trust_weight(
            memory_id=memory_id,
            weight=new_weight,
            client_id=client_id,
            reason=reason,
            corrected_by=corrected_by
        )
        
        return new_weight
