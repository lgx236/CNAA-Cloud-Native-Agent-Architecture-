# CNAA Memory Scoring System - Complete Documentation Index

> 🎯 **Welcome!** This is the central hub for all Memory Scoring System documentation.
> 
> ⚡ **Status**: Active Development (v1.0) - Changes expected during development phase.

---

## 📋 Documentation Overview

### 🔰 Getting Started (Start Here!)

1. **[Usage Guide](./MEMORY_SCORING_GUIDE.md)**
   - What is memory scoring?
   - How to use in your code
   - Common patterns and examples
   - Best practices

2. **[API Reference](./API_REFERENCE_SCORING.md)**
   - Complete API surface with type signatures
   - All parameters and return values
   - Algorithm details
   - Version history

### 🏗️ Architecture & Design

3. **[Architecture Principles](./SCORING_ARCHITECTURE.md)** (Coming Soon)
   - Design decisions rationale
   - Module dependency map
   - Extension points
   - Performance characteristics

4. **[Change Impact Analysis](./SCORING_CHANGE_ANALYSIS.md)** ⭐ IMPORTANT
   - Module dependencies
   - Breaking change detection
   - Risk assessment templates
   - **Required reading before making ANY changes**

5. **[Safe Development Guidelines](./SCORING_SAFE_DEVELOPMENT.md)** ⭐ CRITICAL
   - Type safety checklist
   - Refactoring safely
   - Testing workflows
   - Rollback procedures
   - **Follow this to avoid global breaks!**

### 🧪 Testing & Quality

6. **[Testing Strategy](./SCORING_TESTING.md)** (Coming Soon)
   - Test pyramid
   - Mocking strategies
   - Performance benchmarks
   - CI/CD integration

7. **[Known Limitations](./SCORING_LIMITATIONS.md)** (Coming Soon)
   - Current constraints
   - Future improvements
   - Workarounds for edge cases

---

## 🚀 Quick Start Examples

### Example 1: Basic Usage

```python
from cnaa.memory_selector import create_scored_selector
from cloud.storage.memory_store import InMemoryMemoryStore

store = InMemoryMemoryStore()
selector = create_scored_selector(store)

# Store some memories
# ... (see full example below)

# Get top 5 scored memories
top_memories = selector.get_top_n("alice", n=5)
for mem, score in top_memories:
    print(f"{mem.memory_id}: {score:.3f}")
```

### Example 2: Context-Aware Retrieval

```python
# Find best matching memory for user query
best_match = selector.find_best_match(
    "alice",
    query_context={"keywords": ["python", "programming"]},
    threshold=0.5
)

if best_match:
    mem, score = best_match
    print(f"Relevant: {mem.content} (score={score:.3f})")
```

---

## 📂 File Structure

```
docs/
├── MEMORY_SCORING_GUIDE.md           # User guide (START HERE!)
├── API_REFERENCE_SCORING.md          # Complete API docs
├── SCORING_CHANGE_ANALYSIS.md        # Change impact template ⭐
├── SCORING_SAFE_DEVELOPMENT.md       # Dev workflow guide ⭐
├── SCORING_ARCHITECTURE.md           # Architecture (WIP)
├── SCORING_TESTING.md                # Testing guide (WIP)
└── SCORING_LIMITATIONS.md            # Known issues (WIP)

cnaa/
├── scoring.py                         # Data models (Type: str, float, datetime | None)
├── scoring_algorithms.py              # Algorithm implementations (O(1) complexity)
└── memory_selector.py                 # High-level API wrapper

cloud/storage/
└── scoring_backend.py                 # Service layer + persistence

tests/
└── test_scoring_system.py             # 27 unit tests covering all scenarios

examples/
└── memory_scoring_demo.py             # Complete working demonstrations
```

---

## 🔑 Key Concepts

### Core Architecture Principles

| Principle | Description | Why It Matters |
|-----------|-------------|----------------|
| **Modularity** | Each component is independent | Safe refactoring without breaking everything |
| **Type Safety** | All types explicitly annotated | Catch errors at compile-time, not runtime |
| **Backward Compatibility** | Default parameter values | Zero-breaking changes during development |
| **Graceful Degradation** | Fallback mechanisms | Partial failures don't crash entire system |

### Scoring Dimensions

Each memory gets 5 scores [0.0, 1.0]:

1. **Recency** (20% weight): Time decay - newer = higher
2. **Completion** (25% weight): Task progress - completed = higher  
3. **Importance** (30% weight): Keyword matching - critical = higher
4. **Frequency** (15% weight): Access count - frequently used = higher
5. **Relevance** (10% weight): Context match - query similarity = higher

**Composite Score** = Weighted sum of all dimensions

---

## 🛠️ Common Tasks

### Task 1: Add New Scoring Dimension

**Steps:**
1. Read [`Change Impact Analysis`](./SCORING_CHANGE_ANALYSIS.md) ✅ Pattern 1
2. Add field to `MemoryScores` (with default value!)
3. Create new Scorer class
4. Update `CompositeScorer.score_memory()`
5. Write tests
6. Run full test suite

**Expected time**: 2-3 hours  
**Risk level**: Medium  

### Task 2: Modify Default Weights

**Steps:**
1. Edit `scoring.py::_default_weights()`
2. Ensure weights sum to 1.0
3. Update documentation examples
4. Verify no tests broken

**Expected time**: 15 minutes  
**Risk level**: Low  

### Task 3: Extend Interface

**Steps:**
1. Add abstract method to `MemoryInterface`
2. Implement placeholder in base classes
3. All implementations must override
4. Compilation fails until complete! → Forces implementation

**Expected time**: 1-2 hours  
**Risk level**: Medium-High  

---

## 🧪 Running Tests

```bash
# All scoring tests
cd /root/CNAA-Cloud-Native-Agent-Architecture-
python3 -m pytest tests/test_scoring_system.py -v

# Specific test class
python3 -m pytest tests/test_scoring_system.py::TestMemoryScores -v

# With coverage
python3 -m pytest tests/test_scoring_system.py --cov=cnaa.scoring

# Demo script
python3 examples/memory_scoring_demo.py
```

**Acceptance criteria:**
- ✅ All 27 tests pass
- ✅ Coverage ≥ 95%
- ✅ Demo runs without errors

---

## 🔍 Troubleshooting

### Problem: Tests Fail After Code Change

**Solution:**
1. Check what broke: `pytest -v --tb=line`
2. Identify scope: Is it one module or cascading?
3. Revert last change if uncertain: `git revert HEAD`
4. Apply smaller fix incrementally

### Problem: Import Errors

**Solution:**
```bash
# Add project root to Python path
export PYTHONPATH="/root/CNAA-Cloud-Native-Agent-Architecture-:$PYTHONPATH"

# Or use python -m from project root
cd /root/CNAA-Cloud-Native-Agent-Architecture-
python3 -m tests.test_scoring_system
```

### Problem: Type Checking Warnings

**Solution:**
```bash
# Install mypy
pip install mypy

# Run type check
python3 -m mypy cnaa/scoring.py cnaa/scoring_algorithms.py

# Fix ALL warnings before committing
```

---

## 📈 Version History

### v1.0 (Current - 2026-08-02)

**Added:**
- Complete data structures (`MemoryScores`, `ScoreRanking`, `ScoreThresholds`)
- 5 algorithm implementations with O(1) complexity
- Batch scoring backend service
- High-level selector API
- 27 comprehensive tests
- Full API documentation

**Breaking changes:** None (backward compatible design)

**Known limitations:**
- String content requires conversion to dict format
- No vector embedding support yet
- Linear scan for list operations (could be optimized)

---

## 🤝 Contributing

When contributing to scoring system:

1. **Read first**: [`Safe Development Guidelines`](./SCORING_SAFE_DEVELOPMENT.md)
2. **Plan changes**: Use [`Change Impact Template`](./SCORING_CHANGE_ANALYSIS.md)
3. **Type everything**: Add complete type hints
4. **Test thoroughly**: Write comprehensive tests
5. **Document clearly**: Update all relevant docs
6. **Review carefully**: Peer review required
7. **Small commits**: Atomic, self-contained changes

### Code Style Rules

- ✅ Use `snake_case` for functions/variables
- ✅ Use `PascalCase` for classes/types
- ✅ Always include docstrings (NumPy style)
- ✅ Type annotate EVERYTHING
- ✅ Prefer clarity over cleverness
- ❌ Never remove existing type annotations
- ❌ Never create circular imports

---

## 🚨 Important Notices

### ⚠️ Active Development Warning

This system is actively evolving. Expect:
- New features added weekly
- Some APIs to be refined
- Breaking changes (with migration guides)
- Performance improvements

**Stay updated by:**
- Reading changelog regularly
- Subscribing to release announcements
- Regular pull requests before pushing

### ⚡ Critical Rule: Modular Independence

**NEVER modify more than 2 core files in a single commit.**

Why? Because it makes:
- Review easier ✅
- Testing simpler ✅
- Rollback faster ✅

**Good**: Modify `scoring_algorithms.py` → Commit → Then modify `scoring_backend.py` → Commit separately

**Bad**: Modify all 3 core files at once → Hope nothing breaks ❌

---

## 📞 Support & Contact

For questions or issues:
1. Read this documentation first
2. Check [`SCORING_SAFE_DEVELOPMENT.md`](./SCORING_SAFE_DEVELOPMENT.md)
3. Run failing test case
4. Open GitHub issue with minimal reproduction

---

## 📚 Related Documentation

- [CNAA Main Documentation](../README.md)
- [CNAA API Reference](../docs/api-reference-v0.1.md)
- [CNAA Architecture Vision](../docs/architecture.md)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Last updated**: 2026-08-02  
**Documentation version**: 1.0  
**System version**: 1.0  
**Maintenance status**: Active Development ⚠️

---

## 🎯 Next Steps

Choose your path:

**📖 Learning Path:**
1. Start with [Usage Guide](./MEMORY_SCORING_GUIDE.md)
2. Try examples in [Demo Script](../examples/memory_scoring_demo.py)
3. Deep dive into [API Reference](./API_REFERENCE_SCORING.md)

**🛠️ Developer Path:**
1. Read [Safe Development Guidelines](./SCORING_SAFE_DEVELOPMENT.md) ⭐
2. Study [Change Impact Analysis](./SCORING_CHANGE_ANALYSIS.md) ⭐
3. Follow the development workflow

**📐 Architecture Path:**
1. Understand [Core Concepts](#key-concepts)
2. Study [Module Dependencies](#file-structure)
3. Review [Version History](#version-history)

Pick your journey and get started! 🚀
