# SVTD API Reference

Complete API documentation for the SVTD package.

---

## Core Module: `svtd.trust_engine`

### Constants

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `GHOST_STATE_THRESHOLD` | float | 0.1 | Trust weight below which memories are "ghosted" |
| `DEFAULT_TRUST_WEIGHT` | float | 1.0 | Default trust for new memories |
| `DECAY_FACTOR` | float | 0.01 | Multiplicative decay factor (1% remaining) |

### Functions

#### `apply_decay(current_weight: float, factor: float = DECAY_FACTOR) -> float`

Apply decay to the current trust weight.

**Parameters:**
- `current_weight` (float): The current trust weight (0.0 to 1.0)
- `factor` (float): The decay factor (default: 0.01)

**Returns:**
- float: The new trust weight (minimum 0.01)

**Example:**
```python
from svtd import apply_decay

new_weight = apply_decay(1.0)  # Returns 0.01
new_weight = apply_decay(0.5, factor=0.5)  # Returns 0.25
```

---

#### `calculate_trust_weight(relevance: float, trust: float) -> float`

Calculate the combined trust-weighted relevance score.

**Parameters:**
- `relevance` (float): The original relevance score (e.g., cosine similarity)
- `trust` (float): The trust weight for the memory chunk

**Returns:**
- float: The trust-weighted relevance score

**Formula:**
```
final_relevance = relevance × trust
```

**Example:**
```python
from svtd import calculate_trust_weight

score = calculate_trust_weight(0.9, 1.0)  # Returns 0.9
score = calculate_trust_weight(0.9, 0.5)  # Returns 0.45
```

---

## Core Module: `svtd.trust_ledger`

### Class: `TrustLedger`

SQLite-based ledger for persisting trust weights.

#### Constructor

```python
TrustLedger(db_path: str = "svtd_trust.db")
```

**Parameters:**
- `db_path` (str): Path to the SQLite database file

**Example:**
```python
from svtd import TrustLedger

ledger = TrustLedger("my_trust.db")
```

---

#### Methods

##### `get_trust_weight(memory_id: str, client_id: str = "default") -> float`

Retrieve trust weight for a specific memory.

**Parameters:**
- `memory_id` (str): The ID of the memory chunk
- `client_id` (str): The client/user identifier (default: "default")

**Returns:**
- float: The trust weight (defaults to 1.0 if not found)

**Example:**
```python
weight = ledger.get_trust_weight("mem_123", "user_456")
print(f"Trust weight: {weight}")  # 1.0 if never set
```

---

##### `update_trust_weight(
    memory_id: str,
    weight: float,
    client_id: str = "default",
    reason: Optional[str] = None,
    corrected_by: Optional[str] = None
)`

Update trust weight for a memory.

**Parameters:**
- `memory_id` (str): The ID of the memory chunk
- `weight` (float): The new trust weight
- `client_id` (str): The client/user identifier
- `reason` (Optional[str]): Reason for the update (e.g., "decay", "correction")
- `corrected_by` (Optional[str]): ID of the memory that corrects this one

**Example:**
```python
ledger.update_trust_weight(
    memory_id="mem_123",
    weight=0.01,
    client_id="user_456",
    reason="explicit_correction"
)
```

---

##### `load_all_weights(client_id: Optional[str] = None) -> Dict[str, float]`

Load all trust weights into memory for fast lookup.

**Parameters:**
- `client_id` (Optional[str]): Optional client ID to filter by

**Returns:**
- Dict[str, float]: Dictionary mapping memory_id to trust_weight

**Example:**
```python
# Load all weights for a specific client
weights = ledger.load_all_weights("user_456")
for memory_id, trust in weights.items():
    print(f"{memory_id}: {trust}")

# Load all weights (all clients)
all_weights = ledger.load_all_weights()
```

---

##### `close()`

Close the database connection.

**Example:**
```python
ledger.close()
```

---

## Core Module: `svtd.correction`

### Class: `CorrectionHandler`

Handles memory corrections and applies trust decay.

#### Constructor

```python
CorrectionHandler(ledger: TrustLedger)
```

**Parameters:**
- `ledger` (TrustLedger): The TrustLedger instance

**Example:**
```python
from svtd import TrustLedger, CorrectionHandler

ledger = TrustLedger("trust.db")
handler = CorrectionHandler(ledger)
```

---

#### Methods

##### `flag_memory_as_correction(
    memory_id: str,
    client_id: str = "default",
    decay_factor: float = DECAY_FACTOR,
    reason: str = "explicit_correction",
    corrected_by: Optional[str] = None
) -> float`

Explicitly flag a memory as causing an error (triggers trust decay).

**Parameters:**
- `memory_id` (str): The ID of the incorrect memory chunk
- `client_id` (str): Client identifier
- `decay_factor` (float): The factor to multiply current weight by (default: 0.01)
- `reason` (str): Reason for flagging (default: "explicit_correction")
- `corrected_by` (Optional[str]): ID of the memory that replaces/corrects this one

**Returns:**
- float: The new trust weight

**Example:**
```python
new_weight = handler.flag_memory_as_correction(
    memory_id="mem_123",
    client_id="user_456",
    reason="user_correction"
)
print(f"New trust weight: {new_weight}")  # 0.01
```

---

## Core Module: `svtd.integration`

### Functions

#### `multiply_relevance_by_trust(
    results: List[Dict[str, Any]],
    ledger: Optional[TrustLedger] = None,
    client_id: str = "default"
) -> List[Dict[str, Any]]`

Multiply each result's relevance score by its trust weight.

**Parameters:**
- `results` (List[Dict]): List of retrieved memory objects (must contain 'memory_id' and 'relevance_score')
- `ledger` (Optional[TrustLedger]): The TrustLedger instance (if None, uses default 1.0)
- `client_id` (str): Client identifier

**Returns:**
- List[Dict]: The updated results list with additional fields:
  - `original_relevance`: Original relevance score
  - `trust_weight`: Applied trust weight
  - `relevance_score`: Trust-weighted relevance (final)
  - `is_ghost`: True if below ghost threshold

**Example:**
```python
from svtd import multiply_relevance_by_trust

results = [
    {"memory_id": "mem_1", "content": "...", "relevance_score": 0.9},
]

updated = multiply_relevance_by_trust(results, ledger, "user_1")
print(updated[0]['trust_weight'])
print(updated[0]['is_ghost'])
```

---

#### `rerank_results(
    results: List[Dict[str, Any]],
    ledger: Optional[TrustLedger] = None,
    client_id: str = "default"
) -> List[Dict[str, Any]]`

Apply trust weighting and rerank results.

**Parameters:**
- `results` (List[Dict]): List of retrieved memory objects
- `ledger` (Optional[TrustLedger]): The TrustLedger instance
- `client_id` (str): Client identifier

**Returns:**
- List[Dict]: Reranked list of results (sorted by trust-weighted relevance, descending)

**Example:**
```python
from svtd import rerank_results

# Get results from your vector DB
results = vector_db.query("my query")

# Rerank with SVTD
reranked = rerank_results(results, ledger, "user_1")

# Use top result
top_result = reranked[0]
```

---

## Complete Example

```python
from svtd import (
    TrustLedger,
    CorrectionHandler,
    rerank_results,
    apply_decay,
    calculate_trust_weight
)

# Initialize
ledger = TrustLedger("trust.db")
handler = CorrectionHandler(ledger)

# Simulate RAG results
results = [
    {
        "memory_id": "old_policy",
        "content": "Old vacation policy: 15 days",
        "relevance_score": 0.95
    },
    {
        "memory_id": "new_policy", 
        "content": "New vacation policy: 20 days",
        "relevance_score": 0.85
    }
]

# User corrects the old policy
handler.flag_memory_as_correction("old_policy", "user_1")

# Rerank with trust weights
reranked = rerank_results(results, ledger, "user_1")

# New policy now ranks higher
print(reranked[0]["content"])  # "New vacation policy: 20 days"

# Cleanup
ledger.close()
```

---

## Type Hints

For type checking, you can use the following types:

```python
from typing import Dict, Any, List, Optional

MemoryResult = Dict[str, Any]
# Contains: memory_id, content, relevance_score, metadata, etc.
```

---

## Error Handling

All functions handle edge cases gracefully:

- Missing memory IDs return default trust (1.0)
- Missing ledger defaults to trust = 1.0
- Invalid weights are clamped to valid range [0.01, 1.0]

**Example:**
```python
# Memory never seen before - returns default
weight = ledger.get_trust_weight("unknown_id")  # Returns 1.0

# Works even without ledger
reranked = rerank_results(results, ledger=None)  # No trust weighting applied
```

---

## See Also

- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Value Proposition](VALUE_PROPOSITION.md) - Why use SVTD
- [Examples](../examples/) - Code examples and integrations

---

*For managed enterprise features and support, visit [MemoryGate.io](https://memorygate.io)*
