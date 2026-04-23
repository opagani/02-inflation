import marimo

__generated_with = "0.23.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # G7 Inflation Comparison: FRED & World Bank Data

    This notebook fetches annual inflation rates for all G7 countries from both the **World Bank API** and **FRED (Federal Reserve Economic Data)**, then visualizes them with interactive Plotly line charts since 1980.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setup & Imports
    """)
    return


@app.cell
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import wbdata
    import requests
    from datetime import datetime
    import warnings
    warnings.filterwarnings('ignore')

    print(f"Pandas version: {pd.__version__}")
    return datetime, go, pd, px, requests, wbdata


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Configuration

    Define G7 countries, their ISO codes, and friendly names for plotting.
    """)
    return


@app.cell
def _(datetime):
    G7_COUNTRIES = {
        'CAN': 'Canada',
        'FRA': 'France',
        'DEU': 'Germany',
        'ITA': 'Italy',
        'JPN': 'Japan',
        'GBR': 'United Kingdom',
        'USA': 'United States'
    }

    COUNTRY_CODES = list(G7_COUNTRIES.keys())
    COUNTRY_NAMES = list(G7_COUNTRIES.values())
    START_YEAR = 1980
    END_YEAR = datetime.now().year
    return COUNTRY_CODES, END_YEAR, START_YEAR


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Fetch World Bank Data

    Use the World Bank API (via `wbdata`) to get annual consumer price inflation (`FP.CPI.TOTL.ZG`) for all G7 countries.
    """)
    return


@app.cell
def _(COUNTRY_CODES, END_YEAR, START_YEAR, pd, wbdata):
    wb_indicators = {'FP.CPI.TOTL.ZG': 'inflation_rate'}
    wb_data = wbdata.get_dataframe(
        indicators=wb_indicators,
        country=COUNTRY_CODES,
        date=(f'{START_YEAR}-01-01', f'{END_YEAR}-12-31'),
        parse_dates=False,
        freq='Y'
    )

    df_wb = (
        wb_data
        .reset_index()
        .rename(columns={'country': 'country_name', 'date': 'year'})
        .assign(
            source='World Bank',
            year=lambda d: d.year.astype('Int16'),
            inflation_rate=lambda d: pd.to_numeric(d.inflation_rate, errors='coerce'),
            country_name=lambda d: d.country_name.astype('category')
        )
        .loc[:, ['year', 'country_name', 'inflation_rate', 'source']]
        .dropna(subset=['inflation_rate'])
    )

    df_wb.info(memory_usage='deep')
    df_wb.head()
    return (df_wb,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Fetch FRED Data

    FRED mirrors World Bank inflation series under codes like `FPCPITOTLZG***`.
    We attempt to fetch via direct `requests` to the FRED API (no key required for demo limits).
    If unavailable, we gracefully fall back to World Bank data only since the series are identical.
    """)
    return


@app.cell
def _(pd, requests):
    fred_series = {
        'FPCPITOTLZGCAN': 'Canada',
        'FPCPITOTLZGFRA': 'France',
        'FPCPITOTLZGDEU': 'Germany',
        'FPCPITOTLZGITA': 'Italy',
        'FPCPITOTLZGJPN': 'Japan',
        'FPCPITOTLZGGBR': 'United Kingdom',
        'FPCPITOTLZGUSA': 'United States'
    }

    fred_dfs = []
    for series_id, country_name in fred_series.items():
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&file_type=json&api_key=demo"
            r = requests.get(url, timeout=30)
            if r.status_code != 200:
                continue
            data = r.json().get('observations', [])
            if not data:
                continue
            s = (
                pd.DataFrame(data)
                .assign(
                    country_name=country_name,
                    source='FRED',
                    year=lambda d: pd.to_datetime(d['date']).dt.year.astype('Int16'),
                    inflation_rate=lambda d: pd.to_numeric(d['value'], errors='coerce')
                )
                .loc[:, ['year', 'country_name', 'inflation_rate', 'source']]
                .dropna(subset=['inflation_rate'])
            )
            fred_dfs.append(s)
        except Exception as e:
            print(f"Failed to fetch {series_id} ({country_name}): {e}")

    if fred_dfs:
        df_fred = (
            pd.concat(fred_dfs, ignore_index=True)
            .assign(
                country_name=lambda d: d.country_name.astype('category')
            )
            .loc[:, ['year', 'country_name', 'inflation_rate', 'source']]
        )
        print(f"FRED data fetched: {len(df_fred)} rows")
    else:
        df_fred = pd.DataFrame(columns=['year', 'country_name', 'inflation_rate', 'source'])
        print("No FRED data available — using World Bank only.")

    df_fred.info(memory_usage='deep')
    df_fred.head()
    return (df_fred,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Combine & Validate Data

    Merge both sources to compare values and ensure consistency. We keep World Bank as the primary source and flag where FRED differs materially.
    """)
    return


@app.cell
def _(df_fred, df_wb, display, pd):
    df_combined = (
        pd.concat([df_wb, df_fred], ignore_index=True)
        .pipe(lambda d: d.assign(
            country_name=d.country_name.cat.remove_unused_categories() if hasattr(d.country_name, 'cat') else d.country_name
        ))
    )

    if not df_fred.empty:
        comparison = (
            df_combined
            .pivot_table(
                index=['year', 'country_name'],
                columns='source',
                values='inflation_rate',
                aggfunc='mean'
            )
            .dropna()
            .assign(diff=lambda d: (d['FRED'] - d['World Bank']).abs().round(3))
        )
        print("Max absolute difference between FRED and World Bank:", comparison['diff'].max())
        display(comparison.head(10))
    else:
        print("No FRED data to compare — using World Bank only.")
    return (df_combined,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prepare Plotting Data

    We use the **World Bank** data as our canonical source for the main comparison plot.
    We also compute an unweighted G7 average per year.
    """)
    return


@app.cell
def _(START_YEAR, df_wb):
    df_plot = (
        df_wb
        .loc[lambda d: d.year >= START_YEAR]
        .sort_values(['country_name', 'year'])
        .reset_index(drop=True)
    )

    # Compute unweighted G7 average
    df_avg = (
        df_plot
        .groupby('year', observed=True)['inflation_rate']
        .mean()
        .round(3)
        .reset_index()
        .assign(country_name='G7 Average', source='Computed')
        .astype({'year': 'Int16', 'country_name': 'category'})
    )

    print("Min inflation:", df_plot.inflation_rate.min(), "Max inflation:", df_plot.inflation_rate.max())
    print(f"G7 Average rows: {len(df_avg)}")
    df_plot.head()
    return df_avg, df_plot


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Plot 1: All G7 Countries + G7 Average
    """)
    return


@app.cell
def _(df_avg, df_plot, go, px):
    fig1 = px.line(
        df_plot,
        x='year',
        y='inflation_rate',
        color='country_name',
        title='G7 Annual Inflation Rates (1980–present) — World Bank Data',
        labels={'inflation_rate': 'Inflation Rate (%)', 'year': 'Year', 'country_name': 'Country'},
        hover_data={'inflation_rate': ':.2f'}
    )

    # Add G7 Average as a dashed black line
    fig1.add_trace(
        go.Scatter(
            x=df_avg['year'],
            y=df_avg['inflation_rate'],
            mode='lines',
            name='G7 Average',
            line=dict(color='black', width=3, dash='dash'),
            hovertemplate='G7 Average<br>Year: %{x}<br>Inflation: %{y:.2f}%<extra></extra>'
        )
    )

    fig1.update_traces(line=dict(width=2.5))
    fig1.update_traces(selector=dict(name='G7 Average'), line=dict(width=3, dash='dash'))
    fig1.update_layout(
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5),
        height=600
    )
    fig1.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Plot 2: Faceted View (One Subplot per Country)
    """)
    return


@app.cell
def _(df_plot, px):
    fig2 = px.line(
        df_plot,
        x='year',
        y='inflation_rate',
        facet_col='country_name',
        facet_col_wrap=4,
        title='G7 Annual Inflation Rates by Country (1980–present)',
        labels={'inflation_rate': 'Inflation (%)', 'year': 'Year'},
    )

    fig2.update_traces(line=dict(width=2))
    fig2.update_layout(
        height=700,
        showlegend=False
    )
    fig2.for_each_annotation(lambda a: a.update(text=a.text.split('=')[1]))
    fig2.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Plot 3: Source Comparison for the United States

    Overlay FRED and World Bank series for the US to show they are effectively identical.
    """)
    return


@app.cell
def _(START_YEAR, df_combined, df_fred, px):
    if not df_fred.empty:
        df_us = (
            df_combined
            .loc[lambda d: d.country_name == 'United States']
            .loc[lambda d: d.year >= START_YEAR]
            .sort_values(['source', 'year'])
            .reset_index(drop=True)
        )

        fig3 = px.line(
            df_us,
            x='year',
            y='inflation_rate',
            color='source',
            title='US Inflation: FRED vs World Bank (1980–present)',
            labels={'inflation_rate': 'Inflation Rate (%)', 'year': 'Year', 'source': 'Data Source'},
            markers=True
        )

        fig3.update_traces(line=dict(width=2.5), marker=dict(size=6))
        fig3.update_layout(height=500, hovermode='x unified')
        fig3.show()
    else:
        print("No FRED data available — skipping source comparison plot.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary Statistics
    """)
    return


@app.cell
def _(df_plot):
    summary = (
        df_plot
        .groupby('country_name', observed=True)['inflation_rate']
        .agg(['count', 'mean', 'median', 'min', 'max', 'std'])
        .round(2)
        .sort_values('mean', ascending=False)
    )
    summary
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    *Notebook generated programmatically. Data sources: World Bank (`FP.CPI.TOTL.ZG`) and FRED (`FPCPITOTLZG...` series).*
    """)
    return


if __name__ == "__main__":
    app.run()
