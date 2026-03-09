# Simple RAG Demo

A minimal demonstration of SVTD working with a basic in-memory RAG system.

**No external vector database required** - uses simple keyword matching.

---

## Quick Start

```bash
cd demos/simple_rag_demo
python demo.py
```

---

## What This Demo Shows

### The Scenario

Your company has updated office hours:
- **Old:** 9 AM - 5 PM
- **New:** 8 AM - 6 PM (with flexible scheduling)

### The Problem

When users ask about office hours, the RAG system returns the **old** hours because:
1. More documents mention "9 AM" and "5 PM"
2. Simple keyword matching favors the old policy

### The Solution

SVTD trust weighting:
1. User corrects the bot: "Actually, we changed to 8-6"
2. SVTD decays trust on the old memory (1.0 → 0.01)
3. Next query returns the correct, updated hours

---

## Demo Output

```
============================================================
  SVTD Simple RAG Demo
============================================================

[Step 1] Initialize RAG system and Trust Ledger
  ✓ RAG system ready
  ✓ Trust Ledger initialized

[Step 2] Add memories to the system
  ✓ Added 3 memories:
    - [mem_0001] The office opens at 9 AM and closes at 5 PM...
    - [mem_0002] Lunch break is from 12 PM to 1 PM...
    - [mem_0003] Starting March 2025, office hours are 8 AM to 6 PM...

[Step 3] Query: 'What are the office hours?'
  🤖 Bot says: 'The office opens at 9 AM and closes at 5 PM.'
  ⚠️  This is the OLD hours (before March 2025)

[Step 4] User provides correction
  ✓ Flagged mem_0001 as incorrect

[Step 5] Query again: 'What are the office hours?'
  🤖 Bot says: 'Starting March 2025, office hours are 8 AM to 6 PM...'
  ✓ This is the CORRECT updated hours!
```

---

## Key Features Demonstrated

| Feature | Demonstration |
|---------|---------------|
| Trust decay | Old memory trust: 1.0 → 0.01 |
| Ghost state | Old memory marked as ghost |
| Reranking | New memory promoted to top |
| Non-destructive | Old memory still exists (audit) |

---

## How It Works

### 1. Simple RAG Class

```python
class SimpleRAG:
    def search(self, query: str):
        # Basic keyword matching
        # Returns: [{"memory_id": "...", "content": "...", "relevance_score": 0.9}]
```

### 2. SVTD Integration

```python
# Get raw results
raw_results = rag.search("office hours")

# Apply SVTD reranking
reranked = rerank_results(raw_results, ledger)

# Use top result
top_answer = reranked[0]['content']
```

### 3. User Correction

```python
# User flags old information as incorrect
handler.flag_memory_as_correction("mem_0001")

# Trust weight automatically decays
# Next query uses new trust weights
```

---

## Why This Matters

### Without SVTD

```
User: What are the office hours?
Bot: 9 AM to 5 PM (old, wrong)
User: Actually, it's 8-6 now
Bot: Sorry, you have 8 AM to 6 PM (old answer still in system)
```

### With SVTD

```
User: What are the office hours?
Bot: 8 AM to 6 PM with flexible scheduling (correct!)
```

The user never sees the wrong answer after the first correction.

---

## Extending This Demo

### Add More Memories

```python
rag.add_memory("Remote work is allowed 2 days per week.")
rag.add_memory("New office location: Building C, Floor 3.")
```

### Try Different Queries

```python
results = rag.search("remote work policy")
results = rag.search("building location")
```

### Simulate Multiple Corrections

```python
# Flag multiple memories
handler.flag_memory_as_correction("mem_0002")
handler.flag_memory_as_correction("mem_0003")
```

---

## Next Steps

- **Law Demo**: See a real legal use case
  ```bash
  python demos/law_demo/run_law_demo.py
  ```

- **Custom Integration**: Build your own RAG pipeline
  ```bash
  python examples/rag_pipeline.py
  ```

- **Documentation**: Learn more about SVTD
  ```bash
  cat docs/ARCHITECTURE.md
  ```

---

## License

Apache 2.0 - See [LICENSE](../../LICENSE)

---

*Built with 💙 by the Goldfish Team @ NovaCore*  
*Learn more at [memorygate.io](https://memorygate.io)*
