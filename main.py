import pandas as pd
import plotly.express as px
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

st.set_page_config(layout="wide")
POPULATION_LABELS = {'Very small': '<1M', 'Small': '1M-10M', 'Medium': '10M-50M', 'Large': '50M-100M',
                     'Very Large': '100M-1B', 'Extra Large': '>1B'}
POPULATION_BINS = [0, 1e6, 1e7, 5e7, 1e8, 1e9, 2e10]


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
col1, col2 = st.columns([6, 3])

col1.write('#### Development globally')
dfw = df_world[df_world.location.isin(continents_selected)]
col1.write("#### New Cases")
col1.plotly_chart(px.line(dfw, x='date', y='new_cases_smoothed', color='location'), use_container_width=True)

# col1.write("#### Incident rate")
# col1.plotly_chart(px.line(dfw, x='date', y='Incident_rate', color='location'), use_container_width=True)

# col1.plotly_chart(px.line(df_world, x='date', y='new_cases_smoothed'),use_container_width=True)
st.write("#### Cases by country size")
st.plotly_chart(px.treemap(df_latest, path=[px.Constant('World'), 'country_size', 'location'], values='population', color='Incident_rate', color_continuous_scale='rdbu_r', color_continuous_midpoint=0), use_container_width=True)

space(5, col2)
col2.write("#### Countries with Incident Rate over 400")
with col2:
    df_table = df_latest[df_latest.Incident_rate >= 400][
        ['location', 'Incident_rate', 'new_cases_smoothed']].sort_values(
        by=['Incident_rate'], ascending=False).copy()
    gb = GridOptionsBuilder.from_dataframe(df_table)
    # gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_pagination()
    grid_options = gb.build()
    selected_data = AgGrid(df_table, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED)
    # AgGrid(df_latest[['location', 'Incident_rate', 'new_cases']].sort_values(
    #     by=['Incident_rate'],
    #     ascending=False).head(10))
# col2.table(
#     df_latest[['location', 'weekly_incidence_per_100k_pop', 'new_cases']].sort_values(
#         by=['weekly_incidence_per_100k_pop'],
#         ascending=False).head(10))

st.write('***')
st.subheader(f'2. Country View')
i = [i for i, e in enumerate(all_countries) if e == 'Singapore'][0]
country = st.selectbox('Filter to:', all_countries, index=i)
df_c = df[df.location == country]
st.plotly_chart(px.line(df_c, x=df_c.date, y=df_c.new_cases, ))

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
        df_latest[df.location.isin(countries)][
            ['location', 'Incident_rate', 'week_incidence_rank', 'new_cases_smoothed']])
    analysis_types = {'new_cases': "New Cases",
                      'Incident_rate': "Weekly Incident Rate",
                      'total_cases': "Total Cases",
                      'total_vaccinations': "Total Vaccinations",
                      'icu_patients': "ICU Patients",
                      'population': "Population",
                      'total_deaths': "Total Deaths",
                      'new_deaths_smoothed': "New Deaths"}
    colY,colZ,colEmpty = st.columns([2,2,8])
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

# https://towardsdatascience.com/7-reasons-why-you-should-use-the-streamlit-aggrid-component-2d9a2b6e32f0
if show_data:
    latest = st.checkbox("Show latest day only", value=True)
    st.subheader("Detailed Data")
    if latest:
        df_grid = df_latest.copy()
        # st.write(selected_data)
    else:
        df_grid = dff.copy()
    gb = GridOptionsBuilder.from_dataframe(df_grid)
    gb.configure_pagination()
    gb.configure_side_bar()
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()
    selected_data = AgGrid(df_grid, gridOptions=grid_options, enable_enterprise_modules=True,
                           update_mode=GridUpdateMode.SELECTION_CHANGED)
