# Contributing to GEO Visibility Diagnostician

Thank you for your interest in contributing! This project was built with **Vibe Coding** (AI-assisted collaborative coding), and we welcome all forms of contributions — code, documentation, bug reports, and feature requests.

---

## How to Contribute

### 1. Reporting Issues

Before creating an issue, please:

- Check existing [Issues](../../issues) to avoid duplicates
- Include your Python version, OS, and the exact command that triggered the problem
- Paste the full error traceback
- Attach the `output/{brand}_{platform}_diag-report.json` if available (redact sensitive data)

**Issue Templates:**

- 🐛 **Bug Report**: Something is broken
- ✨ **Feature Request**: New capability or enhancement
- 📚 **Documentation**: Typos, unclear instructions, missing translations
- 🧪 **Vibe Coding Experiment**: Share your Vibe Coding approach or improvements

### 2. Submitting Pull Requests

```bash
# 1. Fork the repository
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/geo-visibility-diagnostician.git

# 3. Create a branch
git checkout -b feature/your-feature-name

# 4. Make changes and commit
git add .
git commit -m "feat: description of your change"

# 5. Push and create PR
git push origin feature/your-feature-name
```

**PR Guidelines:**

- Keep PRs focused on a single feature or fix
- Update `CHANGELOG.md` with your changes
- Add/update relevant documentation
- Ensure `.env` files are NOT committed (check `.gitignore`)
- For V2.0 features (MCP, LangGraph), reference the roadmap in `docs/IMPLEMENTATION.md`

### 3. Development Setup

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/geo-visibility-diagnostician.git
cd geo-visibility-diagnostician
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest  # For testing (V2.0)

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### 4. Code Style

- Python: Follow PEP 8
- Use `from __future__ import annotations` for Python 3.9 compatibility
- Type annotations required for all public functions
- Async functions preferred for I/O operations
- All JSON outputs must include `_stageMeta` with `elapsedMs`, `status`, `recordCount`

### 5. Testing (V2.0)

> V1.0 has zero test coverage. V2.0 will introduce pytest. Until then, manual verification is the standard.

```bash
# Manual verification
python main.py --brand "TestBrand" --category "Test Category"
# Check output/ directory for valid JSON and HTML
```

### 6. Documentation Contributions

- English is the primary language for GitHub-facing docs
- Chinese translations can be added as `.zh.md` files
- `MEMORY.md` should be updated when significant bugs or lessons are learned

---

## Vibe Coding Experiments

This project is a **Vibe Coding case study**. We especially welcome:

- **New Vibe Coding approaches**: How you used AI to build or extend this project
- **Sub-agent experiments**: New ways to parallelize stage generation
- **Prompt engineering**: Better prompts for any of the 9 stages
- **Tool integrations**: New MCP tools, search APIs, or LLM backends

If you ran a Vibe Coding experiment, create an Issue with label `vibe-coding` and share your approach, prompts, and results.

---

## Code of Conduct

- Be respectful and constructive
- Assume good intentions
- Focus on the code, not the person
- Help others learn Vibe Coding

---

## Questions?

Open a [Discussion](../../discussions) or reach out via the Issue tracker.

Happy Vibe Coding! 🚀
