import pandas as pd
import datetime
import requests
import numpy as np
import xlrd

ma_days = 7

def pullRecent(days_back, date_format):
    """Pulls COVID data workbook from DC website based on date and date format.
    Parameters:
        days_back: number of days to subtract from today's date when specifying date in file name
        date_format: datetime format to use in file name (e.g. %Y-%m-%d)
    Returns dataframe of downloaded workbook."""
    date = datetime.datetime.today()-pd.to_timedelta(days_back, unit='D')
    url = 'https://coronavirus.dc.gov/sites/default/files/dc/sites/coronavirus/page_content/attachments/DC-COVID-19-Data-for-'+date.strftime(date_format)+'.xlsx'
    response = requests.get(url)
    file = response.content
    try:
        df = pd.read_excel(file, sheet_name='Overal Stats')
    except:
        # I'm thinking they'll see the above typo and fix it at some point
        df = pd.read_excel(file, sheet_name='Overall Stats')
    return(df)

# Hedging for a possible date format change by preparing several formats to cycle through; quits once one works though
date_formats = ['%#m-%#d-%Y','%B-%#d-%Y', '%B-%d-%Y', '%m-%d-%Y']

#Try to pull spreadsheet with most recent date, but work backwards a day at a time from there; also hedge for different date formats; break flag is ugly, but works for now
break_flag = False
for i in range(10):
    for j in date_formats:
        try:
            df = pullRecent(i,j)
            break_flag = True
            break
        except xlrd.XLRDError:
            # may handle these more precisely eventually
            continue
        except ValueError:
            continue
    if break_flag == True:
        break

keep_values = ['Total Overall Number of Tests','Total Positives','Total COVID-19 Patients in DC Hospitals','Total COVID-19 Patients in ICU']
df = df.loc[df['Unnamed: 1'].isin(keep_values)]
df = df.transpose()
begin = datetime.datetime(2020, 12, 1)
df = df.loc[begin:]
df = df.reset_index()
df.columns = ['Date','Total Tests','Total Positives','Hospitalizations','ICU']

for i in df.columns:
    df[i] = df[i].replace(',', '', regex =True)
    df[i] = df[i].replace(' ', '', regex =True)

# Data doesn't come with weekend dates, so pull all days between min and max dates and merge with data
range = pd.date_range(df['Date'].min(),df['Date'].max(),freq='d')
out_df = pd.DataFrame(range, columns=['Date'])
df = pd.merge(out_df, df, how= 'left', on='Date')
df['Total Tests'] = df['Total Tests'].astype(np.float64)

for i, row in df.iterrows():
    #correcting a persistent error in their excel file
    if df.loc[i,'Date'] == datetime.datetime(2021, 9, 22):
        df.loc[i,'Total Positives'] = 60018

# Fill weekend dates with prior day's values for cumulative data
    if np.isnan(df.loc[i,'Hospitalizations']):
        df.loc[i,'Hospitalizations'] = df.loc[i-1,'Hospitalizations']
        df.loc[i,'ICU'] = df.loc[i-1,'ICU']
    if np.isnan(df.loc[i,'Total Tests']):
        df.loc[i,'Total Tests'] = df.loc[i-1,'Total Tests']
        df.loc[i,'Total Positives'] = df.loc[i-1,'Total Positives']

df['New Tests'] = df['Total Tests'].diff().fillna(0)
df['New Positives'] = df['Total Positives'].diff().fillna(0)

df = df.sort_values(['Date'])
print('DC data through '+ str(df['Date'].max())[:10])
df.to_csv('dc.csv', index=False)
