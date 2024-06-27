import contextlib
from RPA.Browser.Selenium import Selenium
from datetime import datetime, timedelta, timezone
from loguru import logger
from src.config import Config
import traceback
from box import Box
from selenium.webdriver.chrome.options import Options

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from time import sleep


class RPANewsScraper:
    def __init__(self, search_phrase, topic, months):
        self.base_url = Config.BASE_URL
        self.search_phrase = search_phrase
        self.topic = topic
        self.months = months
        self.articles = []
        self.browser = Selenium(
            timeout=10, implicit_wait=10, run_on_failure="CapturePageScreenshot"
        )
        self.locators = Box(
            {
                "search_field_button": 'css:button[data-element="search-button"]',
                "search_field": 'css:input[data-element="search-form-input"]',
                "submit_button": 'css:button[data-element="search-submit-button"]',
                "sort_by_button": "css:select.select-input",
                "filter": "css:div.search-results-module-filters-title",
                "see_all_topics": "xpath://ul[@data-name='Topics']/ancestor::ps-toggler//span[@class='see-all-text']",
                "topic": f"xpath://label[span[text()='{self.topic}']]/input",
                "topic_selected_count": f"//span[text()='{self.topic}']/../../following-sibling::div[contains(@class, 'SearchFilterInput-count')]",
                "search_results_count": "xpath://span[contains(text(), 'There are <?> results that match your search.')]",
                "search_results": "css:ul.search-results-module-results-menu li",
                "article_title": "css:h3.promo-title > a",
                "article_description": "css:p.promo-description",
                "article_date": "css:p.promo-timestamp",  # attr data-timestamp
                "article_image": "css:img.image",
                "next_page": "css:div.search-results-module-next-page",
                "loading_icon": "css:div.loading-icon",
            }
        )

    def _create_webdriver_options(self):
        options = Options()
        options.add_argument("--enable-automation")
        options.add_argument("--headless")
        options.add_argument("--window-size=1024,768")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--disable-gpu")
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--log-level=3")
        options.add_argument("enable-features=NetworkServiceInProcess")
        options.add_argument("disable-features=NetworkService")
        options.set_capability("pageLoadStrategy", "eager")
        return {
            "arguments": options.arguments,
            "capabilities": options.to_capabilities(),
        }

    def open_site(self):
        logger.info(f"Opening site {self.base_url}")
        try:
            options = self._create_webdriver_options()
            self.browser.open_available_browser(self.base_url, options=options)
        except Exception:
            self._finish_process("Failed to open site: ", traceback.format_exc())

    def _search(self):
        try:
            logger.info(f"Searching for '{self.search_phrase}'")
            self.browser.wait_and_click_button(self.locators.search_field_button)
            self.browser.input_text(
                locator=self.locators.search_field, text=self.search_phrase
            )
            self.browser.click_button(self.locators.submit_button)

            self.browser.wait_until_element_is_visible(self.locators.see_all_topics)
            self.browser.click_element(self.locators.see_all_topics)

        except Exception:
            self._finish_process("Search failed: ", traceback.format_exc())

    def _select_topic(self):
        try:
            self.browser.wait_until_element_is_visible(self.locators.topic)
            total_articles_number = self.browser.get_text(
                self.locators.topic_selected_count
            )[1:-1]  # type: ignore
            search_results_count = self.locators.search_results_count.replace(
                "<?>", total_articles_number
            )
            self.browser.select_checkbox(self.locators.topic)

            self.browser.wait_until_element_is_visible(search_results_count)  # type: ignore
            self.browser.select_from_list_by_value(
                self.locators.sort_by_button, Config.NEWEST
            )

            with contextlib.suppress(AssertionError):
                self.browser.wait_until_element_is_visible(
                    self.locators.loading_icon, timeout=5
                )
                self.browser.wait_until_element_is_not_visible(
                    self.locators.loading_icon, timeout=3
                )
        except Exception:
            self._finish_process("Selecting topic failed: ", traceback.format_exc())

    def _parse_articles(self):
        data = {
            "Title": "",
            "Date": "",
            "Description": "",
            "Picture Filename": "",
            "Search Phrase Count": "",
            "Has Money": bool,
        }
        try:
            search_results = self.browser.get_webelements(self.locators.search_results)
            for article in search_results:
                logger.info(f"Article {article}")
                title_element = self.browser.find_element(
                    self.locators.article_title, article
                )
                description_element = self.browser.find_element(
                    self.locators.article_description, article
                )
                date_element = self.browser.find_element(
                    self.locators.article_date, article
                )

                title = self.browser.get_text(title_element)
                description = self.browser.get_text(description_element)
                date_timestamp = self.browser.get_element_attribute(
                    date_element, "data-timestamp"
                )
                
                date = datetime.fromtimestamp(
                    int(date_timestamp) / 1000, timezone.utc
                ).strftime("%d-%m-%Y")

                if self.is_within_date_range(date):
                    image_url = self.browser.find_element(Config.LOCATORS['article_image'], article).get_attribute('src')
                    self.articles.append({
                        'title': title,
                        'description': description,
                        'date': date,
                        'image_url': image_url,
                    })
                    logger.info(f"Article found: {title}")

                logger.info(f"Article found: {title}")
                logger.info(f"Description: {description}")
                logger.info(f"Date_timestamp: {date_timestamp}")
                logger.info(f"Date: {date}")
        except Exception:
            self._finish_process("Parsing articles failed: ", traceback.format_exc())

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
        self._search()
        self._select_topic()
        self._parse_articles()
        # self.close()
