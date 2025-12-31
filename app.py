import streamlit as st
import pandas as pd
import tempfile
import os
import json
import re
import unicodedata

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
# Text normalization
# ---------------------------------------------------------
def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ---------------------------------------------------------
# Load question → category mapping
# ---------------------------------------------------------
def load_question_map(path="questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    return {
        normalize_text(q["text"]): q["category"]
        for q in questions
    }


# ---------------------------------------------------------
# Detect raw vs standardized survey
# ---------------------------------------------------------
def is_raw_survey(df):
    return "Timestamp" in df.columns and "question" not in df.columns


# ---------------------------------------------------------
# Convert raw (wide) survey → standardized (long)
# ---------------------------------------------------------
def convert_raw_survey(df_raw, client_name, question_map):
    timestamp_col = "Timestamp"

    # Only keep real question columns
    question_cols = [
        c for c in df_raw.columns
        if normalize_text(c) in question_map
    ]

    if not question_cols:
        raise ValueError("No survey question columns matched questions.json")

    df_long = df_raw.melt(
        id_vars=[timestamp_col],
        value_vars=question_cols,
        var_name="question",
        value_name="score"
    )

    df_long = df_long.dropna(subset=["score"])

    df_long["question"] = df_long["question"].apply(normalize_text)
    df_long["category"] = df_long["question"].map(question_map)

    missing = df_long[df_long["category"].isna()]["question"].unique()
    if len(missing) > 0:
        raise ValueError(f"Unmapped questions found: {missing}")

    df_long["client"] = client_name
    df_long["timestamp"] = df_long[timestamp_col]

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
    # RAW survey path (multi-client supported)
    # -----------------------------------------------------
    if is_raw_survey(df_raw):
        st.info("Raw survey format detected.")

        if "Client" not in df_raw.columns:
            st.error("Raw survey file must contain a 'Client' column.")
            st.stop()

        client_name = st.selectbox(
            "Select client",
            sorted(df_raw["Client"].dropna().unique())
        )

        df_raw_client = df_raw[df_raw["Client"] == client_name]

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
