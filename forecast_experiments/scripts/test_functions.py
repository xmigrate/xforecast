import functions
import pandas as pd

df=pd.read_csv('../sample data/Metrics-2.csv')
df['Time'] =  pd.to_datetime(df.pop('Time'), format='%d/%m/%y %H:%M')
df['ds'] = df['Time']
df['y'] = df['Requests_Sum']
train_df = df[4000:9080]
response = functions.fit_and_predict(df=train_df,old_model_loc='../serialized_model.json')
print(response)