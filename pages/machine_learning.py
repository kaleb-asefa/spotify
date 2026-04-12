from __future__ import annotations

import pandas as pd
import streamlit as st

from models.skip_model import train_skip_prediction_model



def render(df: pd.DataFrame):
    st.title("Machine Learning: Skip Probability Prediction")

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    with st.expander("Model Overview", expanded=True):
        st.markdown(
            """
This section trains a **Logistic Regression** model to estimate the probability that a song is skipped.

Features include:
- play duration and listening hour
- platform
- reason start/end context
- shuffle, offline, and incognito behavior
            """
        )

    if st.button("Train Skip Prediction Model"):
        with st.spinner("Training model..."):
            result = train_skip_prediction_model(df)

        if result.get("status") != "ok":
            st.error("Not enough balanced song data to train a robust classifier.")
            return

        c1, c2 = st.columns(2)
        c1.metric("Accuracy", f"{result['accuracy']:.3f}")
        c2.metric("ROC AUC", f"{result['roc_auc']:.3f}")

        report = pd.DataFrame(result["report"]).transpose().reset_index().rename(columns={"index": "label"})
        st.subheader("Classification Report")
        st.dataframe(report, use_container_width=True)

        st.info(
            "Model assumptions: relationships are approximately linear in log-odds space, "
            "and future listening context follows similar behavior to historical data."
        )
