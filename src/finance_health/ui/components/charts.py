from __future__ import annotations

import altair as alt
import polars as pl


def monthly_cashflow_chart(df: pl.DataFrame, series: list[str] | None = None, kind: str = "line"):
    """Interactive monthly cashflow chart.

    - series: subset of ["income", "expense", "net"] to display
    - kind: "line" or "bar"
    """
    if df.is_empty():
        return None
    pdf = df.sort("month").to_pandas()
    long = pdf.melt(id_vars=["month"], value_vars=["income", "expense", "net"], var_name="type", value_name="amount")
    if series:
        long = long[long["type"].isin(series)]

    base = alt.Chart(long).encode(
        x=alt.X("month:T", title="Month"),
        y=alt.Y("amount:Q", title="Amount ($)"),
        color=alt.Color("type:N", scale=alt.Scale(scheme="tableau10")),
        tooltip=["month:T", "type:N", "amount:Q"],
    )

    selector = alt.selection_point(fields=["type"], bind="legend")
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.25))

    if kind == "bar":
        chart = base.mark_bar()
    else:
        chart = base.mark_line(point=True)

    chart = chart.encode(opacity=opacity).add_params(selector).properties(height=320).interactive()
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
