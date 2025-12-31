import streamlit as st
import pandas as pd
import tempfile
import os
import json

from analysis_engine import (
    compute_team_scores,
    score_status,
    generate_ai_analysis
)
from pdf_generator import build_pdf
from visuals import generate_radar_chart


st.set_page_config(layout="wide")
st.title("Executive Team One-Page Diagnostic")

uploaded_file = st.file_uploader(
    "Upload survey file (CSV or Excel)",
    type=["csv", "xlsx"]
)

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    client_name = st.selectbox(
        "Select client",
        sorted(df["client"].unique())
    )

    df_client = df[df["client"] == client_name]

    scores = compute_team_scores(df_client)

    st.subheader("TEAMS Snapshot (Preview)")
    st.bar_chart(scores)

    if st.button("Generate One-Page PDF"):
        with st.spinner("Generating executive diagnostic..."):
            ai_json = generate_ai_analysis(scores.to_dict())

        # ---- Parse structured AI output ----
        ai_output = json.loads(ai_json)

        story = ai_output["story"]
        dimension_notes = ai_output["dimension_notes"]
        ceo_moves = ai_output["ceo_moves"]

        # ---- Build snapshot table rows ----
        snapshot_rows = []
        for dim, score in scores.items():
            snapshot_rows.append([
                dim,
                score_status(score),
                dimension_notes.get(dim, "")
            ])

        # ---- Generate radar chart image ----
        radar_path = os.path.join(
            tempfile.gettempdir(),
            "teams_radar.png"
        )

        generate_radar_chart(
            scores.to_dict(),
            radar_path
        )

        # ---- Build PDF ----
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        build_pdf(
            tmp_pdf.name,
            client_name,
            story,
            snapshot_rows,
            ceo_moves,
            radar_path
        )

        with open(tmp_pdf.name, "rb") as f:
            st.download_button(
                "Download Executive One-Pager (PDF)",
                f,
                file_name=f"{client_name}_Executive_Team_Diagnostic.pdf"
            )
