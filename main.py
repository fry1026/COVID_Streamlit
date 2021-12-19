import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide")


def plotly_figure(df_data, column, countries):
    # long_df = px.data.medals_long()
    # fig = px.bar(long_df, x="nation", y="count", color="medal", title="Long-Form Input")

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
                "title": {"text": column}
            },
            "height": 250,
            "margin": {"t": 10, "l": 10, "r": 10},
        },
    })
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
    df['weekly_incidence_per_100k_pop'] = df.Active_new_week / df.population * 100000
    df.fillna({'weekly_incidence_per_100k_pop': 0}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    return df


df = load_data()
df_world = df[df['continent'].isna() == True].copy()
continents = list(df[df['continent'].isna() == True].location.unique())
df = df[df['continent'].isna() == False].copy()

px.set_mapbox_access_token('pk.eyJ1IjoiZnJ5MTAyNiIsImEiOiJja2Jhbjl0bWEwcGl4MnJta3RjbmgxbndnIn0.uXg4C9JwENtYLAiptce6yA')

last_update = df.date.max()
all_countries = sorted(set(df.location))
df_latest = df[df.date == df.date.max()].copy()
df_latest['week_incidence_rank'] = df_latest['weekly_incidence_per_100k_pop'].rank()

# Sidebar
st.sidebar.title("Filter options")

analysis_type = st.sidebar.selectbox('Sort by',
                                     ['new_cases', 'weekly_incidence_per_100k_pop', 'total_cases',
                                      'total_vaccinations', 'icu_patients', 'population'],
                                     index=0)
records_number = st.sidebar.selectbox('Show data', ['All', '10', '25', '50', '100'], index=2)
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
col1.write("#### Incident rate")
col1.plotly_chart(px.line(dfw, x='date', y='weekly_incidence_per_100k_pop', color='location'), use_container_width=True)
# col1.plotly_chart(px.line(df_world, x='date', y='new_cases_smoothed'),use_container_width=True)

space(5, col2)
col2.write("#### Top 10 Countries (Incident Rate)")
col2.table(
    df_latest[['location', 'weekly_incidence_per_100k_pop', 'new_cases']].sort_values(
        by=['weekly_incidence_per_100k_pop'],
        ascending=False).head(10))

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
    fig = px.line(dff, x='date', y='weekly_incidence_per_100k_pop', color='location')
    fig.update_traces(line=dict(width=1))
    colA.plotly_chart(fig, use_container_width=True)
    colB.write('#### Country Incident Rate and Ranking')
    colB.dataframe(
        df_latest[df.location.isin(countries)][
            ['location', 'weekly_incidence_per_100k_pop', 'week_incidence_rank', 'new_cases_smoothed']])

    df_latest = df_latest.sort_values(by=[analysis_type], ascending=False)
    if records_number != 'All':
        df_latest = df_latest.head(int(records_number))
    # st.plotly_chart(px.bar(df_latest, x='location', y=analysis_type), use_container_width=True)
    # Test
    col1, col2 = st.columns(2)
    col1.plotly_chart(plotly_figure(df_latest, 'new_cases', countries), use_container_width=True)
    col2.plotly_chart(plotly_figure(df_latest, 'weekly_incidence_per_100k_pop', countries), use_container_width=True)
    col1, col2 = st.columns(2)
    col1.plotly_chart(plotly_figure(df_latest, 'total_cases', countries), use_container_width=True)
    col2.plotly_chart(plotly_figure(df_latest, 'total_vaccinations', countries), use_container_width=True)
    col1, col2 = st.columns(2)
    col1.plotly_chart(plotly_figure(df_latest, 'icu_patients', countries), use_container_width=True)
    col2.plotly_chart(plotly_figure(df_latest, 'population', countries), use_container_width=True)

st.write('***')
if show_data:
    st.subheader("Detailed Data")
    st.write(dff)
