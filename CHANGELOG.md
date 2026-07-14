# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-14

### V1.0 Frozen — Python MVP

> **V1.0 is frozen. No core logic changes will be accepted.** All new development targets V2.0 (MCP + LangGraph).

### Features

- **9-Stage Diagnostic Pipeline**: Complete pipeline from user profile to actionable suggestions
- **AIVO Scoring System**: 4-dimension × 25% weighted scoring (0-100)
- **Auto Competitor Benchmarking**: LLM semantic identification + default category fallback
- **Dual-Track Delivery**: JSON structured data + HTML visual report
- **Multi-LLM Backend**: Kimi (moonshot-v1) + Doubao (Seed series) + OpenAI compatible
- **JSON Repair Tool**: Auto-fix Chinese quotes, unescaped characters, trailing commas
- **Graceful Degradation**: Every stage can fail without breaking the pipeline

### Technical Highlights

- 11 sub-agents generated 9 stage modules + 2 utility modules in parallel
- 10 bugs fixed during integration testing (see MEMORY.md)
- 74/100 AIVO score achieved on first test run (Brand: 听力熊 / Tinglixiong)
- Design system upgraded to refer_1 specification (light theme, semantic tokens)

### Known Limitations (V1.0)

- **Slow AI search**: Doubao `doubao-seed-evolving` deep-thinking model takes 15-25s per query, total ~60-120s
- **Simulated search data**: Stages 4 (AI search) and 6 (sentiment) rely on LLM simulation — no real search API connected yet
- **Single platform support**: Only Doubao is fully implemented; ChatGPT/Perplexity stubs exist but not tested
- **No test coverage**: Zero unit/integration tests
- **No deployment**: Local script only, no web service
- **Estimated competitor scores**: Competitor AIVO scores are LLM estimates, not real measurements

### Documentation

- PRD (Product Requirements Document)
- Implementation Plan (Vibe Coding approach)
- VibeCoding Course Gap Analysis (43% course coverage)
- AI Agent Working Guide (AGENTS.md)
- Project Memory (MEMORY.md) — 10 bug fixes with root cause analysis

---

## [Unreleased] — V2.0 Planning

### Planned Features

- **MCP Tool Integration**: Wrap API calls in MCP protocol (modelcontextprotocol.io)
- **LLM LOOP**: Thinking → Call → Observe → Re-think cycle for autonomous decisions
- **LangGraph Orchestration**: Replace fixed pipeline with conditional edges and loops
- **Real Search APIs**: SerpAPI / Bing Search integration for authentic data
- **FastAPI Web Service**: REST API + async task queue
- **pytest Testing**: Full stage coverage
- **RAG Vector Database**: ChromaDB + embedding for knowledge base
- **Vercel Deployment**: Public web service with landing page

### Course Mapping

| V2.0 Feature | VibeCoding Course Module | Priority |
|-------------|------------------------|----------|
| MCP + LLM LOOP | DAY-02: AI Tool Calling | 🔴 P0 |
| LangGraph | DAY-04: Autonomous Agent | 🔴 P0 |
| FastAPI + Deploy | DAY-01: Prototype to Production | 🟡 P1 |
| pytest + RAG | DAY-03: Engineering Practices | 🟡 P1 |

---

[1.0.0]: https://github.com/zhongwentuo-creator/geo-visibility-diagnostician/releases/tag/v1.0.0
