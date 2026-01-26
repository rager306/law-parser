# LDUP v4 Architecture

## Overview

LDUP v4 is a **self-improving legal document parser** built on **DSPy 3.1** with compile-time optimization and runtime safety rails. It processes Russian federal laws (44-FZ, etc.) into structured semantic graphs with automatic error correction and policy optimization.

## Key Changes vs v3

| Change | Reason | Impact |
|--------|--------|--------|
| **DSPy 3.0.4 → 3.1** | Latest version with bug fixes in optimizer compilation | Better stability, improved cache semantics |
| **YAML → Pydantic + adaptix** | YAML has weak typing, whitespace fragility, no tooling | Type safety, IDE autocomplete, runtime validation, 2-10x faster serialization |
| **Add loguru** | No observability in v3 makes debugging impossible | Structured logging, exception tracking, production monitoring |
| **Add hypothesis** | No testing strategy in v3 leads to edge cases in production | Property-based testing catches bugs unit tests miss |
| **Compile/Runtime separation** | v3 incorrectly showed GEPA/SIMBA/MiPROv2 as runtime components | Accurate architecture: optimizers are compile-time only |
| **Safety rails** | Self-improvement can propagate errors indefinitely | Rollback, circuit-breaker, convergence criteria prevent cascading failures |

## Architecture Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPILE TIME (Once)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GEPA/SIMBA/MiPROv2 optimize DSPy prompts               │  │
│  │  + Pydantic validates rules + adaptix serializes        │  │
│  │  → Compiled DSPy Graph (.pkl)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RUNTIME (Per Document)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Load compiled graph + Parse document                    │  │
│  │  + loguru traces execution + Validators check           │  │
│  │  + hypothesis tests properties                           │  │
│  │  → Export + Feedback to self-improvement                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Documentation Structure

| Document | Purpose |
|----------|---------|
| **architecture.md** | Core components, compile/runtime separation |
| **workflow.md** | Execution flow (2-phase) + self-improvement loop |
| **testing.md** | Testing strategy (hypothesis + unit + integration) |
| **observability.md** | Logging with loguru + metrics |
| **serialization.md** | Pydantic + adaptix for rules |
| **self_improvement.md** | Self-improvement protocol with safety rails |
| **mermaid.md** | Visual diagrams (updated for v4) |
| **CHANGELOG.md** | Detailed reasons for each change vs v3 |

## Quick Start

1. **Understand the architecture**: Read `architecture.md` for components
2. **Follow the flow**: Read `workflow.md` for compile/runtime phases
3. **Testing**: Read `testing.md` for hypothesis strategy
4. **Observability**: Read `observability.md` for logging setup
5. **Serialization**: Read `serialization.md` for Pydantic/adaptix usage
6. **Self-improvement**: Read `self_improvement.md` for safety rails
7. **Visuals**: See `mermaid.md` for diagrams

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | DSPy | 3.1 | LLM orchestration, prompt optimization |
| **Validation** | Pydantic | 2.x | Type-safe rule definitions |
| **Serialization** | adaptix | 1.x | Fast (2-10x) serialization for hot paths |
| **Logging** | loguru | 0.7+ | Structured logging with rotation |
| **Testing** | hypothesis | 6.x+ | Property-based testing |
| **Graph Storage** | FalkorDB/Graphiti | - | Semantic graph persistence |
| **Export Formats** | Akoma Ntoso, LegalDocML-RU | - | Standard legal XML formats |

## Critical Fixes from v3

### 1. Compile-Time vs Runtime Separation
- **Problem v3**: GEPA/SIMBA/MiPROv2 shown as runtime components
- **Fix v4**: Clear 2-phase architecture with optimizers at compile-time only

### 2. Type Safety
- **Problem v3**: YAML has weak typing, no validation until runtime
- **Fix v4**: Pydantic BaseModel for rules + adaptix for fast serialization

### 3. Testing Strategy
- **Problem v3**: No testing defined
- **Fix v4**: hypothesis for property-based testing + unit/integration tests

### 4. Observability
- **Problem v3**: No logging, impossible to debug production issues
- **Fix v4**: loguru for structured logging with levels, rotation, metrics

### 5. Safety Rails
- **Problem v3**: Self-improvement can propagate errors indefinitely
- **Fix v4**: Max iterations, rollback, circuit-breaker, convergence criteria

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v4 | 2026-01-18 | Pydantic + adaptix, loguru, hypothesis, safety rails |
| v3 | 2026-01-17 | Self-improvement restored (with YAML issues) |
| v1 | 2026-01-16 | Original self-improving architecture |
