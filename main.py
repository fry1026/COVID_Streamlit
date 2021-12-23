import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
POPULATION_LABELS = {'Very small': '<1M', 'Small': '1M-10M', 'Medium': '10M-50M', 'Large': '50M-100M',
                     'Very Large': '100M-1B', 'Extra Large': '>1B'}
POPULATION_BINS = [0, 1e6, 1e7, 5e7, 1e8, 1e9, 2e10]
TRANSPARENT_COLOR = 'rgba(0,0,0,0)'
NUMBER_OF_COLUMNS_IN_CARD_GRID = 4


def bootstrap_card(country, cases, trend_value, trend_value_formatted):
    return components.html(f"""
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

        <div class="card">
          <div class="card-header">
            {country}
          </div>
        <div class="card-body">
        <h5 class="card-title">{cases} <sub>new cases</sub></h5>


        {'<p style="color:red">' if trend_value > 0 else '<p style="color:green">'} {trend_value_formatted}  {'&#8593;' if trend_value > 0 else '&#8595;'}</p>

      </div>
    </div>
  </div>
        """, height=250)


def country_details(df_data, country):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_data = df.query(f'location == "{country}"')[
        ['date', 'total_cases', 'new_cases_smoothed', 'case_growth', 'case_growth_7d', 'case_growth_30d']]
    df_data['change_color'] = df['case_growth_7d'].apply(lambda x: 'red' if x > 0 else 'green')

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
                             name="New Cases",
                             marker={'color': 'blue'},
                             hovertemplate='New Cases: %{y:.0f}<extra></extra>'
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


def plotly_figure(df_data, column, countries, title=''):
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


@st.cache
def load_data():
    URL = 'https://covid.ourworldindata.org/data/owid-covid-data.csv'
    df = pd.read_csv(URL)
    df['Active_new_week'] = df.groupby('location')['new_cases'].transform(lambda x: x.rolling(window=7).sum().fillna(0))
    df['Incident_rate'] = (df.Active_new_week / df.population * 100000).fillna(0).astype(int)
    df['country_size'] = pd.cut(df['population'], bins=POPULATION_BINS, labels=POPULATION_LABELS.keys())
    df['case_growth'] = df.groupby('location')['new_cases_smoothed'].pct_change(periods=1).fillna(0)
    df['case_growth_7d'] = df.groupby('location')['new_cases_smoothed'].pct_change(periods=7).fillna(0)
    df['case_growth_7d_formatted'] = df.groupby('location')['new_cases_smoothed'].pct_change(periods=7).fillna(0).apply(
        '{:.0%}'.format)
    df['case_growth_30d'] = df.groupby('location')['new_cases_smoothed'].pct_change(periods=30).fillna(0)
    df.fillna({'Incident_rate': 0}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    return df


# Sidebar
st.sidebar.title("Filter options")
selected_sizes = {}
with st.sidebar.expander("Population filter"):
    for k, v in POPULATION_LABELS.items():
        selected_sizes[k] = st.checkbox(k, value=False if k == 'Very small' else True, help=v)
    # https://www.shanelynn.ie/pandas-drop-delete-dataframe-rows-columns/
country_size_filter = [k for k, v in selected_sizes.items() if v == True]
df = load_data()
df = df[df.country_size.isin(country_size_filter)]

df_world = df[df['continent'].isna() == True].copy()
continents = list(df[df['continent'].isna() == True].location.unique())
df = df[df['continent'].isna() == False].copy()

last_update = df.date.max()
all_countries = sorted(set(df.location))
df_latest = df[df.date == df.date.max()].copy()
df_latest['week_incidence_rank'] = df_latest['Incident_rate'].rank()

show_data = st.sidebar.checkbox("Show raw data")
st.sidebar.text(f'Data last updated {last_update}')

# Main Page
st.header('Overview')
st.subheader('1. World')
continents_selected = st.multiselect('Continent', continents, ['World'])
col1, col2 = st.columns([6, 4])

col1.write('#### Development globally')
dfw = df_world[df_world.location.isin(continents_selected)]
col1.write("#### New Cases")
TRANSPARENT_COLOR = 'rgba(0,0,0,0)'
fig = make_subplots(specs=[[{"secondary_y": True}]])
for c in continents_selected:
    df_graph = df_world[df_world.location == c]
    fig.add_trace(go.Line(x=df_graph.date, y=df_graph.new_cases_smoothed, name=f'New Cases {c}'), secondary_y=False)
    fig.add_trace(go.Line(x=df_graph.date, y=df_graph.reproduction_rate, name=f'Reproduction rate {c}',
                          line=dict(width=1, dash='dash')), secondary_y=True)
fig.update_layout(
    hovermode='x',
    showlegend=True
    # , title_text=str('Court Data for ' + str(year))
    , paper_bgcolor=TRANSPARENT_COLOR
    , plot_bgcolor=TRANSPARENT_COLOR
)
col1.plotly_chart(fig, use_container_width=True)

st.write("#### Cases by country size")
col2.write("#### Countries with Incident Rate over 400")
space(5, col2)

with col2:
    df_table = df_latest[df_latest.Incident_rate >= 400][
        ['location', 'Incident_rate', 'new_cases_smoothed', 'case_growth_7d_formatted']].sort_values(
        by=['Incident_rate'], ascending=False).copy()
    gb = GridOptionsBuilder.from_dataframe(df_table)
    # gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_pagination()
    grid_options = gb.build()
    selected_data = AgGrid(df_table, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED)
col1, col2 = st.columns(2)
col1.plotly_chart(px.treemap(df_latest, path=[px.Constant('World'), 'country_size', 'location'], values='population',
                             color='Incident_rate', color_continuous_scale='rdbu_r', color_continuous_midpoint=0),
                  use_container_width=True)
col2.plotly_chart(px.treemap(df_latest, path=[px.Constant('World'), 'continent', 'location'], values='population',
                             color='Incident_rate', color_continuous_scale='rdbu_r', color_continuous_midpoint=0),
                  use_container_width=True)

st.write('***')
st.subheader(f'2. Country View')
i = [i for i, e in enumerate(all_countries) if e == 'Singapore'][0]
country = st.selectbox('Filter to:', all_countries, index=i)
# df_c = df[df.location == country]
# st.plotly_chart(px.line(df_c, x=df_c.date, y=df_c.new_cases_smoothed, ))
st.plotly_chart(country_details(df, country), use_container_width=True)

st.write('***')
st.subheader("3. Development of Cases")

countries = st.multiselect("Select countries", all_countries,
                           ['Singapore', 'Germany', 'United States', 'United Kingdom'])
colA, colB = st.columns([6, 4])

if countries:
    dff = df[df.location.isin(countries)]
    fig = px.line(dff, x='date', y='Incident_rate', color='location', title="Weekly incident rate")
    fig.update_traces(line=dict(width=1))
    # fig.update_layout(showlegend=False)
    fig.update_layout(
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
    colA.plotly_chart(fig, use_container_width=True)
    colB.write('#### Country Incident Rate and Ranking')
    colB.dataframe(
        df_latest[df_latest.location.isin(countries)][
            ['location', 'Incident_rate', 'week_incidence_rank', 'new_cases_smoothed']])
    analysis_types = {'new_cases': "New Cases",
                      'Incident_rate': "Weekly Incident Rate",
                      # 'case_growth': 'Growth rate of cases',
                      'total_cases': "Total Cases",
                      'case_growth_7d': 'Weekly Case Growth',
                      'population': "Population",
                      'total_deaths': "Total Deaths",
                      'new_deaths_smoothed': "New Deaths",
                      'total_vaccinations': "Total Vaccinations",
                      'icu_patients': "ICU Patients",
                      }
    df_countries_selected = df_latest[df_latest.location.isin(countries)]
    st.write('#### Details by Country')

    ncol = len(df_countries_selected)
    cols = st.columns(ncol)

    for i, (key, row) in enumerate(df_countries_selected.iterrows()):
        col = cols[i % NUMBER_OF_COLUMNS_IN_CARD_GRID]
        with col:
            bootstrap_card(row['location'], row['new_cases_smoothed'], row['case_growth_7d'],
                           row['case_growth_7d_formatted'])

space(2)
colY, colZ, colEmpty = st.columns([2, 2, 8])
analysis_type = colY.selectbox('Sort all charts by (desc)',
                               (analysis_types.keys()),
                               index=0)
records_number = colZ.selectbox('Show top countries', ['All', '10', '25', '50', '100'], index=1)
colEmpty.write('')
space(2)
df_latest = df_latest.sort_values(by=[analysis_type], ascending=False)
if records_number != 'All':
    df_latest = df_latest.head(int(records_number))

col1, col2 = st.columns(2)
for counter, (key, value) in enumerate(analysis_types.items()):
    if counter % 2 == 0:
        col1.plotly_chart(plotly_figure(df_latest, key, countries, value), use_container_width=True)
    else:
        col2.plotly_chart(plotly_figure(df_latest, key, countries, value), use_container_width=True)

st.write('***')

latest = False
if show_data:
    latest = st.checkbox("Show latest day only", value=True)
    st.subheader("Detailed Data")
    if latest:
        df_grid = df_latest.copy()

    else:
        df_grid = dff.copy()
    gb = GridOptionsBuilder.from_dataframe(df_grid)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()
    selected_data = AgGrid(df_grid, gridOptions=grid_options, enable_enterprise_modules=True,
                           update_mode=GridUpdateMode.SELECTION_CHANGED)
    # st.write(selected_data)
