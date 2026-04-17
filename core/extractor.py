import json
import os
from typing import Any, Optional
from openai import OpenAI

EXTRACTION_SCHEMA = {
    "author_year": "Author(s) and publication year in APA-style short citation e.g. 'Smith et al. (2021)'",
    "title": "Full title of the paper",
    "research_context": "Country/region, industry/sector, and dataset used",
    "methodology": "Primary statistical/econometric model(s) used e.g. OLS, SEM, Panel Data, SUR, etc.",
    "key_variables": {
        "independent": "List of independent/predictor variables",
        "dependent": "Dependent/outcome variable(s)",
        "controls": "Control variables if mentioned",
    },
    "findings": "Clear, directional summary of key empirical results (what was significant, direction, magnitude if given)",
    "theoretical_contributions": "What does this add to theory?",
    "practical_contributions": "What are the managerial or policy implications?",
    "strengths": "Methodological or data strengths",
    "limitations": "Explicitly stated or implied limitations",
    "citation_apa": "Full APA 7th edition citation",
    "citation_mla": "Full MLA 9th edition citation",
    "citation_harvard": "Full Harvard citation",
}

EXTRACTION_PROMPT = """You are an expert academic research analyst. Your task is to extract structured empirical information from the research paper text provided.

CRITICAL RULES:
1. Only extract information explicitly present in the text. Do NOT invent or hallucinate.
2. If a field cannot be determined from the text, use "Not specified" — never guess.
3. Be concise but complete. Findings must be directional (e.g., "X has a significant positive effect on Y").
4. For methodology, be specific about the model variant (e.g., "Fixed-effects panel regression" not just "regression").

Return a single JSON object with EXACTLY these keys:
- author_year: Short citation e.g. "Smith et al. (2021)"
- title: Full paper title
- research_context: Country, industry, dataset description
- methodology: Primary model(s) used
- independent_variables: Comma-separated list of IVs
- dependent_variable: The main outcome variable
- control_variables: Comma-separated controls (or "None specified")
- findings: 2-4 sentence summary of key results with directions
- theoretical_contributions: 1-2 sentences
- practical_contributions: 1-2 sentences  
- strengths: 1-2 key methodological strengths
- limitations: 1-3 key limitations
- citation_apa: Full APA 7 citation
- citation_mla: Full MLA citation
- citation_harvard: Full Harvard citation

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.

Paper text:
{text}"""


SYNTHESIS_PROMPT = """You are an expert academic research synthesizer. You have been given structured extractions from {n_papers} research papers.

Your task is to produce a cross-paper synthesis with the following JSON structure:

{{
  "common_findings": ["finding 1", "finding 2", ...],          // 3-6 recurring themes/results across papers
  "conflicting_results": ["conflict 1", "conflict 2", ...],    // 2-4 areas where papers disagree  
  "dominant_methodology": "most used approach across papers",
  "methodology_patterns": ["pattern 1", "pattern 2", ...],     // 2-4 methodological observations
  "common_weaknesses": ["weakness 1", ...],                    // 2-4 shared limitations
  "research_gaps": ["gap 1", "gap 2", ...],                    // 4-6 underexplored areas
  "underexplored_variables": ["var 1", "var 2", ...],          // 3-5 variables rarely tested
  "future_directions": ["direction 1", ...],                   // 3-5 concrete future research suggestions
  "overall_summary": "2-3 sentence synthesis of the body of literature"
}}

CRITICAL: Base ALL findings on the actual paper extractions. Do not fabricate. Return ONLY the JSON object.

Paper extractions:
{extractions}"""


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OpenAI API key not set. Please enter your API key in the sidebar.")
    return OpenAI(api_key=api_key)


def extract_paper(text: str, filename: str = "") -> dict[str, Any]:
    """
    Call GPT-4o to extract structured empirical data from paper text.
    Returns a dict with all schema fields.
    """
    client = get_client()
    
    prompt = EXTRACTION_PROMPT.format(text=text)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a precise academic research analyst. You extract structured data from research papers. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=1500,
        response_format={"type": "json_object"}
    )
    
    raw = response.choices[0].message.content
    result = json.loads(raw)
    
    # Attach source filename
    result["_source_file"] = filename
    result["_status"] = "success"
    
    return result


def synthesize_papers(papers: list[dict]) -> dict[str, Any]:
    """
    Generate cross-paper synthesis from list of extracted paper dicts.
    """
    client = get_client()
    
    # Build a clean summary of each paper for the prompt
    extractions_text = ""
    for i, p in enumerate(papers, 1):
        extractions_text += f"\n--- Paper {i}: {p.get('title', 'Unknown')} ---\n"
        extractions_text += f"Author/Year: {p.get('author_year', 'N/A')}\n"
        extractions_text += f"Methodology: {p.get('methodology', 'N/A')}\n"
        extractions_text += f"IVs: {p.get('independent_variables', 'N/A')}\n"
        extractions_text += f"DV: {p.get('dependent_variable', 'N/A')}\n"
        extractions_text += f"Findings: {p.get('findings', 'N/A')}\n"
        extractions_text += f"Limitations: {p.get('limitations', 'N/A')}\n"
    
    prompt = SYNTHESIS_PROMPT.format(
        n_papers=len(papers),
        extractions=extractions_text
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert academic research synthesizer. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    
    raw = response.choices[0].message.content
    return json.loads(raw)
