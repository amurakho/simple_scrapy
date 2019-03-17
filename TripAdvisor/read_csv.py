import pandas as pd

df = pd.read_csv('adv.csv')
data = df
# data = df[df['country_name'] == 'Caribbean']
# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#     print(data)
print(data)