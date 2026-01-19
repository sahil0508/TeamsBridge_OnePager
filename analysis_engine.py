import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TEAMS_ORDER = [
    "Trust",
    "Empathy",
    "Alignment",
    "Meaning / Purpose",
    "Psychological Safety"
]


def compute_team_scores(df):
    return (
        df.groupby("category")["score"]
        .mean()
        .reindex(TEAMS_ORDER)
        .round(2)
    )


def score_status(score):
    if score >= 3.0:
        return "Strength"
    elif score >= 2:
        return "Fragile"
    else:
        return "At risk"


def generate_ai_analysis(scores_dict):
    """
    Returns structured JSON:
    {
      story: str,
      dimension_notes: {dimension: note},
      ceo_moves: [str, str, str]
    }
    """

    prompt = f"""
You are an executive team effectiveness advisor.

Based on the TEAMS scores below, produce a concise executive diagnostic.

TEAMS scores:
{scores_dict}

STRICT OUTPUT FORMAT (JSON ONLY, no markdown, no commentary):

{{
  "story": "One concise paragraph (4–5 lines) describing overall team dynamics and execution risk.",
  "dimension_notes": {{
    "Trust": "One short, direct interpretation.",
    "Empathy": "One short, direct interpretation.",
    "Alignment": "One short, direct interpretation.",
    "Meaning / Purpose": "One short, direct interpretation.",
    "Psychological Safety": "One short, direct interpretation."
  }},
  "ceo_moves": [
    "I will ...",
    "I will ...",
    "I will ..."
  ]
}}

Tone: board-ready, direct, non-academic.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content

def generate_visual_insight(scores_dict):
    """
    Returns a single board-ready sentence interpreting the radar pattern.
    """

    prompt = f"""
You are an executive advisor.

Based on the TEAMS scores below, write ONE concise sentence (max 20 words)
interpreting the overall pattern shown in a radar chart.

TEAMS scores:
{scores_dict}

Rules:
- One sentence only
- No recommendations
- No labels (e.g. "Overall")
- Board-ready, precise, neutral tone
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
