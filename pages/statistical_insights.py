from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm

from utils.stats import confidence_interval_mean, weekday_weekend_hypothesis_test, zscore_anomaly_days



def render(df: pd.DataFrame):
    st.title("Statistical Insight Section")

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    daily = df.groupby("date", as_index=False)["play_hours"].sum()

    ci = confidence_interval_mean(daily["play_hours"], confidence=0.95)
    if ci:
        st.success(
            f"95% Confidence Interval for average daily listening hours: [{ci[0]:.2f}, {ci[1]:.2f}]"
        )
    else:
        st.info("Not enough daily samples for confidence interval estimation.")

    threshold = st.slider("Z-score anomaly threshold", min_value=1.5, max_value=4.0, value=2.5, step=0.1)
    anomalies = zscore_anomaly_days(daily, threshold=threshold)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Outlier Listening Days")
        if anomalies.empty:
            st.write("No anomaly days detected at current threshold.")
        else:
            st.dataframe(anomalies, use_container_width=True)

    with c2:
        st.subheader("Distribution of Daily Hours")
        x = daily["play_hours"].dropna().to_numpy()
        if len(x) > 1:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.hist(x, bins=20, density=True, alpha=0.6)
            mu, sigma = x.mean(), x.std(ddof=1)
            xs = np.linspace(x.min(), x.max(), 300)
            ax.plot(xs, norm.pdf(xs, mu, sigma), linewidth=2)
            ax.set_title("Daily Listening Hours Histogram")
            ax.set_xlabel("Hours")
            ax.set_ylabel("Density")
            st.pyplot(fig)
        else:
            st.write("Not enough data for distribution plot.")

    st.subheader("Hypothesis Test: Weekday vs Weekend Listening")
    result = weekday_weekend_hypothesis_test(df)

    if result.get("status") != "ok":
        st.info("Insufficient data for hypothesis testing.")
    else:
        p_value = result["p_value"]
        st.write(
            f"Weekday mean: {result['weekday_mean']:.2f} min/day | "
            f"Weekend mean: {result['weekend_mean']:.2f} min/day"
        )
        st.write(f"t-statistic: {result['t_stat']:.3f}, p-value: {p_value:.4f}")

        if p_value < 0.05:
            st.success(
                "Result is statistically significant at alpha=0.05. Weekday and weekend listening differ."
            )
        else:
            st.warning(
                "Result is not statistically significant at alpha=0.05. No strong evidence of a difference."
            )

    with st.expander("Interpretation Notes"):
        st.markdown(
            """
- Confidence interval estimates the plausible range for your average daily listening.
- Z-score anomaly detection flags unusually high/low listening days.
- Hypothesis test compares weekday vs weekend daily listening means.
- A p-value below 0.05 suggests a meaningful behavioral difference.
            """
        )
