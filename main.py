from dotenv import load_dotenv
import pandas as pd
import os
load_dotenv()

csid = 12854

def run_sql_query(sql_query):
   
   return pd.read_sql_query(sql_query, con=os.getenv('RSR_SVC_CONN')) 

def get_market_status():
    market_status = f'''
    SELECT 
	    ss.collection_set_id, 
        cs.name, 
        ss.time_start, 
        ss.time_end, 
        ss.insert_time, 
        ss.update_time, 
        c.data_source
    FROM
	    md2.collection_set_status_states ss
    JOIN
	    md2.collection_set_statuses cs
    ON
	    ss.collection_set_status_id = cs.collection_set_status_id
    JOIN
	    md2.data_sources c
    ON
	    ss.data_source_id = c.data_source_id
    WHERE 
	    ss.collection_set_id = {csid}
    AND
        cs.name = 'Report Publish'
    ORDER BY
	    ss.update_time;
'''
    df_market_status = run_sql_query(market_status)
    print(df_market_status)

get_market_status()