🖥️ AI Data Center Procurement Risk Agent

An AI-powered procurement and deployment readiness tool for data center hardware planning.

Built to simulate how supply chain risk across GPUs, servers, networking, storage, cooling, and power infrastructure can affect AI cluster deployment.

🚨 Business Problem

AI infrastructure teams depend on long-lead-time hardware such as GPUs, servers, networking gear, and cooling systems. A delay in even one component category can delay cluster deployment, reduce available compute capacity, and slow infrastructure expansion.

Traditional inventory planning tools usually stop at SKU-level reorder signals. They do not clearly show which hardware categories are most likely to block deployment readiness.

💡 Solution

This project combines deterministic supply chain analytics with LLM-based reasoning to:

classify procurement risk at the SKU level
estimate shortage exposure and reorder requirements
project 12-week capacity scenarios using market/news signals
identify category-level deployment blockers
answer natural language procurement questions
generate executive summaries and action plans
🏗️ Architecture
data.csv → tools.py → agent.py → app.py
                ↑
           llm_helper.py

tools.py
Deterministic supply chain calculations such as demand metrics, risk classification, shortage cost calculations, capacity forecasting, and news fetching.

llm_helper.py
LLM reasoning layer responsible for executive summaries, action plans, category insights, and natural language Q&A.

agent.py
Routing layer that determines which tool or reasoning function should be used based on the user's question.

app.py
Streamlit dashboard UI that visualizes supply chain risk, capacity forecasts, and deployment readiness.

✨ Features
Live news signal extraction via Google News RSS + Groq LLM
3-scenario capacity forecasting (base / optimistic / pessimistic)
Procurement risk classification (Critical / High / Medium / Low)
Shortage cost exposure calculation
Reorder quantity recommendations
Cluster deployment readiness analysis identifying hardware categories that may block AI cluster deployment
Natural language procurement queries through an agent router
Structured action plans for procurement and capacity teams
Executive-ready summaries for leadership reviews
CSV report downloads
🛠️ Tech Stack
Python
Streamlit
Pandas
NumPy
Matplotlib
Groq API (Llama 3.3 70B)
Feedparser
🚀 How to Run
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-datacenter-agent.git
cd ai-datacenter-agent
2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Set the Groq API key
export GROQ_API_KEY="your-groq-key"

You can obtain a free API key at:
https://console.groq.com

5. Run the application
python -m streamlit run app.py
📊 Example Questions to Ask the Agent
Question	Description
Which items are critical?	Shows hardware with critical or high procurement risk
Give me an action plan	Generates structured immediate and quarterly procurement actions
Analyze GPU vs server risk	Provides category-level risk insights
What is blocking cluster deployment?	Identifies infrastructure categories that may delay cluster readiness
Give me an executive summary	Produces a leadership-ready procurement summary
What should we reorder first?	Prioritized procurement recommendations
🏢 Relevance to Infrastructure & Supply Chain Roles

This project demonstrates capabilities relevant to:

Supply Chain Program Managers
Logistics Program Managers
Infrastructure Capacity Planning teams
Data Center Deployment teams

Key skills showcased include:

Supply chain analytics and demand modeling
Procurement risk management
Infrastructure deployment awareness
LLM-assisted decision support
Data visualization and executive reporting
👤 About

Built by Parth Gandhi

Industrial & Systems Engineer with 5+ years of experience in supply chain analytics, demand planning, and operations optimization.

Certifications:
APICS CSCP
AWS Cloud Practitioner
Certified Six Sigma Black Belt (CSSBB)

LinkedIn:
https://linkedin.com/in/parthdgandhi

Email:
parthdgandhi1@gmail.com