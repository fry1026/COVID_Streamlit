import streamlit as st
import plotly.express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from streamlit.components import v1 as components

TRANSPARENT_COLOR = 'rgba(0,0,0,0)'


def graph_global_case_development(df_world, continents_selected):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for c in continents_selected:
        df_graph = df_world[df_world.location == c]
        fig.add_trace(go.Scatter(x=df_graph.date, y=df_graph.new_cases_smoothed, name=f'New Cases {c}'),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=df_graph.date, y=df_graph.reproduction_rate, name=f'Reproduction rate {c}',
                                 line=dict(width=1, dash='dash')), secondary_y=True)
    fig.update_layout(
        title=dict(
            text='<b>New cases</b>',
            # x=0.5,
            y=0.86,
            font=dict(
                family="arial",  #
                size=22,
                # color='#000000'
            )
        ),
        hovermode='x',
        showlegend=True
        # , title_text=str('Court Data for ' + str(year))
        , paper_bgcolor=TRANSPARENT_COLOR
        , plot_bgcolor=TRANSPARENT_COLOR
    )
    return fig


def graph_incident_development_for_countries(dff):
    fig = px.line(dff, x='date', y='Incident_rate', color='location', title="Weekly incident rate")
    fig.update_traces(line=dict(width=1))
    # fig.update_layout(showlegend=False)
    fig.update_layout(
        paper_bgcolor=TRANSPARENT_COLOR,
        plot_bgcolor=TRANSPARENT_COLOR,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
        title=dict(
            font=dict(
                family="Source Sans Pro",
                size=24,
            ))
    )

    fig.update_yaxes(visible=False)
    return fig


def bootstrap_card(country, cases, trend_value, trend_value_formatted, country_code, population, incident_rate=0):
    return components.html(f"""
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

        <div class="card">
          <div class="card-header" style="white-space:nowrap">
            <div> <img src="https://raw.githubusercontent.com/lipis/flag-icons/main/flags/4x3/{country_code}.svg" height="20" alt="test image" align="style="display:inline;"/>
            <div style="display:inline; white-space:nowrap;">{country}</div>
            </div>
          </div>
        <div class="card-body">
        <h5 class="card-title">{cases} <sub>daily new cases (smoothed)</sub></h5>

        {'<p> <span style="color:red">' if trend_value > 0 else '<span style="color:green">'} <b>{trend_value_formatted}</b> {'&#8593;' if trend_value > 0 else '&#8595;'} </span><sub>weekly change</sub></p>
        <span class="card-title">{int(population):,} Population</span>
        <span class="card-title">{int(incident_rate)} Incident rate</span>
      </div>
    </div>
  </div>
        """, height=250)


def graph_cases_and_change_by_country(df_data, country):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_data = df_data.query(f'location == "{country}"')[
        ['date', 'total_cases', 'new_cases_smoothed', 'new_cases', 'case_growth', 'case_growth_7d', 'case_growth_30d']]
    df_data['change_color'] = df_data['case_growth_7d'].apply(lambda x: 'red' if x > 0 else 'green')

    y1_up = 1.1 * (df_data.new_cases_smoothed.max())
    y1_low = 1.1 * (df_data.new_cases_smoothed.max() / (df_data.case_growth_7d.max() / df_data.case_growth_7d.min()))
    y2_up = 1.1 * (df_data.case_growth_7d.max())
    y2_low = 1.1 * (df_data.case_growth_7d.min())

    fig.update_yaxes(range=[y1_low, y1_up], secondary_y=True)
    fig.update_yaxes(range=[y2_low, y2_up], secondary_y=False)

    fig.update_layout(
        showlegend=True,
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='x'
    )

    # fig.add_trace(go.Bar(x=df_sg.date, y=df_sg.case_growth, name="trend (daily)"), secondary_y=True)
    fig.add_trace(go.Scatter(x=df_data.date,
                             y=df_data.new_cases_smoothed,
                             name="New Cases (smoothed)",
                             marker={'color': 'blue'},
                             hovertemplate='New Cases: %{y:.0f}<extra></extra>'
                             ), secondary_y=True)

    fig.add_trace(go.Scatter(x=df_data.date,
                             y=df_data.new_cases,
                             mode='markers',
                             name="New Cases",
                             marker=dict(size=2, line=dict(width=0.5, color='red'))
                             ), secondary_y=True)

    fig.add_trace(go.Bar(
        x=df_data.date,
        y=df_data.case_growth_7d,
        marker={'color': df_data.change_color},
        name="Weekly % Change",
        hovertemplate='Weekly Change: %{y:%.2f}<extra></extra>'
    ), secondary_y=False)

    # fig.add_trace((go.Scatter(x=df_data.date,
    #                           y=df_data.case_growth_30d,
    #                           name="Monthly % Change",
    #                           hovertemplate='Monthly Change: %{y:%.2f}<extra></extra>')), secondary_y=False)
    return fig


def graph_country_comparison_bar_charts(df_data, column, countries, title=''):
    selected_country_ids = [i for i, e in enumerate(df_data.location) if e in countries]
    colors = ['#FF0000' if i in selected_country_ids else '#0074D9'
              for i in range(len(df_data))]
    fig = dict({
        "data": [
            {
                "x": df_data["location"],
                "y": df_data[column],
                "type": "bar",
                "marker": {"color": colors},
            }
        ],
        "layout": {
            "xaxis": {"automargin": True},
            "yaxis": {
                "automargin": True,
                "title": {"text": ""},
            },
            "height": 250,
            "margin": {"t": 30, "l": 10, "r": 10},
            "title": {"text": title, },
            'font': {
                # 'family': "Source Sans Pro",
                'size': 16, }
        }})
    return fig


def space(n, col=None):
    for _ in range(n):
        if col:
            col.write('\n')
        else:
            st.write('\n')
