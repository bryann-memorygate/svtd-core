# SVTD: Surgical Vector Trust Decay

<p align="center">
  <strong>Trust-Weighted Retrieval for RAG Systems</strong><br>
  <a href="https://memorygate.io">MemoryGate.io</a> • 
  <a href="https://github.com/bryann-memorygate/svtd-core">GitHub</a>
</p>

---

**SVTD** (Surgical Vector Trust Decay) is an open-source trust layer for RAG (Retrieval-Augmented Generation). It allows you to mathematically decay the relevance of stale or incorrect memories based on user and system corrections.

> **Trusted by:** Enterprise teams building production RAG systems that need to handle changing knowledge.

---

## The Problem: RAG Returns Stale Data

In a production RAG system, semantic search often retrieves information that is no longer true. For example, if a company updates its remote work policy, a semantic search for "remote work" might still return the old policy because it contains more relevant keywords than the new one.

**Real-world scenarios where RAG breaks:**
- 📋 **Policy Updates** - Old HR policies outrank new ones
- ⚖️ **Legal Changes** - Superseded regulations appear current
- 📊 **Data Revisions** - Corrected metrics mixed with original
- 🔧 **Documentation Drift** - Outdated technical specs persist

## The Solution: Trust-Weighted Retrieval

SVTD adds a **Trust Dimension** to your retrieval pipeline. When a user corrects the AI ("No, that's the old policy, the new one is X"), SVTD applies a surgical decay to the specific vectors involved. 

**The Core Formula:**
```
Final Relevance = Semantic Relevance × Trust Weight
```

### Key Benefits

| Feature | Benefit |
|---------|---------|
| 🎯 **Non-destructive** | Memories suppressed, not deleted (full audit trail) |
| ⚡ **O(1) updates** | Instant trust changes, no re-indexing required |
| 🔒 **Privacy-safe** | Works with opaque memory handles |
| 🧩 **Drop-in** | Works with any vector DB (Pinecone, Chroma, Weaviate, etc.) |
| 📊 **Auditable** | Every correction tracked with timestamps |

---

## ⚖️ Law Demo: The Power of SVTD

We've included a real-world legal example involving the Fair Labor Standards Act (FLSA).

**The Scenario:**
- April 2024: DOL issues new rule ($844/week salary threshold)
- November 2024: Court vacates the rule, reinstates old threshold ($684/week)
- Problem: Semantic search still favors the newer (but invalid) rule

**Run the Demo:**
```bash
cd demos/law_demo
python run_law_demo.py
```

**Results:**
- **Vanilla RAG:** Returns stale rule ($844/week) - keyword match is stronger
- **SVTD:** After one correction, promotes **Controlling Order** ($684/week) to top

---

## Quickstart

### Installation

```bash
pip install svtd
```

### Basic Usage

```python
from svtd import TrustLedger, rerank_results, CorrectionHandler

# 1. Initialize the Trust Ledger (SQLite)
ledger = TrustLedger("trust.db")
handler = CorrectionHandler(ledger)

# 2. RAG results from your Vector DB (Pinecone, Chroma, etc.)
results = [
    {"memory_id": "mem_1", "content": "Old info", "relevance_score": 0.95},
    {"memory_id": "mem_2", "content": "New info", "relevance_score": 0.85},
]

# 3. Apply a correction (manual or via Sentinel)
handler.flag_memory_as_correction(client_id="user_123", memory_id="mem_1")

# 4. Rerank your results
reranked = rerank_results(client_id="user_123", results=results, ledger=ledger)

# mem_2 is now the top result!
print(reranked[0]["content"]) 
```

### More Examples

See the [`examples/`](examples/) folder for:
- LangChain integration
- LlamaIndex integration  
- Custom RAG pipeline integration

---

## How It Works

```
User Query
    ↓
RAG Retrieval (semantic search)
    ↓
SVTD Trust Weighting (multiplies by trust weight)
    ↓
Final Results (stale info suppressed)
```

### The "Ghost State"

Memories with `trust_weight < 0.2` enter "ghost state":
- ✅ Still exist in database (audit trail)
- ✅ Automatically filtered from results
- ✅ Can be recovered if approved

### Trust Decay Mechanics

| Trigger | Trust Change | Result |
|---------|--------------|--------|
| Explicit correction | ×0.01 | Immediate ghost state |
| User flag | ×0.01 | Trust drops significantly |
| Rehabilitation | +0.10 | Quick recovery |

---

## Architecture

**SVTD is a trust layer, not a content manager:**

- Your system injects corrected memories
- SVTD decays the wrong memories
- New memories naturally surface with trust = 1.0
- No explicit linking required (optional for audit)

**Privacy Mode (Ghost Protocol):**

When `SVTD_PRIVACY_MODE=true`, content is never stored - only trust scores and opaque handles.

---

## Enterprise: MemoryGate.io

SVTD is the open-source core of [MemoryGate.io](https://memorygate.io). 

| Feature | SVTD (Open Source) | MemoryGate.io (Managed) |
|---------|-------------------|------------------------|
| Manual corrections | ✅ | ✅ |
| Auto-detection (Sentinel) | ❌ | ✅ |
| Multi-tenancy | ❌ | ✅ |
| High-scale analytics | ❌ | ✅ |
| Role-based corrections | ❌ | ✅ |
| SLA & Support | Community | Enterprise |

**[Learn more about MemoryGate.io →](https://memorygate.io)**

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - How SVTD works under the hood
- [Value Proposition](docs/VALUE_PROPOSITION.md) - Why RAG alone isn't enough
- [API Reference](docs/API.md) - Complete API documentation
- [Contributing](CONTRIBUTING.md) - How to contribute

---

## Community & Support

- 🌐 **Website:** [memorygate.io](https://memorygate.io) - Learn more about the managed enterprise version
- 📧 **Contact:** Reach out via [memorygate.io](https://memorygate.io) for support and inquiries

---

## License & Patents

SVTD is licensed under the **Apache License 2.0**.

Provisional patents were filed in December 2025. The Apache 2.0 license includes an express patent grant for users of this software.

---

<p align="center">
  <em>Built with 💙 by the Goldfish Team @ NovaCore</em><br>
  <sub>Making AI memory trustworthy, one correction at a time.</sub>
</p>
