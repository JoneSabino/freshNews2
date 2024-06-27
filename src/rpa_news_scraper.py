from RPA.Browser.Selenium import Selenium
from datetime import datetime, timedelta
from loguru import logger
from src.config import Config
import traceback
from box import Box
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


class RPANewsScraper:
    def __init__(self, search_phrase, topic, months):
        self.base_url = Config.BASE_URL
        self.search_phrase = search_phrase
        self.topic = topic
        self.months = months
        self.articles = []
        self.browser = Selenium()
        self.locators = Box(
            {
                "search_field_button": 'css:button[data-element="search-button"]',
                "search_field": 'css:input[data-element="search-form-input"]',
                "submit_button": 'css:button[data-element="search-submit-button"]',
                "sort_by_button": "css:select.select-input",
                "filter": "css:div.search-results-module-filters-title",
            }
        )

    def create_webdriver_options(self):
        options = Options()
        options.add_argument("--enable-automation")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--disable-gpu")
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument("enable-features=NetworkServiceInProcess")
        options.add_argument("disable-features=NetworkService")
        options.set_capability("pageLoadStrategy", "normal")

        return {
            "arguments": options.arguments,
            "capabilities": options.to_capabilities(),
        }

    def open_site(self):
        logger.info(f"Opening site {self.base_url}")
        try:
            options = self.create_webdriver_options()
            self.browser.open_available_browser(self.base_url, options=options)
        except Exception:
            self._finish_process('Failed to open site: ', traceback.format_exc())

    def search(self):
        try:
            logger.info(f"Searching for '{self.search_phrase}'")
            self.browser.wait_until_page_contains_element(self.locators.search_field_button, timeout=300)
            self.browser.click_button(self.locators.search_field_button)
            self.browser.input_text(locator=self.locators.search_field, text=self.search_phrase)
            self.browser.click_button(self.locators.submit_button) #type: ignore
            self.browser.wait_until_page_contains(self.locators.filter)
        except Exception:
            self._finish_process('Search failed: ', traceback.format_exc())

    def select_topic(self):
        if self.topic:
            try:
                logger.info(f"Selecting topic '{self.topic}'")
                self.browser.click_link(self.topic)  #type: ignore
                self.browser.wait_until_page_contains(self.topic)
                self.locators
            except Exception:
                self._finish_process('Category selection failed: ', traceback.format_exc())

    def parse_articles(self):
        try:
            logger.info("Parsing articles")
            articles = self.browser.find_elements(Config.LOCATORS["article"])   #type: ignore
            for article in articles:
                title = self.browser.find_element(
                    Config.LOCATORS["article_title"], article
                ).text
                description = self.browser.find_element(
                    Config.LOCATORS["article_description"], article
                ).text
                date_text = self.browser.find_element(
                    Config.LOCATORS["article_date"], article
                ).get_attribute("datetime")
                date = datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%SZ")

                if self.is_within_date_range(date):
                    image_url = self.browser.find_element(
                        Config.LOCATORS["article_image"], article
                    ).get_attribute("src")
                    self.articles.append(
                        {
                            "title": title,
                            "description": description,
                            "date": date,
                            "image_url": image_url,
                        }
                    )
                    logger.info(f"Article found: {title}")
        except Exception:
            self._finish_process('Parsing articles failed: ', traceback.format_exc())

    def _finish_process(self, message, exception):
        logger.error(f"{message}\n\n{exception}")
        self.close()
        raise

    def is_within_date_range(self, date):
        today = datetime.now()
        past_date = today - timedelta(days=30 * self.months)
        return past_date <= date <= today

    def close(self):
        logger.info("Closing browser")
        self.browser.close_all_browsers()

    def extract_data(self):
        self.open_site()
        self.search()
        # self.select_topic()
        # self.parse_articles()
        # self.close()
