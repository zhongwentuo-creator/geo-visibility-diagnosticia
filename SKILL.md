# Skill: GEO Visibility Diagnostician

> 帮助品牌量化自己在 AI 原生时代的"数字存在感"。
> 通过 9 阶段诊断流水线，评估品牌在生成式引擎（豆包、ChatGPT 等）中的信息可见度与推荐权重。

---

## Trigger Conditions

When the user asks for any of the following:

- "帮我诊断 [品牌] 的 GEO 可见度"
- "GEO 诊断"
- "AI 可见度诊断"
- "品牌体检"
- "AI 搜索中的品牌表现"
- "帮我看看 [品牌] 在豆包里搜得到吗"
- "Generative Engine Optimization"
- "GEO 优化建议"

---

## Prerequisites

Before running the diagnosis, ensure:

1. **API Keys configured** in `.env`:
   - `KIMI_API_KEY` (for LLM reasoning)
   - `DOUBAO_API_KEY` (for AI search testing)
   
2. **Virtual environment activated**:
   ```bash
   cd /Users/zhongwentuo/Desktop/WenTuo_kimi/WorkBuddy_Dify/GEO可见度诊断师
   source venv/bin/activate
   ```

3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Execution Steps

### Step 1: Gather Input

Ask the user for:
- **Brand name** (required): e.g., "听力熊", "小米", "Apple"
- **Product category** (required): e.g., "儿童AI对话智能体", "智能手机", "电动汽车"
- **Official website** (optional): e.g., "https://www.example.com"
- **Platform** (optional, default: doubao): `doubao` / `chatgpt` / `perplexity`

### Step 2: Run Diagnosis

```bash
cd /Users/zhongwentuo/Desktop/WenTuo_kimi/WorkBuddy_Dify/GEO可见度诊断师
source venv/bin/activate

python main.py --brand "{品牌名}" --category "{产品类型}" --platform {平台}
```

### Step 3: Wait for Completion

The pipeline will execute 9 stages:
1. User Profile Construction (1-2s)
2. Infrastructure Evaluation (3-5s)
3. Competitor Analysis (5-10s) — **parallel with Stage 2**
4. AI Search Testing (15-60s) — **depends on Stage 1+3**
5. GEO Effect Summary (1-2s) — **parallel with Stage 6**
6. Sentiment Scan (5-25s) — **parallel with Stage 5**
7. Comprehensive Overview (2-3s)
8. AIVO Scoring (1-2s)
9. Suggestion System (3-5s)

**Total time**: ~60-120 seconds.

### Step 4: Report Output

After completion, the report files are saved in:
```
output/GEO-YYYYMMDD-HHMMSS/
├── {brand}_{platform}_diag-report.json      # Structured data
└── {brand}_{platform}_GEO-Diagnosis-Report.html  # Visual report
```

### Step 5: Interpret Results

Read the HTML report and provide a summary to the user:

**Key metrics to highlight:**
- **AIVO Total Score** (0-100): Overall brand visibility in AI
- **Grade**: 优秀(90+)/良好(80-89)/中等(70-79)/较差(60-69)/差(0-59)
- **4 Dimensions**: AI Search Visibility / Infra Completeness / Competitive Advantage / Sentiment Health
- **Top 3 Actions**: Highest priority recommendations from the suggestion system
- **Score Projection**: Expected improvement if recommendations are followed (e.g., 57 → 81 in 6 months)

**Example summary format:**
```
🏆 AIVO 总分: 74/100（中等）

| 维度 | 得分 | 说明 |
|------|------|------|
| AI 搜索可见度 | 58 | 豆包 15 问中提及 7 次（47%） |
| 基建完善度 | 55 | 官网几乎空白，内容密度不足 |
| 竞品对比优势 | 60 | 仅为竞品均值的 82% |
| 舆情健康度 | 56 | 负面率 30%，中风险，趋势上升 |

💡 三个最关键的行动:
1. 舆情清零：处理存量投诉
2. 官网重建：建立独立品牌站
3. 内容破圈：进入小红书/抖音家长决策场景

预计 6 个月内可从 74 分提升至 81 分（良好）。
```

### Step 6: Open Report (if possible)

```bash
# macOS
open output/*/听力熊_doubao_*-GEO诊断报告.html

# Or provide the file path to the user
ls output/*/听力熊_doubao_*-GEO诊断报告.html
```

---

## Output File Interpretation

### JSON Report (`-diag-report.json`)

Structured data with all 9 stage outputs. Useful for:
- BI integration
- Historical tracking
- Custom analysis

### HTML Report (`-GEO诊断报告.html`)

Self-contained visual report with:
- Cover page: AIVO score ring chart
- Executive summary: 1-sentence conclusion + 3 key findings
- User profile: 3 persona cards
- Infrastructure: Radar chart + media matrix
- Competitor: Horizontal bar chart + detail cards
- AI Search: Heat map (mentioned/not mentioned)
- Sentiment: Pie chart + risk badge
- Optimization: Priority tags + timeline

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "401 Authentication Error" | API Key invalid or expired | Check `.env` keys, verify with `curl` test |
| "TimeoutError" | Doubao deep-thinking model slow | Already set 60s timeout, normal behavior |
| "JSON parse error" | Chinese quotes in LLM output | `json_repair.py` auto-fixes, should resolve |
| "No output files" | `output/` directory missing | Check permissions, directory auto-creates |
| "ModuleNotFoundError" | Virtual env not activated | Run `source venv/bin/activate` |

---

## V2.0 Roadmap

This skill will evolve in V2.0 with:
- MCP tool integration for autonomous API calling
- LangGraph orchestration for conditional decision-making
- Real search API (SerpAPI) for authentic data
- FastAPI web service for remote access

---

## Project Info

- **GitHub**: https://github.com/YOUR_USERNAME/geo-visibility-diagnostician
- **License**: MIT
- **Built with**: Vibe Coding (11 sub-agents, 9 stages, 10 bugs fixed)
- **First test score**: 74/100 (Brand: 听力熊)

---

*This skill is frozen at V1.0. V2.0 will introduce MCP and LangGraph capabilities.*
