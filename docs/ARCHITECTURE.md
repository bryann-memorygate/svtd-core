# SVTD Architecture

**Last Updated:** 2026-03-08  
**Version:** 0.1.0

---

## Overview

SVTD (Surgical Vector Trust Decay) is a trust layer that sits between your vector database and your LLM. It applies multiplicative trust weights to semantic relevance scores, enabling non-destructive correction of RAG systems.

---

## Core Algorithm

### The Trust Formula

```
final_relevance = semantic_relevance × trust_weight
```

Where:
- **semantic_relevance**: Cosine similarity from your vector DB (0.0 to 1.0)
- **trust_weight**: Current trust level for this memory (0.01 to 1.0)
- **final_relevance**: Trust-weighted score used for ranking

### Trust Decay

When a memory is flagged as incorrect:

```python
new_trust = max(0.01, current_trust × DECAY_FACTOR)
# DECAY_FACTOR = 0.01
# So: 1.0 → 0.01 (100x reduction)
```

This aggressive decay ensures corrected memories are immediately suppressed.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Query                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Vector Database (RAG)                     │
│              (Pinecone, Chroma, Weaviate, etc.)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Returns: List[Document]
                              │   - memory_id
                              │   - content
                              │   - relevance_score
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         SVTD Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │Trust Ledger │  │   Correction │  │   Reranking      │  │
│  │  (SQLite)   │  │   Handler    │  │   Engine         │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Returns: Reranked results
                              │   - trust_weight applied
                              │   - is_ghost flag set
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Final Results                           │
│              (Stale info suppressed)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM (Your Model)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Trust Ledger

The `TrustLedger` class provides persistent storage for trust weights using SQLite.

**Key Features:**
- Client isolation (separate trust weights per user/tenant)
- Feedback count tracking
- Automatic cold memory detection
- Full audit trail with timestamps

**Schema:**
```sql
CREATE TABLE trust_weights (
    memory_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    trust_weight REAL DEFAULT 1.0,
    feedback_count INTEGER DEFAULT 0,
    is_cold BOOLEAN DEFAULT 0,
    last_feedback TEXT,
    decay_reason TEXT,
    corrected_by TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (memory_id, client_id)
)
```

### 2. Correction Handler

The `CorrectionHandler` class manages user and system corrections.

**Key Methods:**
- `flag_memory_as_correction()` - Apply decay to a memory
- Supports explicit corrections and user flags
- Configurable decay factors and reasons

### 3. Reranking Engine

Provides drop-in functions for integrating with existing RAG pipelines.

**Key Functions:**
- `rerank_results()` - Apply trust weighting and sort
- `multiply_relevance_by_trust()` - In-place score modification

---

## The Ghost State

Memories with `trust_weight < GHOST_STATE_THRESHOLD` (0.1) enter "ghost state":

| Property | Value |
|----------|-------|
| Still in database | ✅ Yes (audit trail) |
| Returned in results | ❌ No (filtered) |
| Can be recovered | ✅ Yes (rehabilitation) |

This provides:
- **Non-destructive suppression** - Information is never lost
- **Audit compliance** - Full history preserved
- **Safety net** - Wrong corrections can be reversed

---

## Trust Lifecycle

```
New Memory
    │
    ▼
┌─────────────┐
│ trust = 1.0 │  ← Default: fully trusted
└─────────────┘
    │
    │ User correction detected
    ▼
┌─────────────┐
│ trust = 0.01│  ← Aggressive decay
└─────────────┘
    │
    │ Multiple corrections
    ▼
┌─────────────┐
│ trust < 0.1 │  ← Ghost state
└─────────────┘
    │
    │ User rehabilitation
    ▼
┌─────────────┐
│ trust += 0.1│  ← Gradual recovery
└─────────────┘
```

---

## Integration Patterns

### Pattern 1: Post-Retrieval Reranking

Most common pattern - add SVTD after your vector DB retrieval:

```python
# 1. Retrieve from vector DB
results = vector_db.query(query)

# 2. Rerank with SVTD
reranked = rerank_results(results, ledger, client_id)

# 3. Use top results
for result in reranked[:5]:
    context += result['content']
```

### Pattern 2: Custom Retriever

Wrap SVTD in a custom retriever class:

```python
class SVTDRetriever:
    def __init__(self, base_retriever, ledger):
        self.base = base_retriever
        self.ledger = ledger
    
    def retrieve(self, query):
        raw = self.base.retrieve(query)
        return rerank_results(raw, self.ledger)
```

### Pattern 3: Correction API

Expose corrections via API:

```python
@app.post("/feedback")
def feedback(memory_id: str, is_correct: bool):
    if not is_correct:
        handler.flag_memory_as_correction(memory_id)
    return {"status": "ok"}
```

---

## Privacy Considerations

### Opaque Memory Handles

SVTD supports privacy-safe operation using opaque handles:

```python
# Create handle from client_id + memory_id
handle = hashlib.sha256(
    f"{client_id}:{memory_id}".encode()
).hexdigest()[:32]

# Store using handle, not raw IDs
ledger.update_trust_weight(handle, trust_weight)
```

This ensures:
- Client IDs are not exposed in storage
- Cross-client collision prevention
- GDPR-compliant audit trails

### Privacy Mode (Ghost Protocol)

When `SVTD_PRIVACY_MODE=true`:

| Feature | Behavior |
|---------|----------|
| Trust scoring | ✅ Same |
| Decay formulas | ✅ Same |
| Content storage | ❌ None (NULL) |
| Vector search | ✅ Same |

---

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Trust lookup | O(1) | SQLite index on memory_id + client_id |
| Trust update | O(1) | Single row write |
| Reranking | O(n log n) | n = number of retrieved results |
| Batch load | O(n) | Load all weights for a client |

**Typical Latency:**
- Trust lookup: < 1ms
- Reranking 100 results: < 5ms
- Full pipeline overhead: < 10ms

---

## Scalability

### Single Node

SQLite handles:
- Up to 10M trust records
- Thousands of operations per second
- Suitable for most applications

### Multi-Node (Future)

For high-scale deployments, MemoryGate.io provides:
- Distributed trust storage (PostgreSQL)
- Redis caching layer
- Horizontal scaling

---

## Security

### Data Isolation

- Client IDs isolate trust weights between users
- No content stored in trust ledger (only IDs and scores)
- SQLite file permissions respected

### Audit Trail

Every trust change is logged:
- Timestamp
- Memory ID
- Old and new trust weights
- Reason for change
- Client ID

---

## Comparison: SVTD vs Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Delete stale docs** | Simple | Loses history, can't recover |
| **Version tags** | Keeps history | Requires manual versioning |
| **Recency boost** | Automatic | Recency ≠ truth |
| **SVTD** | Surgical, auditable, recoverable | Adds complexity |

---

## Related Documentation

- [Value Proposition](VALUE_PROPOSITION.md) - Why RAG alone isn't enough
- [API Reference](API.md) - Complete API documentation
- [Contributing](../CONTRIBUTING.md) - How to contribute

---

*For enterprise features (auto-detection, multi-tenancy, analytics), visit [MemoryGate.io](https://memorygate.io)*
