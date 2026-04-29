# 🔬 Agent43 — AI-Powered Academic Writing System

A personal academic writing system with nine cognitively distinct AI agents across three disciplines. Built with Streamlit, OpenAI, and Supabase.

---

## What It Does

- **Dispatcher Agent** — analyses your assessment brief and recommends the best writer
- **9 Specialist Agents** — across International Business, International Marketing, and Health & Social Care (NVQ)
- **Citation Grounding** — citations drawn only from your uploaded reference materials
- **Dual Similarity Check** — output vs source materials + output vs your writing history
- **AI Risk Assessment** — scores AI-pattern density in the output
- **Cost Tracking** — per-generation and cumulative USD cost
- **Export** — clean DOCX and TXT download

---

## Agent Registry

| Agent | Class | Cognitive Signature |
|---|---|---|
| Agent Alpha | International Business | Institutional Economist |
| Agent Beta | International Business | Emerging Markets Realist |
| Agent Gamma | International Business | Corporate Strategist |
| Agent Delta | International Marketing | Cultural Intelligence Theorist |
| Agent Epsilon | International Marketing | Digital & Behavioural Strategist |
| Agent Zeta | International Marketing | Brand Equity Architect |
| Agent Eta | Health & Social Care (NVQ) | Reflective Practitioner |
| Agent Theta | Health & Social Care (NVQ) | Policy & Systems Analyst |
| Agent Iota | Health & Social Care (NVQ) | Social Justice Advocate |

---

## Repo Structure

```
agent43/
├── app.py              ← entire application (single file)
├── requirements.txt    ← Python dependencies
└── README.md
```


create extension if not exists vector;

-- Writings table
create table if not exists writings (
    id            bigserial primary key,
    created_at    timestamptz default now(),
    discipline    text,
    agent_name    text,
    context       text,
    word_count    int,
    output_text   text,
    tokens_in     int,
    tokens_out    int,
    cost_usd      numeric(10,6)
);

-- Embeddings table
create table if not exists embeddings (
    id          bigserial primary key,
    writing_id  bigint references writings(id) on delete cascade,
    embedding   vector(1536)
);

-- Cost log table
create table if not exists cost_log (
    id          bigserial primary key,
    created_at  timestamptz default now(),
    feature     text,
    model       text,
    tokens_in   int,
    tokens_out  int,
    cost_usd    numeric(10,6)
);
```

---

---


---

## Step 4 — Using Agent43

### Writing Flow
1. **Paste your assessment context**
2. Click **Analyse & Recommend Agent** — the Dispatcher reads the brief and suggests the best agent
3. Confirm or override the agent selection
4. Fill in: **Structure**, **Rubric** (optional), **Word Count**
5. **Upload your reference materials** (PDF, DOCX, or TXT) — citations will be drawn only from these
6. Click **Generate**
7. Click **Run Assessment** to get similarity scores, risk level, and cost
8. **Download** as DOCX or TXT

### Tips
- Always upload your source materials before generating — this is what prevents hallucinated citations
- The Dispatcher is an advisor, not a gatekeeper — you can always override
- Run the Assessment after every generation to build your similarity history in Supabase
- Check the Dashboard tab to monitor your cumulative costs

---

## Similarity Score Guide

| Score | Status |
|---|---|
| Below 75% | 🟢 Original — genuine synthesis |
| 75%–85% | 🟡 Moderate overlap — review recommended |
| Above 85% | 🔴 High similarity — significant overlap |

The **vs Source Materials** check ensures the write-up is not just a paraphrase of your uploaded references.
The **vs Past Work** check ensures you are not recycling content across submissions.

---

## Cost Reference (approximate)

| Action | Model | Typical Cost |
|---|---|---|
| Dispatcher | GPT-4o-mini | ~$0.0001 |
| Writing (1500 words) | GPT-4o | ~$0.04–0.06 |
| Risk Assessment | GPT-4o-mini | ~$0.0003 |
| Embeddings (similarity) | text-embedding-3-small | ~$0.00001 |

---

## Updating OpenAI Pricing

If OpenAI updates pricing, find this block in `app.py` and update the values:

```python
PRICING = {
    "gpt-4o":          {"in": 0.000005,   "out": 0.000015},
    "gpt-4o-mini":     {"in": 0.00000015, "out": 0.0000006},
    "text-embedding-3-small": {"in": 0.00000002, "out": 0.0},
}
```

---

## Security Note

Agent43 uses a simple password gate (`APP_PASSWORD` in secrets). Since this is for personal use only, this is sufficient. Never share your Streamlit app URL or password publicly.
