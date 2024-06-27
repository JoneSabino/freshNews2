import os
from box import Box

class Config:
    BASE_URL = "https://www.latimes.com/"
    OUTPUT_DIR = "output"
    EXCEL_FILE = os.path.join(OUTPUT_DIR, "news_data.xlsx")

    # Locators
    LOCATORS = Box(
        {
            "search_field_button": 'css:button[data-element="search-button"]',
            "search_field": 'css:input[data-element="search-form-input"]',
            "submit_button": 'css:button[data-element="search-submit-button"]',
            "sort_by_button": "css:select.select-input",
        }
    )
