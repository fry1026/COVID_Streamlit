import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder
import country_converter as coco

from covid_helpers import bootstrap_card, graph_cases_and_change_by_country, graph_country_comparison_bar_charts, space, graph_global_case_development, \
    graph_incident_development_for_countries

st.set_page_config(layout="wide")
POPULATION_LABELS = {'Very small': '<1M', 'Small': '1M-10M', 'Medium': '10M-50M', 'Large': '50M-100M',
                     'Very Large': '100M-1B', 'Extra Large': '>1B'}
POPULATION_BINS = [0, 1e6, 1e7, 5e7, 1e8, 1e9, 2e10]
TRANSPARENT_COLOR = 'rgba(0,0,0,0)'
NUMBER_OF_COLUMNS_IN_CARD_GRID = 4

ANALYSIS_TYPES = {'new_cases': "New Cases",
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


#### Data loading and transformation ####
@st.cache(ttl=60 * 60)  # cache is valid for 1 hour
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


#### Sidebar ####
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
st.sidebar.markdown('***')
st.sidebar.markdown(f'Data last updated on {last_update.strftime("%d %b %Y")}')
st.sidebar.markdown('Source data from [OWID](https://github.com/owid/covid-19-data/tree/master/public/data)')
st.sidebar.markdown('Source code on [GitHub](https://github.com/fry1026/COVID_Streamlit)')

#### Main Page ####
st.header('Overview')

#### 1. World ####
st.subheader('1. World')
continents_selected = st.multiselect('Continent', continents, ['World'])
col1, col2 = st.columns([6, 4])

col1.write('#### Development globally')
dfw = df_world[df_world.location.isin(continents_selected)]
col1.write("#### New Cases")

col1.plotly_chart(graph_global_case_development(dfw, continents_selected), use_container_width=True)

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

#### 2. Country View ####
st.subheader(f'2. Country View')
i = [i for i, e in enumerate(all_countries) if e == 'Singapore'][0]
country = st.selectbox('Filter to:', all_countries, index=i)
st.plotly_chart(graph_cases_and_change_by_country(df, country), use_container_width=True)
st.write('***')

#### 3. Development of Cases ####
st.subheader("3. Development of Cases")

countries = st.multiselect("Select countries", all_countries,
                           ['Singapore', 'Germany', 'United States', 'United Kingdom'])
colA, colB = st.columns([6, 4])

if countries:
    dff = df[df.location.isin(countries)]

    colA.plotly_chart(graph_incident_development_for_countries(dff), use_container_width=True)
    colB.write('#### Country Incident Rate and Ranking')
    colB.dataframe(
        df_latest[df_latest.location.isin(countries)][
            ['location', 'Incident_rate', 'week_incidence_rank', 'new_cases_smoothed']])

    df_countries_selected = df_latest[df_latest.location.isin(countries)]
    st.write('#### Details by Country')

    ncol = len(df_countries_selected)
    cols = st.columns(ncol)

    for i, (key, row) in enumerate(df_countries_selected.iterrows()):
        col = cols[i % NUMBER_OF_COLUMNS_IN_CARD_GRID]
        with col:
            bootstrap_card(row['location'], f"{int(row['new_cases_smoothed']):,}", row['case_growth_7d'],
                           row['case_growth_7d_formatted'],
                           coco.convert(names=row['iso_code'], to='ISO2', not_found='de').lower(), row['population'],
                           row['Incident_rate'])

space(2)
colY, colZ, colEmpty = st.columns([2, 2, 8])
analysis_type = colY.selectbox('Sort all charts by (desc)',
                               (ANALYSIS_TYPES.keys()),
                               index=0)
records_number = colZ.selectbox('Show top countries', ['All', '10', '25', '50', '100'], index=1)
colEmpty.write('')
space(2)
df_latest = df_latest.sort_values(by=[analysis_type], ascending=False)
if records_number != 'All':
    df_latest = df_latest.head(int(records_number))

col1, col2 = st.columns(2)
for counter, (key, value) in enumerate(ANALYSIS_TYPES.items()):
    if counter % 2 == 0:
        col1.plotly_chart(graph_country_comparison_bar_charts(df_latest, key, countries, value), use_container_width=True)
    else:
        col2.plotly_chart(graph_country_comparison_bar_charts(df_latest, key, countries, value), use_container_width=True)

st.write('***')
#### Detailed data table ####
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
