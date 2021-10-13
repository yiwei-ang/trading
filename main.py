#import required modules
from bs4 import BeautifulSoup
import ast
import pandas as pd
import re
import requests
from datetime import datetime

def get_stock_price(ticker):
  # pass a ticker name to i3investor website url
  url = "https://klse.i3investor.com/servlets/stk/chart/{}.jsp". format(ticker)
  # get response from the site and extract the price data
  response = requests.get(url, headers={'User-Agent':'test'})
  soup = BeautifulSoup(response.content, "html.parser")
  script = soup.find_all('script')
  data_tag = script[19].contents[0] #changed to 19 from 20
  chart_data = ast.literal_eval(re.findall('\[(.*)\]', data_tag.split(';')[0])[0])
  # tabulate the price data into a dataframe
  chart_df = pd.DataFrame(chart_data, columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
  # convert timestamp into readable date
  chart_df['Date'] = chart_df['Date'].apply(lambda x: \
      datetime.utcfromtimestamp(int(x)/1000).strftime('%Y-%m-%d'))
  return chart_df

def add_EMA(price, day):
  return price.ewm(span=day).mean()

def get_stock_list():
  # this is the website we're going to scrape from
  url = "https://www.malaysiastock.biz/Stock-Screener.aspx"
  response = requests.get(url, headers={'User-Agent':'test'})
  soup = BeautifulSoup(response.content, "html.parser")
  table = soup.find(id = "MainContent2_tbAllStock")
  # return the result in a list
  return [stock.getText() for stock in table.find_all('a')]

# function to check for EMA crossing
def check_EMA_crossing(df):
  # condition 1: EMA18 is higher than EMA50 at the last trading day
  cond_1 = df.iloc[-1]['EMA18'] > df.iloc[-1]['EMA50']
  # condition 2: EMA18 is lower than EMA50 the previous day
  cond_2 = df.iloc[-2]['EMA18'] < df.iloc[-2]['EMA50']
  # condition 3: to filter out stocks with less than 50 candles
  cond_3 = len(df.index) > 50
  # will return True if all 3 conditions are met
  return (cond_1 and cond_2 and cond_3)

# main program
if __name__ == '__main__':
  # a list to store the screened results
  screened_list = []
  # get the full stock list
  stock_list = get_stock_list()
  for each_stock in stock_list:
    # Step 1: get stock price for each stock
    price_chart_df = get_stock_price(each_stock)
    # Step 2: add technical indicators (in this case EMA)
    price_chart_df['EMA18']=add_EMA(price_chart_df['Close'],18)
    price_chart_df['EMA50']=add_EMA(price_chart_df['Close'],50)
    price_chart_df['EMA100']=add_EMA(price_chart_df['Close'],100)
    # if all 3 conditions are met, add stock into screened list
    if check_EMA_crossing(price_chart_df):
      screened_list.append(each_stock)
    print(screened_list)