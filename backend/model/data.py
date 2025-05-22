import requests
import pandas as pd

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
    return clean_df