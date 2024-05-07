from influxdb_client import InfluxDBClient
import pandas as pd
import warnings
from influxdb_client.client.warnings import MissingPivotFunction
warnings.simplefilter("ignore", MissingPivotFunction)

INFLUX_HOST = "http://influxdb:8086"
INFLUX_TOKEN = "_dLOVD41oGB3UPNoCuXcqwb7MZonkMIi48eNL6NKW6aVRX0wUqJxo4O75HRdxmH4xOF-L9MJpybbyNpA9jraZw=="
INFLUX_ORG = "sensor_load_pipeline"
INFLUX_BUCKET = "sensors_bucket"

client = InfluxDBClient(url=INFLUX_HOST, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

def set_df_index(df):
    df = df.set_index('Date')
    df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S%z').tz_localize(None)
    return df.sort_index()

def split_columns_multiindex(df):
    tuple_columns = [(x[1][-1], x[2][-1], x[3]) for x in [column.split('_') for column in df.columns]]
    df.columns = pd.MultiIndex.from_tuples(tuple_columns, names=['Floor', 'Zone','Sensor'])
    return df
    
def clean_up_influx_df(df):
    df = df.drop(columns=['result', 'table','_start','_stop','_field','_measurement','client_id','host','topic'])
    df = df.rename(columns = {'_time':'Date'})
    return set_df_index(df) 

def get_last_available_date(client_id='client-1'):
    query = f'''from(bucket: "sensors_bucket")
    |> range(start: 0)
    |> filter(fn: (r) => r["client_id"] == "{client_id}")
    |> filter(fn: (r) => r["device_id"] == "1")
    |> last()'''
    df = query_api.query_data_frame(org=INFLUX_ORG, query=query)
    if df.empty == False:
        return df.iloc[-1, df.columns.get_loc('_time')]
    else: 
        return None

def get_period_since(since, period='1mo', client_id='client-1'):
    query = f'''import "date"
    from(bucket: "sensors_bucket")
        |> range(start: date.add(d: -{period}, to: time(v:{since})), stop: time(v:{since}))
        |> filter(fn: (r) => r["_measurement"] == "sensors")
        |> filter(fn: (r) => r["_field"] == "electricity_load")
        |> filter(fn: (r) => r["client_id"] == "{client_id}")
        |> pivot(rowKey:["_time"], columnKey: ["device_id", "floor", "zone", "sensor"], valueColumn: "_value")
    '''
    return query_api.query_data_frame(org=INFLUX_ORG, query=query)

def get_all_after(start, client_id='client-1'):
    query = f'''import "date"
    from(bucket: "sensors_bucket")
        |> range(start: time(v:{start}))
        |> filter(fn: (r) => r["_measurement"] == "sensors")
        |> filter(fn: (r) => r["_field"] == "electricity_load")
        |> filter(fn: (r) => r["client_id"] == "{client_id}")
        |> pivot(rowKey:["_time"], columnKey: ["device_id", "floor", "zone", "sensor"], valueColumn: "_value")
    '''
    return query_api.query_data_frame(org=INFLUX_ORG, query=query)

def get_last_by_period(period='1mo', client_id='client-1'):
    query = f'''import "date"
    lastObservationTime = () => {{
        timeRecord = from(bucket: "sensors_bucket")
            |> range(start: 0)
            |> filter(fn: (r) => r["client_id"] == "{client_id}")
            |> filter(fn: (r) => r["device_id"] == "1")
            |> last()
            |> findRecord(fn: (key) => true, idx: 0)

        return timeRecord._time
    }}

    lastTime = lastObservationTime()
    if exists lastTime then
    from(bucket: "sensors_bucket")
    |> range(start: date.add(d: -{period}, to: lastTime), stop: lastTime)
    |> filter(fn: (r) => r["_measurement"] == "sensors")
    |> filter(fn: (r) => r["_field"] == "electricity_load")
    |> filter(fn: (r) => r["client_id"] == "{client_id}")
    |> pivot(rowKey:["_time"], columnKey: ["device_id", "floor", "zone", "sensor"], valueColumn: "_value")
    else
    from(bucket: "sensors_bucket")
    |> range(start: 0)'''
    return query_api.query_data_frame(org=INFLUX_ORG, query=query)

