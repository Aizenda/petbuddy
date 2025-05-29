import requests
import pandas as pd
from db_connect import mysql_pool

class DataCleaning:
    def __init__(self, data, wanted_fields):
        self.data = data
        self.fields = wanted_fields

    def clean(self):
        df = pd.DataFrame(self.data)[self.fields]
        df = df.dropna(subset=self.fields)
        for col in self.fields:
            df = df[df[col].astype(str).str.strip() != ""]
        return df

def get_clean_data():
    url = "https://data.moa.gov.tw/Service/OpenData/TransService.aspx?UnitId=QcbUEzN6E6DL"
    response = requests.get(url, verify=False)
    raw_data = response.json()

    wanted_fields = [
        "animal_subid", "animal_place", 
        "animal_kind", "album_file",
        "animal_sex", "animal_bodytype",
        "animal_colour", "shelter_address", "shelter_tel"
    ]

    cleaner = DataCleaning(raw_data, wanted_fields)
    clean_df = cleaner.clean()
    clean_df["animal_sex"] = clean_df["animal_sex"].replace({"F": "母", "M": "公"})
    clean_df["animal_bodytype"] = clean_df["animal_bodytype"].replace({"MEDIUM": "中型", "SMALL":"小型","BIG":"大型"})
    return clean_df

def insert_data_to_mysql(df):
    conn = mysql_pool.get_connection()
    cursor = conn.cursor()

    insert_query = """
        INSERT IGNORE INTO public (
            animal_subid, animal_place, animal_kind, album_file,
            animal_sex, animal_bodytype, animal_colour,
            shelter_address, shelter_tel
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data_tuples = [tuple(row) for row in df.values]
    cursor.executemany(insert_query, data_tuples)

    conn.commit()
    cursor.close()
    conn.close()
 
if __name__ == "__main__":
    df = get_clean_data()    
    insert_data_to_mysql(df)     