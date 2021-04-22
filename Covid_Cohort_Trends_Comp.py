import pandas as pd
import datetime
import json
from pandas import DataFrame
import numpy as np


#-------------------Data Sources-----------------------------------------------:
cases_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
deaths_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'
hosp_file = 'https://api.covidtracking.com/v1/states/daily.json'
pop_file = 'https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/national/totals/nst-est2020.csv'
state_bridge = pd.read_csv('https://raw.githubusercontent.com/jasonong/List-of-US-States/master/states.csv', delimiter = ",", header=0, index_col=None)

# Set number of days for moving average calculations
ma_days = 7

#-------------------Define Cohorts-----------------------------------------------:
# (these are roughly chronologically ordered batches of states, based on when the first wave of the virus occurred in each state)
# can be switched around easily to make any desired comparisons, including single states
cohort1_list = ['New York','New Jersey','Rhode Island','Massachusetts','Connecticut','Delaware','Pennsylvania','District of Columbia','Michigan']
cohort2_list = ['Florida','Arizona','California','Texas','Alabama','South Carolina','Idaho','Nevada']
cohort3_list = ['Louisiana','Mississippi','Alaska','Arkansas','Kentucky','Hawaii','Missouri','Georgia','Tennessee','Oklahoma','North Carolina']
cohort4_list = ['North Dakota','West Virginia','Montana','South Dakota','Minnesota','Iowa','Indiana','Kansas','Ohio','Wisconsin']

# exclude for now based on trends
exclude_list = ['Virgin Islands','Guam','Northern Mariana Islands','Diamond Princess','Grand Princess','American Samoa','Puerto Rico']

#-------------Set up files--------------------------------------------------------------#
#---cases and deaths set up
#Function to download cases and deaths data and then process to same format
def process(df, url, name):
    """This function reads JHU data, selects relevant fields, transposes and sums up to the state level"""
    df = pd.read_csv(url, delimiter = ",", header=0)

    #create list of irrelevant columns (only want state and date columns)
    non_date_cols = [col for col in df.columns if '/' not in col and col != 'Province_State']

    #drop unwanted columns and territories
    df = df.drop(non_date_cols, axis=1)
    df = df.loc[~df['Province_State'].isin(exclude_list)]
    #transpose to long, state-day shape
    df = pd.melt(df, id_vars='Province_State',
        var_name = 'Date',
        value_name = name)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.groupby(['Province_State','Date'],as_index=False)[[name]].sum()
    df.sort_values(['Province_State', 'Date'])
    return(df)

# Process cases and deaths, then bring them together
deaths = process(df='deaths', url = deaths_url, name='Deaths')
cases = process(df='cases', url = cases_url, name='Cases')

#---hospitalizations set up
hosp = pd.read_json(hosp_file)
#create date column in datetime formate
hosp['str_date'] = hosp['date'].apply(str)
hosp['Date'] = pd.to_datetime(hosp.str_date.str.slice(start=0, stop=4)+"-"+hosp.str_date.str.slice(start=4, stop=6)+"-"+hosp.str_date.str.slice(start=6))

#Get full state name worked out
hosp = hosp.rename(columns={'state':'Abbreviation'})
hosp = pd.merge(hosp,state_bridge, how='left', on='Abbreviation')
hosp = hosp.filter(['State','Date','hospitalizedCurrently','positiveIncrease','totalTestResultsIncrease'])
hosp = hosp.rename(columns={'State':'Province_State'})

#---population set up
pop = pd.read_csv(pop_file, delimiter = ",", header=0, index_col=None)
pop = pop.filter(['NAME','POPESTIMATE2020'], axis=1)
pop = pop.rename(columns={'NAME':'Province_State','POPESTIMATE2020':'Population2020'})

#-----------------function to calculate per capita measures by cohort---------------
def pct(cohort,name):
    """This function subsets cases, hospitalizations and deaths to the list of states in the cohort input.
    It then creates a new dataframe with the overall 7 day moving averages of those measures per person (or percent of population) in the selected states."""
    cases_unit = cases.loc[cases['Province_State'].isin(cohort)]
    hosp_unit = hosp.loc[hosp['Province_State'].isin(cohort)]
    deaths_unit = deaths.loc[deaths['Province_State'].isin(cohort)]

    df = pd.merge(cases_unit, pop, how='left', on='Province_State')
    df = pd.merge(df, hosp_unit, how='left', on=['Province_State','Date'])
    df = pd.merge(df, deaths_unit, how='left', on=['Province_State','Date'])

    df = df.groupby('Date')[['Cases','hospitalizedCurrently','Deaths','positiveIncrease','totalTestResultsIncrease','Population2020']].sum()
    df['daily_cases'] = df[['Cases']].diff().fillna(0)
    df['daily_cases_per_cap'] = df['daily_cases']/df['Population2020']
    df['daily_cases_per_capMA'] = df['daily_cases_per_cap'].rolling(ma_days).mean()

#using hospitalizedCurrently -- there's also the new hospitalizations
    df['daily_hospitalized_per_cap'] = df['hospitalizedCurrently']/df['Population2020']
    df['daily_hospitalized_per_capMA'] = df['daily_hospitalized_per_cap'].rolling(ma_days).mean()

    df['daily_deaths'] = df[['Deaths']].diff().fillna(0)
    df['daily_deaths_per_cap'] = df['daily_deaths']/df['Population2020']
    df['daily_deaths_per_capMA'] = df['daily_deaths_per_cap'].rolling(ma_days).mean()

    df['daily_positivity'] = df['positiveIncrease']/df['totalTestResultsIncrease']
    df['daily_positivity_ma'] = df['daily_positivity'].rolling(ma_days).mean()

    df = df.drop(['Cases','hospitalizedCurrently','Deaths','Population2020','daily_cases','daily_cases_per_cap',
    'daily_hospitalized_per_cap','daily_deaths','daily_deaths_per_cap','daily_positivity',
    'positiveIncrease','totalTestResultsIncrease'], axis=1)

    col_order = ['daily_cases_per_capMA','daily_hospitalized_per_capMA','daily_deaths_per_capMA','daily_positivity_ma']
    df = df[col_order]

    df = df.rename(columns={'daily_cases_per_capMA':name+' MA Cases', 'daily_deaths_per_capMA':name+' MA Deaths',
    'daily_hospitalized_per_capMA':name+' MA Hosp.','daily_positivity_ma':name+' MA Positivity'})
    return(df)

cohort1 = pct(cohort=cohort1_list, name='Cohort 1')
cohort2 = pct(cohort=cohort2_list, name='Cohort 2')
cohort3 = pct(cohort=cohort3_list, name='Cohort 3')
cohort4 = pct(cohort=cohort4_list, name='Cohort 4')

df = pd.merge(cohort1, cohort2, how='left', on='Date')
df = pd.merge(df, cohort3, how='left', on='Date')
df = pd.merge(df, cohort4, how='left', on='Date')

#select limited time period
begin = datetime.datetime(2020, 3, 15)
df = df.loc[begin:]
df.to_csv('cohort_be.csv')
