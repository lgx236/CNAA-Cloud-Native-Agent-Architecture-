# CNAA Memory Scoring - Safe Development Guidelines

> 🎯 **Goal**: Ensure safe, modular development during active development phase.
> 
> ⚡ **Key Principle**: Small changes, frequent commits, comprehensive tests = no global breaks!

---

## 🚀 Development Workflow

### ✅ Correct Flow (Safe)

```bash
1. Create feature branch
   git checkout -b feature/important-memory-rankings

2. Update documentation FIRST (before code)
   docs/API_REFERENCE_SCORING.md → Document new parameter types

3. Add type annotations to signatures
   cnaa/scoring.py: Add proper type hints

4. Write failing test (if new functionality)
   tests/test_scoring_system.py: New test case

5. Implement minimal fix to pass test

6. Run full test suite
   python3 -m pytest tests/test_scoring_system.py -v

7. If all green → Commit with detailed message

8. Push & open PR for review
```

### ❌ Dangerous Flow (Avoid!)

```bash
git checkout main
# Modify multiple files without testing
# Break dependencies between modules
# Large monolithic commit
# Hope tests pass...
```

---

## 🔒 Type Safety Checklist

Every public function/method MUST have complete type annotations:

### ✅ Required Pattern

```python
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime

def process_memory(
    memory_id: str,                     # Always explicit
    agent_id: str,                      # String identifiers
    optional_param: Optional[str] = None,  # Clear optionality
    list_param: List[int] = [],         # Container types explicit
    dict_param: Dict[str, float] = {},  # Generic parameters
    callback: Callable[[str], bool] = None  # Function types
) -> Dict[str, Any]:                  # Return type ALWAYS annotated
    """Docstring with Args and Returns sections."""
    ...
```

### ❌ Forbidden Patterns

```python
# BAD: Missing return type
def bad_function(param):  # No return type annotation!
    ...

# BAD: Implicit Any
def another_bad(data):  # Could be anything!
    ...

# BAD: Incomplete type hint
def third_bad(items: list):  # Should be list[T]
    ...
```

---

## 📦 Module Independence Rules

### Rule 1: Core Layer (`scoring.py`) Must NOT Import Algorithms

```python
# ✅ CORRECT: Pure data structures ONLY
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class MemoryScores:
    recency_score: float = 0.0
    # NO algorithm imports here!
```

```python
# ❌ WRONG: Creates circular dependency risk
from cnaa.scoring_algorithms import RecencyScorer  # DO NOT IMPORT!

@dataclass
class MemoryScores:
    scorer: RecencyScorer = None  # Don't couple data to logic!
```

### Rule 2: Algorithm Layer (`scoring_algorithms.py`) Depends Only on Data Models

```python
# ✅ CORRECT
from cnaa.scoring import MemoryScores  # Only imports from Level 0

class RecencyScorer:
    def score(self, timestamp: datetime) -> float:
        ...
```

```python
# ❌ WRONG
from cloud.storage.scoring_backend import MemoryScoringBackend  # Creates cycle!
```

### Rule 3: Backend Layer Uses Composition

```python
# ✅ CORRECT: Composes existing components
from cnaa.scoring import MemoryScores
from cnaa.scoring_algorithms import CompositeScorer

class MemoryScoringBackend:
    def __init__(self, scorer: CompositeScorer | None = None):
        self.scorer = scorer or CompositeScorer()  # Inject dependency
    
    def update_scores_for_memory(self, memory: Memory) -> MemoryScores:
        # Uses scorer as tool, not as base class
        ...
```

---

## 🧪 Testing Strategy

### Before Any Change

1. ✅ Run baseline tests:
```bash
python3 -m pytest tests/test_scoring_system.py::TestMemoryScores -v
python3 -m pytest tests/test_scoring_system.py::TestRecencyScorer -v
# ... all existing tests
```

2. ✅ Note current results (for regression detection)

### During Implementation

3. ✅ Test incrementally (every ~30 minutes of work):
```bash
python3 -m pytest tests/test_scoring_system.py -k "test_your_feature" -v
```

4. ✅ Fix failures immediately before continuing

### After Implementation

5. ✅ Full test suite:
```bash
python3 -m pytest tests/test_scoring_system.py -v --tb=short
```

6. ✅ Verify coverage unchanged:
```bash
python3 -m pytest tests/test_scoring_system.py --cov=cnaa.scoring
```

7. ✅ Integration test with demo:
```bash
python3 examples/memory_scoring_demo.py
```

---

## 🛠️ Refactoring Safely

### When Changing Data Structure

**Scenario**: Add new field to `MemoryScores`

**Safe approach:**
```python
@dataclass
class MemoryScores:
    memory_id: str
    agent_id: str
    
    # Existing fields...
    recency_score: float = 0.0
    
    # NEW: Always add with default value!
    quality_score: float = 0.0  # ← Default allows backward compat
    
    # Update serialization methods
    def to_dict(self) -> dict[str, Any]:
        return {
            ...,
            'quality': self.quality_score,  # Include in serialization
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryScores":
        return cls(
            ...,
            quality_score=data.get("quality", 0.0),  # ← Use .get() for old format
        )
```

**What this prevents:**
- ❌ Breaking existing JSON/data loaded from disk
- ❌ Failing tests that use old data format
- ❌ Crashes when loading historical scores

### When Modifying Algorithm

**Scenario**: Improve recency decay formula

**Safe approach:**
```python
class RecencyScorer:
    def score(self, timestamp: datetime | None) -> float:
        if timestamp is None:
            return 0.0
        
        now = datetime.now()
        age_seconds = (now - timestamp).total_seconds()
        
        if age_seconds < 0:
            return 1.0
        
        # OLD: Simple exponential decay
        # decay = math.exp(-self._decay_factor * age_seconds)
        
        # NEW: Enhanced decay WITH fallback
        try:
            decay = self._enhanced_decay(age_seconds)
        except Exception as e:
            # FAIL-SAFE: Log but continue with simple method
            print(f"⚠️ Enhanced decay failed: {e}")
            decay = math.exp(-self._decay_factor * age_seconds)
        
        return max(0.0, min(1.0, decay))
    
    def _enhanced_decay(self, age_seconds: float) -> float:
        """New enhanced decay calculation."""
        # Your improved algorithm here
        pass
```

**What this prevents:**
- ❌ Silent errors breaking user experience
- ❌ Hard-to-debug issues in production
- ❌ Complete scoring failure due to one edge case

---

## 📝 Commit Message Standards

### ✅ Good Format

```
Add importance weight configuration support

- Add weights parameter to CompositeScorer.__init__()
- Update _default_weights() method signature  
- Document in API reference docs
- Add unit tests for custom weights

Related issue: #123
Type safety: All methods have proper type hints
Tests: ✅ 5 new tests passing
```

### ❌ Bad Format

```
fixed scoring stuff
```

or

```
changed a lot of things
more tests added
```

---

## 🔍 Code Review Checklist

Reviewers MUST verify these items before approving:

### Type Safety (Critical)
- [ ] All public functions have complete type annotations
- [ ] Return types always specified (including `None`)
- [ ] Generic types used (List[T], Dict[K,V], Optional[T])
- [ ] Union types written as `A | B`, not `Union[A, B]`

### Documentation
- [ ] Every module has docstring explaining its purpose
- [ ] Every class has docstring describing responsibilities
- [ ] Every public method has NumPy-style docstring
- [ ] Examples included for complex APIs

### Modularity
- [ ] No circular imports (verify: `python3 -c "import your_module"`)
- [ ] Single Responsibility: each function does ONE thing
- [ ] Dependencies flow in one direction (Layer N depends only on N-1)
- [ ] No hidden global state access

### Testing
- [ ] Edge cases covered (None values, empty lists, extreme numbers)
- [ ] Error paths tested (exceptions, validation failures)
- [ ] Tests are deterministic (no randomness, no external dependencies)
- [ ] Tests run in reasonable time (< 1 second per test file)

### Backward Compatibility
- [ ] Added parameters have default values
- [ ] Removed/deprecated features marked clearly
- [ ] Old data formats still loadable (use `.get()` for optional fields)
- [ ] Version strings updated if API changed

---

## 🚨 Emergency Rollback Procedures

If change causes global breakage:

### Step 1: Identify Scope
```bash
# Check what broke
python3 -m pytest tests/test_scoring_system.py -v

# Find which test first failed
python3 -m pytest tests/test_scoring_system.py::TestYourFeature -v --tb=line
```

### Step 2: Revert Safely
```bash
# Option A: Revert single commit (if clean history)
git revert HEAD

# Option B: Checkout working version
git stash          # Save your changes
git checkout main  # Go back to stable
python3 -m pytest tests/test_scoring_system.py -v  # Verify recovery
git stash pop      # Retrieve your changes (for retry later)
```

### Step 3: Root Cause Analysis
After recovery, document:
- What broke?
- Why did it break?
- How to prevent next time?

---

## 🎯 Quality Gates

### Before Local Commit

```python
# ✅ Self-check script
echo "Running quality checks..."

# 1. Type checking
python3 -m mypy cnaa/scoring.py cnaa/scoring_algorithms.py

# 2. Test suite
python3 -m pytest tests/test_scoring_system.py -v

# 3. Demo runs successfully
python3 examples/memory_scoring_demo.py

# If any fail → DO NOT COMMIT
```

### Before Push to Remote

```python
# ✅ Gate check
echo "Pre-push verification..."

# 1. Sync with main
git pull origin main

# 2. Resolve conflicts
# (edit files to merge changes)

# 3. Re-run tests
python3 -m pytest tests/test_scoring_system.py -v

# 4. Verify demo
python3 examples/memory_scoring_demo.py

# 5. Push
git push origin feature/branch-name
```

---

## 🔄 Continuous Integration Triggers

Automated checks happen on:
- **Push to feature branch**: Run tests, type checking
- **Pull Request created**: Full test suite + linting
- **PR merged to main**: Integration tests + demo validation

### CI Configuration

`.github/workflows/test-scoring.yml`:

```yaml
name: Scoring System Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -e .
      - name: Run tests
        run: python3 -m pytest tests/test_scoring_system.py -v
      - name: Run demo
        run: python3 examples/memory_scoring_demo.py
```

---

## 📊 Monitoring Metrics

Track these metrics to detect problems early:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Test pass rate | 100% | < 95% |
| Code coverage | ≥ 95% | < 90% |
| Build time | < 5s | > 10s |
| Demo runtime | < 10ms total | > 50ms |
| Type errors | 0 | > 0 |

Set up alerts if any metric crosses threshold!

---

## 🎓 Best Practices Summary

### DO ✅

- Type everything explicitly
- Write tests BEFORE implementing
- Document every public interface
- Commit frequently with small changes
- Run full test suite after ANY change
- Use semantic commit messages
- Keep dependencies one-way (no cycles)
- Fail fast with clear error messages

### DON'T ❌

- Skip type annotations "to save time"
- Write code without tests
- Remove existing tests to make new code pass
- Make large monolithic changes
- Commit broken builds
- Ignore CI warnings
- Create circular dependencies
- Silently ignore None values

---

## 🌟 Success Stories

### Case Study 1: Safe Addition of Frequency Dimension

**Problem**: Needed to track access frequency without breaking existing system

**Solution:**
1. ✅ Added `frequency_score: float = 0.0` to `MemoryScores` (with default!)
2. ✅ Created `FrequencyScorer` class (new file, no modified files)
3. ✅ Updated `CompositeScorer` to call new scorer
4. ✅ Added 3 unit tests
5. ✅ Verified all 27 existing tests still pass

**Result**: ✅ Zero breaking changes, seamless integration

### Case Study 2: Breaking Change Avoided

**Problem**: Needed to change `importance_score` calculation algorithm

**Initial Approach**: Change formula directly
**Risk**: Would break serialized scores from disk

**Safe Approach**: 
1. Add `importance_v2_score: float = 0.0` field
2. Calculate both versions separately
3. Deprecate old field with warning
4. Migrate users over multiple releases

**Result**: ✅ Improved algorithm, no breaking changes

---

## 🚦 Quick Reference

### Before You Code

- [ ] Read impact analysis document
- [ ] Check dependency map
- [ ] Write down affected modules
- [ ] Plan rollback strategy

### During Development

- [ ] Test every 30 minutes
- [ ] Check type hints are complete
- [ ] Update docs as you go
- [ ] Avoid modifying more than 2 core files

### Before Committing

- [ ] Run `python3 -m pytest tests/test_scoring_system.py -v`
- [ ] Verify demo works
- [ ] Check for type errors
- [ ] Write meaningful commit message

### Before Pushing

- [ ] Pull latest main
- [ ] Merge conflicts
- [ ] Re-run tests
- [ ] Get peer review

---

**Remember**: Slow is smooth, smooth is fast! 🐢→🐇

**Last updated**: 2026-08-02  
**Status**: Active Development Protocol ⚠️
