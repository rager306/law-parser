# LDUP v4 Self-Improvement Protocol

**Goal:** Automatic error detection → rule generation → validation → activation with **safety rails**.

---

## Overview

```
Runtime Execution → Error Detection → Feedback Collection → Policy Optimization
                                                         ↓
                                           Rule Generation (Pydantic)
                                                         ↓
                                           Validation & Simulation
                                                         ↓
                                           Safety Rails Check
                                                         ↓
                                           Activation → Recompile Trigger
```

---

## 1. Error Detection (SRC/TRC/STC Controllers)

### Structural Controller (STC)

**Detects:**
- Orphan nodes (article without parent chapter)
- Missing hierarchy (clause outside part)
- Broken numbering (non-sequential article numbers)

```python
from loguru import logger
from pydantic import BaseModel

class StructuralError(BaseModel):
    error_type: str
    article_id: str
    text_fragment: str
    expected: str
    actual: str
    confidence: float

def detect_structural_issues(document: LegalDocument) -> list[StructuralError]:
    errors = []

    for article in document.structure.articles:
        # Check 1: Orphan article
        if article.parent_chapter is None:
            error = StructuralError(
                error_type="orphan_article",
                article_id=article.id,
                text_fragment=article.text[:100],
                expected="parent_chapter != None",
                actual="parent_chapter == None",
                confidence=1.0
            )
            errors.append(error)
            logger.bind(
                document_id=document.id,
                article_id=article.id
            ).warning("STC: Orphan article detected")

        # Check 2: Non-sequential numbering
        if article.previous_article and int(article.number) != int(article.previous_article.number) + 1:
            error = StructuralError(
                error_type="non_sequential_numbering",
                article_id=article.id,
                text_fragment=f"Статья {article.number}",
                expected=f"Статья {int(article.previous_article.number) + 1}",
                actual=f"Статья {article.number}",
                confidence=0.9
            )
            errors.append(error)
            logger.bind(
                document_id=document.id,
                article_id=article.id,
                expected_number=int(article.previous_article.number) + 1,
                actual_number=int(article.number)
            ).warning("STC: Non-sequential numbering")

    return errors
```

### Semantic Controller (SRC)

**Detects:**
- Misclassified modality (permission vs prohibition)
- Double negatives (запрещается не → should be prohibition_strong)
- Lost definitions (definition not extracted)

```python
class SemanticError(BaseModel):
    error_type: str
    article_id: str
    text_fragment: str
    predicted: str
    expected: str
    confidence: float

def detect_semantic_issues(document: LegalDocument) -> list[SemanticError]:
    errors = []

    for semantic in document.semantics:
        # Check 1: Double negative misclassification
        if "не " in semantic.text.lower() and semantic.text.lower().count("не") >= 2:
            if semantic.modality not in ["prohibition_strong", "obligation_strong"]:
                error = SemanticError(
                    error_type="double_negation_misclassification",
                    article_id=semantic.article_id,
                    text_fragment=semantic.text[:100],
                    predicted=semantic.modality,
                    expected="prohibition_strong" if "запрещ" in semantic.text.lower() else "obligation_strong",
                    confidence=0.88
                )
                errors.append(error)
                logger.bind(
                    document_id=document.id,
                    article_id=semantic.article_id,
                    predicted=semantic.modality
                ).warning("SRC: Double negative not strengthened")

        # Check 2: Permission/prohibition confusion
        if "запрещается" in semantic.text.lower() and semantic.modality == "permission":
            error = SemanticError(
                error_type="modality_misclassification",
                article_id=semantic.article_id,
                text_fragment=semantic.text[:100],
                predicted="permission",
                expected="prohibition",
                confidence=0.95
            )
            errors.append(error)
            logger.bind(
                document_id=document.id,
                article_id=semantic.article_id
            ).warning("SRC: Prohibition misclassified as permission")

    return errors
```

### Temporal Controller (TRC)

**Detects:**
- Invalid intervals (valid_from >= valid_to)
- Missing effective_date
- Competing revisions (same article, overlapping intervals)

```python
class TemporalError(BaseModel):
    error_type: str
    article_id: str
    text_fragment: str
    expected: str
    actual: str
    confidence: float

def detect_temporal_issues(document: LegalDocument) -> list[TemporalError]:
    errors = []

    for temporal in document.temporals:
        # Check 1: Invalid interval
        if temporal.valid_from and temporal.valid_to and temporal.valid_from >= temporal.valid_to:
            error = TemporalError(
                error_type="invalid_interval",
                article_id=temporal.article_id,
                text_fragment=temporal.text[:100],
                expected="valid_from < valid_to",
                actual=f"valid_from={temporal.valid_from} >= valid_to={temporal.valid_to}",
                confidence=1.0
            )
            errors.append(error)
            logger.bind(
                document_id=document.id,
                article_id=temporal.article_id,
                valid_from=temporal.valid_from,
                valid_to=temporal.valid_to
            ).error("TRC: Invalid temporal interval")

        # Check 2: Missing effective_date
        if not temporal.effective_date:
            error = TemporalError(
                error_type="missing_effective_date",
                article_id=temporal.article_id,
                text_fragment=temporal.text[:100],
                expected="effective_date != None",
                actual="effective_date == None",
                confidence=0.7
            )
            errors.append(error)
            logger.bind(
                document_id=document.id,
                article_id=temporal.article_id
            ).warning("TRC: Missing effective date")

    return errors
```

---

## 2. Feedback Collection

### Feedback JSONL Format

```python
from pydantic import BaseModel
from datetime import datetime, timezone

class FeedbackEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    document_id: str
    error_type: str  # structural/semantic/temporal
    module: str  # gepa/simba/miprov2/custom
    text_fragment: str
    expected: str
    predicted: str
    confidence: float
    source_id: str  # consultantplus/garant/raw
    example_fragment: str  # For debugging

# Example feedback
feedback = FeedbackEntry(
    document_id="doc-123",
    error_type="semantic_misclassification",
    module="simba",
    text_fragment="запрещается не курить",
    expected="prohibition_strong",
    predicted="permission",
    confidence=0.88,
    source_id="consultantplus_xml",
    example_fragment="Статья 33, часть 1, пункт 1"
)

# Append to feedback queue
feedback_queue.put(feedback)
```

---

## 3. Policy Optimizer

### Prioritization Strategy

```python
from collections import defaultdict
from typing import List

class PolicyOptimizer:
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_impact = defaultdict(float)  # ΔAccuracy if fixed

    def prioritize(self, feedback_batch: List[FeedbackEntry]) -> List[FeedbackEntry]:
        """Prioritize by error frequency × impact."""
        # Count errors by type
        for feedback in feedback_batch:
            self.error_counts[feedback.error_type] += 1

        # Calculate priority scores
        scored_feedback = []
        for feedback in feedback_batch:
            frequency = self.error_counts[feedback.error_type]
            impact = self.estimate_impact(feedback)
            score = frequency * impact
            scored_feedback.append((feedback, score))

        # Sort by score descending
        scored_feedback.sort(key=lambda x: x[1], reverse=True)

        logger.bind(
            batch_size=len(feedback_batch),
            unique_errors=len(self.error_counts),
            top_score=scored_feedback[0][1] if scored_feedback else 0
        ).info("Policy optimization complete")

        return [fb for fb, score in scored_feedback]

    def estimate_impact(self, feedback: FeedbackEntry) -> float:
        """Estimate accuracy impact if this error is fixed."""
        if feedback.error_type == "structural":
            return 0.1  # Structural errors have high impact
        elif feedback.error_type == "semantic":
            return 0.05  # Semantic errors have medium impact
        elif feedback.error_type == "temporal":
            return 0.03  # Temporal errors have lower impact
        return 0.01  # Default
```

---

## 4. Rule Generation (Pydantic)

### Candidate Rule Creation

```python
from pydantic import BaseModel, Field

class CandidateRule(BaseModel):
    rule_id: str = Field(..., description="Unique identifier")
    pattern: str
    rule_type: Literal["structural", "semantic", "temporal"]
    priority: int = Field(ge=0, le=10)
    source_type: Literal["consultantplus", "garant", "raw"]
    rationale: str
    status: Literal["pending", "active", "archived"] = "pending"
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)

def generate_candidate_rule(feedback: FeedbackEntry) -> CandidateRule:
    """Generate Pydantic rule from feedback."""
    if feedback.error_type == "semantic_misclassification":
        if "double_negation" in feedback.example_fragment.lower():
            return CandidateRule(
                rule_id=f"semantic_double_negation_{hash(feedback.text_fragment)}",
                pattern=r"запрещается не|разрешается не",
                rule_type="semantic",
                priority=8,
                source_type=feedback.source_id,
                rationale="Double negation strengthens the modality",
                status="pending"
            )

    elif feedback.error_type == "temporal_invalid_interval":
        return CandidateRule(
            rule_id=f"temporal_interval_correction_{hash(feedback.text_fragment)}",
            pattern=r"действует с (\d{2}\.\d{2}\.\d{4})",
            rule_type="temporal",
            priority=7,
            source_type=feedback.source_id,
            rationale="Extract effective date to establish valid_from",
            status="pending"
        )

    # Default: generic rule
    return CandidateRule(
        rule_id=f"generic_{hash(feedback.text_fragment)}",
        pattern=feedback.text_fragment[:50],
        rule_type="structural",
        priority=5,
        source_type=feedback.source_id,
        rationale=feedback.text_fragment,
        status="pending"
    )
```

---

## 5. Validation & Simulation

### Schema Validation

```python
def validate_candidate_rule(rule: CandidateRule) -> bool:
    """Validate rule with Pydantic."""
    try:
        validated_rule = rule.model_validate(rule)
        logger.bind(rule_id=rule.rule_id).info("Rule validation passed")
        return True
    except ValidationError as e:
        logger.bind(
            rule_id=rule.rule_id,
            errors=e.errors()
        ).error("Rule validation failed")
        return False
```

### Mini-Corpus Simulation

```python
def simulate_on_mini_corpus(rule: CandidateRule, corpus_size: int = 20) -> float:
    """Test rule on mini-corpus to estimate accuracy."""
    # Load mini-corpus
    mini_corpus = load_validation_set(n=corpus_size)

    # Apply rule and measure accuracy
    correct = 0
    total = 0

    for doc in mini_corpus:
        # Parse with rule
        result = parse_with_rule(doc, rule)

        # Validate result
        if is_valid(result):
            correct += 1
        total += 1

    accuracy = correct / total if total > 0 else 0.0

    logger.bind(
        rule_id=rule.rule_id,
        corpus_size=corpus_size,
        correct=correct,
        accuracy=accuracy
    ).info("Simulation complete")

    return accuracy
```

---

## 6. Safety Rails

### Configuration

```python
# Safety limits
MAX_ITERATIONS = 10  # Maximum self-improvement iterations
MIN_IMPROVEMENT_THRESHOLD = 0.01  # 1% minimum accuracy gain
MAX_ACCURACY_DROP = 0.05  # 5% maximum accuracy drop (circuit breaker)
MIN_CORPUS_SIZE = 10  # Minimum validation set size
ROLLBACK_ENABLED = True  # Enable rollback on failure
```

### Safety Check Function

```python
from loguru import logger
from typing import Optional

def check_safety_rails(
    current_accuracy: float,
    baseline_accuracy: float,
    iteration: int,
    new_accuracy: Optional[float] = None
) -> tuple[bool, str]:
    """
    Check if self-improvement should continue.

    Returns:
        (should_continue, reason)
    """

    # Check 1: Max iterations
    if iteration >= MAX_ITERATIONS:
        logger.info(
            f"Max iterations reached ({MAX_ITERATIONS}), stopping self-improvement"
        )
        return False, "max_iterations"

    # Check 2: Convergence (if new accuracy provided)
    if new_accuracy is not None:
        improvement = new_accuracy - current_accuracy

        if improvement < MIN_IMPROVEMENT_THRESHOLD:
            logger.info(
                f"Converged: improvement ({improvement:.4f}) below threshold ({MIN_IMPROVEMENT_THRESHOLD})"
            )
            return False, "converged"

        # Check 3: Circuit breaker (accuracy drop)
        if new_accuracy < baseline_accuracy * (1 - MAX_ACCURACY_DROP):
            logger.warning(
                f"Accuracy dropped >{MAX_ACCURACY_DROP*100}% "
                f"(baseline={baseline_accuracy:.4f}, new={new_accuracy:.4f}), "
                f"triggering circuit breaker"
            )
            return False, "circuit_breaker"

    return True, "ok"
```

### Rollback Mechanism

```python
import shutil
from pathlib import Path
from datetime import datetime

class RollbackManager:
    def __init__(self, rule_store_path: Path):
        self.rule_store_path = rule_store_path
        self.backup_dir = rule_store_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def backup(self) -> Path:
        """Create backup of current rule store."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"rule_store_{timestamp}.pkl"
        shutil.copy2(self.rule_store_path, backup_path)
        logger.bind(backup_path=backup_path).info("Rule store backup created")
        return backup_path

    def rollback(self, backup_path: Path) -> None:
        """Rollback to backup."""
        shutil.copy2(backup_path, self.rule_store_path)
        logger.bind(backup_path=backup_path).info("Rollback completed")

    def list_backups(self) -> list[Path]:
        """List available backups."""
        return sorted(self.backup_dir.glob("rule_store_*.pkl"), reverse=True)

# Usage
rollback_manager = RollbackManager(Path("data/rule_store.pkl"))

# Before applying new rules
backup_path = rollback_manager.backup()

# If safety rails trigger circuit breaker
if not safe_to_apply:
    rollback_manager.rollback(backup_path)
```

---

## 7. Main Self-Improvement Loop

```python
def self_improvement_loop(
    feedback_queue: FeedbackQueue,
    rule_store: RuleStore,
    baseline_accuracy: float
) -> None:
    """Main self-improvement loop with safety rails."""

    current_accuracy = baseline_accuracy
    rollback_manager = RollbackManager(Path("data/rule_store.pkl"))

    for iteration in range(MAX_ITERATIONS):
        logger.bind(iteration=iteration).info("Starting self-improvement iteration")

        # 1. Collect feedback batch
        feedback_batch = feedback_queue.get_batch(min_size=10)
        if not feedback_batch:
            logger.info("No feedback available, stopping")
            break

        # 2. Prioritize errors
        prioritized = policy_optimizer.prioritize(feedback_batch)

        # 3. Generate candidate rules
        candidate_rules = [generate_candidate_rule(fb) for fb in prioritized]

        # 4. Validate rules
        valid_rules = [r for r in candidate_rules if validate_candidate_rule(r)]

        # 5. Simulate on mini-corpus
        for rule in valid_rules:
            rule.accuracy = simulate_on_mini_corpus(rule)

        # 6. Select best rule
        best_rule = max(valid_rules, key=lambda r: r.accuracy or 0.0)

        # 7. Backup current state
        backup_path = rollback_manager.backup()

        # 8. Check safety rails
        should_continue, reason = check_safety_rails(
            current_accuracy=current_accuracy,
            baseline_accuracy=baseline_accuracy,
            iteration=iteration,
            new_accuracy=best_rule.accuracy
        )

        if not should_continue:
            logger.bind(reason=reason).warning("Self-improvement stopped by safety rails")
            if reason == "circuit_breaker":
                rollback_manager.rollback(backup_path)
            break

        # 9. Apply rule
        rule_store.add_rule(best_rule, metadata=RuleMetadata(...))
        current_accuracy = best_rule.accuracy

        logger.bind(
            iteration=iteration,
            rule_id=best_rule.rule_id,
            accuracy=current_accuracy
        ).info("Rule applied successfully")

    # 10. Trigger recompile if enough rules accumulated
    if rule_store.count_active() % 10 == 0:
        logger.info("Rule batch threshold reached, triggering recompile")
        trigger_compile_time_optimization()
```

---

## 8. Recompile Trigger

```python
def trigger_compile_time_optimization() -> None:
    """Trigger new compile-time optimization run."""
    logger.info("Triggering compile-time optimization")

    # Signal to optimizer daemon
    with open("cache/recompile_trigger", "w") as f:
        f.write("triggered")

    # Alternatively: Send message to optimizer service
    # requests.post("http://optimizer:8000/trigger")
```

---

## Monitoring Self-Improvement

### Metrics to Track

```python
# Metrics to expose
metrics = {
    "self_improvement_iterations_total": 0,
    "rules_generated_total": 0,
    "rules_activated_total": 0,
    "rules_rolled_back_total": 0,
    "accuracy_baseline": baseline_accuracy,
    "accuracy_current": current_accuracy,
    "circuit_breaker_trips_total": 0,
}

# Log metrics periodically
logger.bind(metrics=metrics).info("Self-improvement metrics")
```

---

## Best Practices

### DO ✅
- Use safety rails (max iterations, convergence, circuit breaker)
- Backup rule store before applying changes
- Validate rules with Pydantic before activation
- Test on mini-corpus (not just 1 document)
- Log all decisions for audit trail

### DON'T ❌
- Don't apply rules without validation
- Don't skip safety rails for "quick fixes"
- Don't allow self-improvement to run unbounded
- Don't ignore circuit breaker triggers
- Don't lose audit trail (what rule, when, why)

---

## References

- DSPy optimizers: https://github.com/stanfordnlp/dspy
- Pydantic validation: https://docs.pydantic.dev
- adaptix serialization: https://adaptix.readthedocs.io
