import os
import json
from groq import Groq


DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Please export your Groq API key before running the app."
        )
    return Groq(api_key=api_key)


def safe_json_loads(text: str, fallback):
    """
    Safely parse JSON returned by the LLM.
    Falls back to a default object if parsing fails.
    """
    try:
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception:
        return fallback


def build_system_prompt() -> str:
    return """
You are an AI infrastructure procurement strategist.

Your job is to help a cloud / hyperscaler / AI lab procurement and capacity planning team
understand risks in data center hardware supply.

You think like a cross-functional PM working across:
- supply planning
- procurement
- supplier risk
- capacity forecasting
- infrastructure expansion
- GPU / server / networking / power / cooling dependencies

You do NOT give vague generic advice.
You must connect your reasoning to the actual input metrics.

Priorities:
1. Identify what is most likely to constrain capacity expansion
2. Separate immediate operational risk from medium-term strategic risk
3. Explain downstream impact (compute deployment, cluster readiness, expansion delays)
4. Recommend realistic procurement or mitigation actions
5. Be concise, sharp, and executive-ready

When making recommendations:
- prioritize by urgency and business impact
- distinguish between category-level risk and SKU-level risk
- mention dependency chains when relevant
- focus on actionability
"""


def call_llm(user_prompt: str, model: str = DEFAULT_MODEL, temperature: float = 0.2) -> str:
    client = get_groq_client()

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()


def generate_exec_summary(
    summary_metrics: dict,
    top_risks_csv: str,
    reorder_csv: str,
    news_signals: dict,
    capacity_csv: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Generates an executive summary for leadership / PM review.
    """

    prompt = f"""
Create an executive summary for an AI data center procurement review.

Context:
- We are planning AI infrastructure capacity and need to understand procurement bottlenecks.
- Use the data below to identify the most important risks to expansion readiness.

Summary metrics:
{json.dumps(summary_metrics, indent=2)}

Top risks:
{top_risks_csv}

Reorder recommendations:
{reorder_csv}

News signals:
{json.dumps(news_signals, indent=2)}

Capacity projections:
{capacity_csv}

Output format:
1. Overall risk posture (2-3 sentences)
2. Top 3 constraints to capacity expansion
3. Immediate actions for this week
4. Strategic actions for this quarter
5. One sentence on likely business impact if no action is taken

Constraints:
- Do not repeat raw tables
- Be specific
- Write like a PM / procurement leader briefing infra leadership
- Focus on data center buildout risk, GPU cluster readiness, and procurement prioritization
"""

    return call_llm(prompt, model=model, temperature=0.2)


def generate_category_insights(
    category_summary_csv: str,
    news_signals: dict,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Produces category-level interpretation: GPU vs Server vs Networking vs Power, etc.
    """

    prompt = f"""
Analyze the following category-level procurement summary for AI data center infrastructure.

Category summary:
{category_summary_csv}

News signals:
{json.dumps(news_signals, indent=2)}

Write a decision memo with:
1. Which category is the biggest near-term bottleneck
2. Which category has the highest medium-term expansion risk
3. Which categories are currently manageable
4. Where demand growth and lead time risk are compounding each other
5. Recommended category-level procurement posture

Make the analysis sharp, strategic, and tied to infrastructure deployment risk.
"""

    return call_llm(prompt, model=model, temperature=0.2)


def answer_procurement_question(
    question: str,
    summary_metrics: dict,
    context_csv: str,
    news_signals: dict,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Answers free-form user questions grounded in the procurement data.
    """

    prompt = f"""
Answer the following question about AI data center procurement risk.

User question:
{question}

Summary metrics:
{json.dumps(summary_metrics, indent=2)}

Detailed risk context:
{context_csv}

News signals:
{json.dumps(news_signals, indent=2)}

Instructions:
- Ground the answer in the provided data
- If something is uncertain, say so explicitly
- Prioritize strategic reasoning over generic explanation
- Mention specific SKUs or categories when relevant
- Tie the answer to capacity expansion, procurement constraints, and operational impact
"""

    return call_llm(prompt, model=model, temperature=0.15)


def generate_action_plan(
    critical_items_csv: str,
    reorder_csv: str,
    news_signals: dict,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Returns a structured action plan in JSON for the UI or agent layer.
    """

    prompt = f"""
You are creating an action plan for AI infrastructure procurement.

Critical items:
{critical_items_csv}

Reorder recommendations:
{reorder_csv}

News signals:
{json.dumps(news_signals, indent=2)}

Return ONLY valid JSON in this format:
{{
  "immediate_actions": [
    {{
      "action": "string",
      "owner": "Procurement|Supply Planning|Capacity PM|Supplier Manager",
      "priority": "Critical|High|Medium",
      "reason": "string"
    }}
  ],
  "quarterly_actions": [
    {{
      "action": "string",
      "owner": "Procurement|Supply Planning|Capacity PM|Supplier Manager",
      "priority": "Critical|High|Medium",
      "reason": "string"
    }}
  ],
  "executive_watchouts": [
    "string"
  ]
}}

Rules:
- Immediate actions should focus on urgent mitigation and near-term supply protection
- Quarterly actions should focus on supplier strategy, capacity planning, and dependency reduction
- Keep each action concrete and realistic
- Return only JSON
"""

    fallback = {
        "immediate_actions": [],
        "quarterly_actions": [],
        "executive_watchouts": ["Could not parse structured action plan from model output."],
    }

    raw = call_llm(prompt, model=model, temperature=0.1)
    return safe_json_loads(raw, fallback)


def score_resume_signal(summary_metrics: dict, news_signals: dict, model: str = DEFAULT_MODEL) -> str:
    """
    Optional: generates a recruiter/interviewer-facing explanation of what this project demonstrates.
    Useful later for README, interviews, and resume bullets.
    """

    prompt = f"""
You are helping a candidate explain why their AI infrastructure procurement risk agent is relevant
to roles in data center capacity planning, procurement PM, and technical program management.

Project metrics:
{json.dumps(summary_metrics, indent=2)}

External signals:
{json.dumps(news_signals, indent=2)}

Write:
1. A 3-sentence interview explanation of what this project does
2. 3 strong resume bullets for a PM / supply chain infra role
3. 3 talking points for why this project is relevant to AI data center expansion

Keep it credible and business-oriented.
"""

    return call_llm(prompt, model=model, temperature=0.2)