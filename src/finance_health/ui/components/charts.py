from __future__ import annotations

import altair as alt
import polars as pl


def monthly_cashflow_chart(df: pl.DataFrame):
    if df.is_empty():
        return None
    pdf = df.sort("month").to_pandas()
    long = pdf.melt(id_vars=["month"], value_vars=["income", "expense", "net"], var_name="type", value_name="amount")
    chart = (
        alt.Chart(long)
        .mark_bar()
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("amount:Q", title="Amount ($)"),
            color=alt.Color("type:N", scale=alt.Scale(scheme="tableau10")),
            tooltip=["month:T", "type:N", "amount:Q"],
        )
        .properties(height=300)
    )
    return chart


def categories_chart(df: pl.DataFrame, title: str = "Top Categories/Merchants"):
    if df.is_empty():
        return None
    pdf = df.to_pandas()
    chart = (
        alt.Chart(pdf)
        .mark_bar()
        .encode(
            x=alt.X("spend:Q", title="Spend ($)"),
            y=alt.Y(pdf.columns[0] + ":N", sort='-x', title=pdf.columns[0].capitalize()),
            tooltip=[pdf.columns[0], "spend"],
            color=alt.value("#4C78A8"),
        )
        .properties(title=title, height=300)
    )
    return chart
