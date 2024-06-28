import os


class Config:
    BASE_URL = "https://www.latimes.com/"
    OUTPUT_DIR = "output"
    EXCEL_FILE = os.path.join(OUTPUT_DIR, "news_data.xlsx")
    NEWEST = "1"
