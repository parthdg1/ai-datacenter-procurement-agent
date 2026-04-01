# 🖥️ AI Data Center Procurement Risk Agent

An AI-powered procurement risk agent for data center hardware planning. 
Built for supply chain and infrastructure PM roles at AI-first companies 
like NVIDIA, Google, and AWS.

## 🚨 The Problem

GPU lead times are 150–180 days. AI infrastructure demand is growing 8%+ 
weekly. Traditional flat-line inventory planning breaks down completely 
in this environment.

One missed reorder signal = delayed cluster deployment = millions in lost 
compute capacity.

## 💡 The Solution

An agentic AI system that:
- Scrapes **live news** (NVIDIA supply updates, semiconductor shortages, 
  hyperscaler expansions)
- Extracts **demand signals** using LLM reasoning
- Runs **3-scenario capacity forecasts** (base, optimistic, pessimistic)
- Flags **critical procurement risks** before they become outages
- Answers **natural language questions** about your hardware portfolio
- Generates **structured action plans** for procurement and capacity teams

## 🏗️ Architecture
```
data.csv → tools.py → agent.py → app.py
                ↑          ↑
          llm_helper.py    |
                ↑          |
          Live News API ───┘
```

- **tools.py** — deterministic supply chain calculations (metrics, risk 
  classification, scenario forecasting, news fetching)
- **llm_helper.py** — LLM reasoning layer (executive summaries, action 
  plans, natural language Q&A)
- **agent.py** — intelligent routing layer (decides which tool to use 
  based on user intent)
- **app.py** — Streamlit dashboard UI

## ✨ Features

- 📰 Live news signal extraction via Google News RSS + Groq LLM
- 📊 3-scenario capacity forecasting (base / optimistic / pessimistic)
- 🚨 Risk classification (Critical / High / Medium / Low)
- 💰 Shortage cost exposure calculation
- 📦 Reorder quantity recommendations
- 💬 Natural language procurement queries
- ⚡ Structured action plans (immediate + quarterly)
- 📋 Executive-ready summaries
- ⬇️ CSV report downloads

## 🛠️ Tech Stack

- Python 3.8+
- Groq API (Llama 3.3 70B)
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Feedparser

## 🚀 How to Run

**1. Clone the repo:**
```bash
git clone https://github.com/YOUR_USERNAME/ai-datacenter-agent.git
cd ai-datacenter-agent
```

**2. Create and activate virtual environment:**
```bash
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Set your Groq API key:**
```bash
export GROQ_API_KEY="your-groq-key-here"
```
Get a free key at [console.groq.com](https://console.groq.com)

**5. Run the app:**
```bash
python -m streamlit run app.py
```

**6. Use the app:**
- Check "Use sample inventory data" to load demo data
- Click "Refresh News" to fetch live signals
- Ask questions like:
  - "Which GPUs are critical?"
  - "Give me an action plan"
  - "Analyze server vs networking risk"
  - "Give me an executive summary"

## 📊 Sample Questions to Ask the Agent

| Question | What it does |
|----------|-------------|
| "Which items are critical?" | Shows Critical/High risk hardware |
| "Give me an action plan" | Structured immediate + quarterly actions |
| "Analyze GPU vs server risk" | Category level insights |
| "Give me an executive summary" | Full procurement brief |
| "What should I reorder first?" | Prioritized reorder recommendations |

## 🏢 Relevance to Data Center PM Roles

This project demonstrates:
- **Supply chain domain expertise** — lead time modeling, reorder logic, 
  shortage cost calculation
- **AI integration** — LLM-powered reasoning over real inventory data
- **Agentic architecture** — intelligent routing between deterministic 
  tools and LLM functions
- **Real-time signal processing** — live news extraction and forecast 
  adjustment
- **Executive communication** — dashboard designed for VP/Director 
  level audiences

## 👤 About

Built by **Parth Gandhi** — Supply Chain Professional with 5+ years 
experience in demand planning, S&OP, and inventory management.

APICS CSCP | AWS Cloud Practitioner | CSSBB | Lean Six Sigma Black Belt

[LinkedIn](https://linkedin.com/in/parthdgandhi) | 
[Email](mailto:parthdgandhi1@gmail.com)