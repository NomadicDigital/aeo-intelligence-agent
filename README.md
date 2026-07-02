# AEO Intelligence Agent

An agentic pipeline that audits a website for **Answer Engine Optimisation (AEO)** readiness and generates a branded PDF report. Built with LangGraph, Claude, and FastAPI.

---

## What it does

Given a URL, the pipeline:

1. **Researches** the business — scrapes the site, extracts brand identity, identifies competitors, and generates core visibility queries
2. **Audits technical signals** — checks `robots.txt`, `llms.txt`, `llms-full.txt`, and structured schema markup
3. **Measures AI visibility** — tests whether Claude surfaces the brand (and its competitors) in response to real search queries
4. **Generates a report** — synthesises all findings into a scored PDF with key improvements and a quick win recommendation

Steps 2 and 3 run in parallel to minimise latency.

---

## Pipeline architecture

```
START
  └─▶ Research
        ├─▶ Technical Audit   ─┐
        └─▶ Visibility Analysis─┴─▶ Report ──▶ END
```

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | Claude Haiku (via [LangChain Anthropic](https://github.com/langchain-ai/langchain)) |
| Web scraping | [Firecrawl](https://firecrawl.dev) |
| PDF generation | [WeasyPrint](https://weasyprint.org) + Jinja2 |
| API | FastAPI |

---

## Requirements

- Python 3.11+
- [Firecrawl API key](https://firecrawl.dev)
- [Anthropic API key](https://console.anthropic.com)
- pango (required by WeasyPrint on macOS — see below)

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/NomadicDigital/aeo-intelligence-agent.git
cd aeo-intelligence-agent
python -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Install pango (macOS only)**

WeasyPrint requires pango for PDF rendering. Install it via Homebrew:

```bash
brew install pango
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Add your API keys to `.env`:

```
FIRECRAWL_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

---

## Running the API

```bash
cd src/aeo_agent
uvicorn main:app --reload
```

### Generate a report

```bash
curl -X POST http://localhost:8000/generate_report \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  --output report.pdf
```

The response is a PDF file downloaded directly. Reports are also saved locally to `reports/`.

---

## Project structure

```
src/aeo_agent/
├── agents/
│   ├── research.py           # Scraping and business intelligence
│   ├── technical_audit.py    # robots.txt, llms.txt, schema checks
│   ├── visibility_analysis.py# AI visibility scoring
│   └── report.py             # LLM synthesis + PDF generation
├── templates/
│   └── report.html           # Jinja2 PDF template
├── graph.py                  # LangGraph pipeline definition
├── main.py                   # FastAPI entry point
├── pdf_generator.py          # WeasyPrint rendering
└── state.py                  # Shared AgentState schema
```
