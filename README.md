# GEO Visibility Diagnostician — V1.0 Engine + V1.5 Web Experience

> Quantify a brand's "digital presence" in the AI-native era and provide actionable optimization paths.
>
> **Current status**: V1.0 nine-stage engine is frozen; V1.5 is live on Render and has passed public real-brand, cross-device and 24-hour stability acceptance.

[中文版本](README.zh.md) | [V1.5 Web README](v1.5/README.md) | [Node 5 execution](v1.5/docs/NODE5_EXECUTION.md) | [V1.5 delivery plan](v1.5/docs/plan.md) | [V1.5 node records](v1.5/docs/PROJECT_NODE_RECORDS.md) | [VibeCoding acceptance matrix](docs/VIBECODING_ACCEPTANCE_MATRIX.md)

---

## Current repository map

| Scope | Location | Status |
|---|---|---|
| V1.0 diagnostic engine | Repository root: `main.py`, `stages/`, `utils/`, `report/` | Frozen; reused by V1.5 without changing diagnostic algorithms. |
| V1.5 Web experience | `v1.5/` | Merged to `main`; FastAPI, SSE, conversational UI, tests, Docker and Render configuration are ready. |
| V1.5 node execution | `v1.5/docs/NODE4_EXECUTION.md`, `v1.5/docs/NODE5_EXECUTION.md` | Historical SSE repair plus completed cross-device and stability evidence. |
| V1.5 release evidence | `v1.5/docs/plan.md`, `v1.5/docs/ACCEPTANCE.md`, `v1.5/docs/PROJECT_NODE_RECORDS.md` | Public release acceptance passed. |
| Project governance | `AGENTS.md`, `MEMORY.md`, `v1.5/docs/ISSUE_BACKLOG.md`, `v1.5/docs/SDD.md` | Rules, stable decisions, known limitations and V1.5 traceability. |

The V1.5 release was merged through PR #1 (`21918de`) after four GitHub checks passed. It is source release evidence, not proof of public deployment.

---

## What is GEO?

**GEO** = **G**enerative **E**ngine **O**ptimization — the evolution of SEO in the AI-native era.

While SEO optimizes for search engine ranking, GEO optimizes for **AI platforms' citation and recommendation of your brand**.

| Dimension | SEO | GEO |
|-----------|-----|-----|
| **Goal** | Webpage ranking in search results | Brand information cited in AI answers |
| **Assessment** | Keywords, traffic, CTR | AI mention rate, recommendation position, context |
| **Content** | Webpage content, Meta tags | Structured data, authoritative media, user reviews |
| **Competition** | Compete with other pages | Compete with "cognitive density" of competing brands in AI training data |

> **Why now?** As AI search platforms (ChatGPT, Doubao, Perplexity) surpass 100M+ DAU, user journeys are shifting from "search → click webpage" to "ask AI → get summary answer." Brands invisible in AI answers are effectively missing from the first page of the next era.

---

## Features

- **9-Stage Diagnostic Pipeline**: User Profile → Infra Evaluation → Competitor Analysis → AI Search Test → GEO Effect Summary → Sentiment Scan → Overview → AIVO Score → Suggestion System
- **AIVO Scoring System**: 4 dimensions (AI Search Visibility / Infra Completeness / Competitive Advantage / Sentiment Health) × 25% weight, 0-100 quantitative score
- **Auto Competitor Benchmarking**: Identifies 3-5 industry competitors, runs parallel diagnostics
- **Dual-Track Delivery**: JSON structured data (for BI integration) + HTML visual report (for direct presentation)
- **Actionable Recommendations**: Priority action list + Quick Wins + 3-phase roadmap (P1 Immediate / P2 Short-term / P3 Long-term)

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/zhongwentuo-creator/geo-visibility-diagnosticia.git
cd geo-visibility-diagnosticia
```

### 2. Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required:**
- `KIMI_API_KEY`: For LLM reasoning (Stages 1/3/7/9)
- `DOUBAO_API_KEY`: For AI search testing (Stage 4)

**Optional:**
- `SERPAPI_KEY` / `BING_SEARCH_KEY`: For real-time sentiment scraping (Stage 6)
- `OPENAI_API_KEY`: Alternative LLM backend

### 5. Run Diagnosis

```bash
python main.py --brand "Tinglixiong" --category "Children\'s AI Companion" --platform doubao
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--brand` | Yes | Brand name |
| `--category` | Yes | Product category |
| `--website` | No | Official website (improves infra evaluation) |
| `--platform` | No | Diagnosis platform (default: `doubao`, options: `chatgpt` / `perplexity`) |

### 6. View Report

```bash
open output/*/Tinglixiong_doubao_*-GEO-Diagnosis-Report.html  # macOS
start output/*/Tinglixiong_doubao_*-GEO-Diagnosis-Report.html  # Windows
```

---

## Project Structure

```
geo-visibility-diagnostician/
├── main.py                  # Entry point: 9-stage pipeline orchestration
├── config.py                # Configuration management (pydantic-settings + .env)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template (no secrets)
├── .gitignore               # Git exclusion rules
├── stages/                  # 9-stage diagnostic pipeline
│   ├── s1_user_profile.py   # Stage 1: User profile construction
│   ├── s2_infra_eval.py     # Stage 2: Infrastructure evaluation
│   ├── s3_competitor.py     # Stage 3: Competitor analysis
│   ├── s4_ai_search.py      # Stage 4: AI search scenario testing
│   ├── s5_geo_effect.py     # Stage 5: GEO effect summary
│   ├── s6_sentiment.py      # Stage 6: Sentiment scan
│   ├── s7_overview.py       # Stage 7: Comprehensive overview
│   ├── s8_aivo_score.py     # Stage 8: AIVO scoring
│   └── s9_suggestion.py     # Stage 9: Suggestion system
├── utils/                   # Utility modules
│   ├── api_client.py        # API gateway (Kimi + Doubao + OpenAI compatibility)
│   └── json_repair.py       # JSON repair tool (Chinese quotes, escapes, trailing commas)
├── report/                  # Report templates
│   └── template.html        # Jinja2 HTML visual report template (CSS/SVG inline)
├── output/                  # Auto-generated output directory
│   ├── {brand}_{platform}_diag-report.json
│   └── {brand}_{platform}_GEO-Diagnosis-Report.html
├── docs/                    # Documentation
│   ├── IMPLEMENTATION.md    # Vibe Coding Implementation Plan
│   └── COURSE_GAP_ANALYSIS.md # VibeCoding Course Gap Review
├── GEO可见度诊断师_V1.0_PRD.md  # Product Requirements Document (V1.0)
├── AGENTS.md                # AI Agent working guide
├── MEMORY.md                # Project memory (bug fixes, tuning records)
└── README.zh.md             # Chinese version of this README
```

---

## AIVO Scoring System

**AIVO** = **AI** **V**isibility & **O**ptimization

| Dimension | Weight | Code | Data Source | Description |
|-----------|--------|------|-------------|-------------|
| AI Search Visibility | 25% | `AI_SEARCH_VISIBILITY` | Stage 4 | Brand mention rate in typical user queries |
| Infra Completeness | 25% | `INFRA_COMPLETENESS` | Stage 2 | Website quality, social media presence, authoritative media coverage |
| Competitive Advantage | 25% | `COMPETITIVE_ADVANTAGE` | Stage 3 + 5 | Relative performance vs. 3-5 auto-identified competitors |
| Sentiment Health | 25% | `SENTIMENT_HEALTH` | Stage 6 | Negative rate, risk level, sentiment distribution |

| Grade | Score | Color | Description |
|-------|-------|-------|-------------|
| Excellent | 90-100 | 🟢 | GEO Leader |
| Good | 80-89 | 🟢 | GEO Advanced |
| Moderate | 70-79 | 🟡 | GEO Follower |
| Poor | 60-69 | 🟠 | GEO Laggard |
| Bad | 0-59 | 🔴 | GEO Invisible |

---

## 9-Stage Pipeline

```
Stage 1: User Profile      ──→ Stage 2: Infra Eval ─┐
                              Stage 3: Competitor ──┤ Parallel
                                                  ↓
                              Stage 4: AI Search Test
                                                  ↓
Stage 5: GEO Effect   ──┐                       │
Stage 6: Sentiment    ──┤ Parallel              │
                        ↓                       │
               Stage 7: Overview              │
                        ↓                       │
               Stage 8: AIVO Score            │
                        ↓                       │
               Stage 9: Suggestion ←────────────┘
```

**Total time**: ~60-120s per platform (Doubao deep-thinking model `doubao-seed-evolving` takes 15-25s per query).

---

## Tech Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| Language | Python 3.9+ | Async pipeline (asyncio) with `from __future__ import annotations` for 3.9 compatibility |
| HTTP Client | httpx | Async HTTP requests, compatible with Kimi / Doubao / OpenAI |
| HTML Template | jinja2 | Visual report rendering, pure CSS/SVG inline (no external JS) |
| Data Parsing | BeautifulSoup4 | Website structure analysis |
| Configuration | pydantic-settings | `.env` file loading with environment variable override |
| AI Search | Doubao Responses API + Kimi Chat Completions | Doubao Seed series (deep-thinking), Kimi moonshot-v1 series |

---

## Error Handling & Degradation

| Scenario | Stage | Fallback Strategy | Output Flag |
|----------|-------|-------------------|-------------|
| AI search API timeout | Stage 4 | Use cached data or simulation, mark as "data timeliness limited" | `dataQuality: "degraded"` |
| Competitor identification fails | Stage 3 | Use default category library (Top 3 brands), mark as "default recommendation" | `competitorSource: "default"` |
| Sentiment platform unavailable | Stage 6 | Mark as "data missing", use category average for scoring | `sentimentStatus: "unavailable"` |
| Website inaccessible | Stage 2 | Website sub-item = 0, infra score based on other dimensions | `websiteStatus: "inaccessible"` |
| JSON generation error | Output stage | Call JSON repair tool, retry up to 3 times | `jsonRepairApplied: true` |

---

## FAQ

**Q: Why is the diagnosis result "Poor" (e.g., 57)?**

A: AIVO score is the average of 4 dimensions. If one dimension scores very low (e.g., Infra 55), even if others are decent, the total is pulled down. Check the HTML report for specific weaknesses and optimization suggestions.

**Q: Can I diagnose English brands?**

A: Yes, but Chinese brands are prioritized. For international brands, switch `--platform` to `chatgpt` or `perplexity`.

**Q: How are competitors selected?**

A: Three-layer strategy: ① LLM semantic analysis ② Search API co-occurrence analysis ③ Default category library fallback. You can see the selection rationale for each competitor in the HTML report.

**Q: Are paid APIs required?**

A: Core functions (LLM reasoning + search testing) require API keys. Both Kimi and Doubao offer free tiers sufficient for daily diagnostics.

---

## V2.0 Roadmap

| Phase | Feature | Course Mapping | Priority |
|-------|---------|---------------|----------|
| Phase 1 | MCP Tool Integration | VibeCoding DAY-02 | 🔴 P0 |
| Phase 2 | LangGraph Autonomous Agent | VibeCoding DAY-04 | 🔴 P0 |
| Phase 3 | Real Search API (SerpAPI) | VibeCoding DAY-02 | 🟡 P1 |
| Phase 4 | FastAPI Web Service | VibeCoding DAY-01 | 🟡 P1 |
| Phase 5 | pytest Automated Testing | VibeCoding DAY-03 | 🟡 P1 |
| Phase 6 | RAG Vector Database | VibeCoding DAY-03 | 🟢 P2 |

**Goal**: Evolve from "fixed pipeline script" to "autonomous decision-making Agent" with MCP tool calling, LangGraph orchestration, and conditional edge loop decisions.

---

## License

[MIT License](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Acknowledgments

This project was reverse-engineered from WorkBuddy "GEO Visibility Diagnosis" Agent runtime logs. Thanks to the original designer.

Built with Vibe Coding — 11 sub-agents, 9 stages, 10 bugs fixed, 74/100 AIVO score on the first test.
