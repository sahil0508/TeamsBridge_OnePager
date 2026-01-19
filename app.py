import streamlit as st
import pandas as pd
import tempfile
import os
import json

from analysis_engine import (
    compute_team_scores,
    score_status,
    generate_ai_analysis,
    generate_visual_insight
)
from pdf_generator import build_pdf
from visuals import generate_radar_chart


# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------
st.set_page_config(layout="wide")
st.title("Executive Team One-Page Diagnostic")


# ---------------------------------------------------------
# Load question → category mapping (ID-based, verbatim text)
# ---------------------------------------------------------
def load_question_map(path="questions.json"):
    """
    questions.json format:
    [
      { "id": "q01", "category": "Trust", "text": "..." }
    ]
    """
    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    return {q["id"]: q["category"] for q in questions}


# ---------------------------------------------------------
# Detect raw (Airtable-style) survey
# ---------------------------------------------------------
def is_raw_survey(df):
    return any(str(c).lower().startswith("q") for c in df.columns)


# ---------------------------------------------------------
# Convert raw (wide) survey → standardized (long)
# ---------------------------------------------------------
def convert_raw_survey(df_raw, client_name, question_map):
    """
    Expected raw format:
    client | timestamp | language | q01 | q02 | ... | q41
    """

    # Normalize column names
    df_raw = df_raw.rename(columns={c: c.lower() for c in df_raw.columns})

    required_cols = {"client", "timestamp"}
    if not required_cols.issubset(df_raw.columns):
        raise ValueError("Raw survey must contain 'client' and 'timestamp' columns")

    question_cols = [c for c in df_raw.columns if c in question_map]

    if not question_cols:
        raise ValueError("No question columns (q01–q41) matched questions.json")

    df_long = df_raw.melt(
        id_vars=["timestamp"],
        value_vars=question_cols,
        var_name="question",
        value_name="score"
    )

    df_long = df_long.dropna(subset=["score"])

    df_long["category"] = df_long["question"].map(question_map)

    missing = df_long[df_long["category"].isna()]["question"].unique()
    if len(missing) > 0:
        raise ValueError(f"Unmapped questions found: {missing}")

    df_long["client"] = client_name

    return df_long[
        ["client", "question", "category", "score", "timestamp"]
    ]


# ---------------------------------------------------------
# File upload
# ---------------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload survey file (CSV or Excel)",
    type=["csv", "xlsx"]
)

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)

    question_map = load_question_map()

    # -----------------------------------------------------
    # RAW survey path (Airtable-style)
    # -----------------------------------------------------
    if is_raw_survey(df_raw):
        st.info("Raw Airtable-style survey detected.")

        df_raw.columns = [c.lower() for c in df_raw.columns]

        if "client" not in df_raw.columns:
            st.error("Raw survey file must contain a 'client' column.")
            st.stop()

        client_name = st.selectbox(
            "Select client",
            sorted(df_raw["client"].dropna().unique())
        )

        df_raw_client = df_raw[df_raw["client"] == client_name]

        df = convert_raw_survey(
            df_raw=df_raw_client,
            client_name=client_name,
            question_map=question_map
        )

    # -----------------------------------------------------
    # STANDARDIZED survey path
    # -----------------------------------------------------
    else:
        st.info("Standardized survey format detected.")

        if "client" not in df_raw.columns:
            st.error("Standardized file must contain a 'client' column.")
            st.stop()

        client_name = st.selectbox(
            "Select client",
            sorted(df_raw["client"].dropna().unique())
        )

        df = df_raw[df_raw["client"] == client_name]

    # -----------------------------------------------------
    # Scoring & preview
    # -----------------------------------------------------
    scores = compute_team_scores(df)

    st.subheader("TEAMS Snapshot (Preview)")
    st.bar_chart(scores)

    # -----------------------------------------------------
    # Generate PDF
    # -----------------------------------------------------
    if st.button("Generate One-Page PDF"):
        with st.spinner("Generating executive diagnostic..."):
            ai_json = generate_ai_analysis(scores.to_dict())

        ai_output = json.loads(ai_json)

        story = ai_output["story"]
        dimension_notes = ai_output["dimension_notes"]
        ceo_moves = ai_output["ceo_moves"]

        snapshot_rows = []
        for dim, score in scores.items():
            snapshot_rows.append([
                dim,
                score_status(score),
                dimension_notes.get(dim, "")
            ])

        radar_path = os.path.join(
            tempfile.gettempdir(),
            "teams_radar.png"
        )

        generate_radar_chart(
            scores.to_dict(),
            radar_path
        )

        tmp_pdf = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        )

        visual_insight = generate_visual_insight(scores.to_dict())

        build_pdf(
            tmp_pdf.name,
            client_name,
            story,
            snapshot_rows,
            ceo_moves,
            radar_path,
            visual_insight
        )

        with open(tmp_pdf.name, "rb") as f:
            st.download_button(
                "Download Executive One-Pager (PDF)",
                f,
                file_name=f"{client_name}_Executive_Team_Diagnostic.pdf"
            )
