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
SVTD (Scalable Vector Trust Decay) Core - A trust layer for RAG pipelines.
"""

from .trust_engine import (
    GHOST_STATE_THRESHOLD,
    DEFAULT_TRUST_WEIGHT,
    DECAY_FACTOR,
    apply_decay,
    calculate_trust_weight,
)
from .trust_ledger import TrustLedger
from .integration import (
    rerank_results,
    multiply_relevance_by_trust,
)
from .correction import CorrectionHandler

__all__ = [
    "GHOST_STATE_THRESHOLD",
    "DEFAULT_TRUST_WEIGHT",
    "DECAY_FACTOR",
    "apply_decay",
    "calculate_trust_weight",
    "TrustLedger",
    "rerank_results",
    "multiply_relevance_by_trust",
    "CorrectionHandler",
]
