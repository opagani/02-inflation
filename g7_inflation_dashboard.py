import marimo

__generated_with = "0.23.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# 🌍 G7 Inflation Dashboard

Interactive dashboard comparing annual inflation rates across all G7 countries since 1980.
Data sourced from the **World Bank API** (indicator: `FP.CPI.TOTL.ZG`).
""")
    return


@app.cell
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import wbdata
    from datetime import datetime
    return datetime, go, pd, px, wbdata


@app.cell
def _(pd, wbdata):
    G7_COUNTRIES = {
        'CAN': 'Canada',
        'FRA': 'France',
        'DEU': 'Germany',
        'ITA': 'Italy',
        'JPN': 'Japan',
        'GBR': 'United Kingdom',
        'USA': 'United States'
    }

    wb_data = wbdata.get_dataframe(
        indicators={'FP.CPI.TOTL.ZG': 'inflation_rate'},
        country=list(G7_COUNTRIES.keys()),
        date=('1980-01-01', '2024-12-31'),
        parse_dates=False,
        freq='Y'
    )

    df = (
        wb_data
        .reset_index()
        .rename(columns={'country': 'Country', 'date': 'Year', 'inflation_rate': 'Inflation'})
        .assign(
            Year=lambda d: d.Year.astype(int),
            Inflation=lambda d: pd.to_numeric(d.Inflation, errors='coerce'),
            Country=lambda d: d.Country.astype('category')
        )
        .dropna(subset=['Inflation'])
    )
    return (df,)


@app.cell
def _(df, mo):
    countries = mo.ui.multiselect(
        options=df['Country'].unique().tolist(),
        value=df['Country'].unique().tolist(),
        label="Countries"
    )

    year_range = mo.ui.range_slider(
        start=1980,
        stop=2024,
        step=1,
        value=(1980, 2024),
        label="Years"
    )

    show_avg = mo.ui.checkbox(
        value=True,
        label="Show G7 Average"
    )

    chart_type = mo.ui.dropdown(
        options=["Combined", "Faceted", "Heatmap"],
        value="Combined",
        label="View"
    )

    controls = mo.hstack([countries, year_range, show_avg, chart_type], justify="start")
    mo.md("## 🎛️ Controls")
    controls
    return chart_type, controls, countries, show_avg, year_range


@app.cell
def _(countries, df, show_avg, year_range):
    filtered = (
        df
        .loc[lambda d: d.Country.isin(countries.value)]
        .loc[lambda d: (d.Year >= year_range.value[0]) & (d.Year <= year_range.value[1])]
        .reset_index(drop=True)
    )

    avg_df = None
    if show_avg.value and not filtered.empty:
        avg_df = (
            filtered
            .groupby('Year', observed=True)['Inflation']
            .mean()
            .round(2)
            .reset_index()
            .assign(Country='G7 Average')
        )
    return avg_df, filtered


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 📈 Chart")
    return


@app.cell
def _(avg_df, chart_type, filtered, go, mo, px, show_avg, year_range):
    if chart_type.value == "Combined":
        fig = px.line(
            filtered,
            x='Year',
            y='Inflation',
            color='Country',
            title=f"G7 Annual Inflation Rates ({year_range.value[0]}–{year_range.value[1]})",
            labels={'Inflation': 'Inflation Rate (%)', 'Year': 'Year'},
            hover_data={'Inflation': ':.2f'}
        )

        if show_avg.value and avg_df is not None:
            fig.add_trace(
                go.Scatter(
                    x=avg_df['Year'],
                    y=avg_df['Inflation'],
                    mode='lines',
                    name='G7 Average',
                    line=dict(color='black', width=3, dash='dash'),
                    hovertemplate='G7 Average<br>Year: %{x}<br>Inflation: %{y:.2f}%<extra></extra>'
                )
            )

        fig.update_traces(line=dict(width=2.5))
        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5),
            height=600
        )

    elif chart_type.value == "Faceted":
        fig = px.line(
            filtered,
            x='Year',
            y='Inflation',
            facet_col='Country',
            facet_col_wrap=4,
            title=f"G7 Annual Inflation Rates by Country ({year_range.value[0]}–{year_range.value[1]})",
            labels={'Inflation': 'Inflation (%)', 'Year': 'Year'}
        )
        fig.update_traces(line=dict(width=2))
        fig.update_layout(height=700, showlegend=False)
        fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[1]))

    else:  # Heatmap
        pivot = filtered.pivot_table(index='Country', columns='Year', values='Inflation', aggfunc='mean')
        fig = px.imshow(
            pivot,
            aspect='auto',
            color_continuous_scale='RdYlBu_r',
            title=f"Inflation Heatmap ({year_range.value[0]}–{year_range.value[1]})",
            labels={'color': 'Inflation (%)'}
        )
        fig.update_layout(height=500)

    mo.plain(fig)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 📊 Summary Statistics")
    return


@app.cell
def _(avg_df, filtered, mo, pd, show_avg):
    summary = (
        filtered
        .groupby('Country', observed=True)['Inflation']
        .agg(['count', 'mean', 'median', 'min', 'max', 'std'])
        .round(2)
        .sort_values('mean', ascending=False)
        .reset_index()
    )

    if show_avg.value and avg_df is not None:
        overall_avg = (
            filtered
            .groupby('Year', observed=True)['Inflation']
            .mean()
            .agg(['count', 'mean', 'median', 'min', 'max', 'std'])
            .round(2)
        )
        overall_avg['Country'] = 'G7 Average'
        summary = pd.concat([summary, pd.DataFrame([overall_avg])], ignore_index=True)

    mo.ui.table(summary, selection=None, pagination=False, label="Stats")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 💾 Download Data")
    return


@app.cell
def _(datetime, filtered, mo):
    csv_data = filtered.to_csv(index=False)
    mo.download(csv_data.encode('utf-8'), filename="g7_inflation_data.csv", mimetype="text/csv")
    mo.md(f"Data: World Bank API (FP.CPI.TOTL.ZG) | {len(filtered)} rows | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return


if __name__ == "__main__":
    app.run()
