import contextlib
from RPA.Browser.Selenium import Selenium
from datetime import datetime, timezone
from loguru import logger
from src.config import Config
import traceback
from box import Box
from selenium.webdriver.chrome.options import Options


class RPANewsScraper:
    def __init__(self, search_phrase: str, topic: str, months: int):
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

    def _create_webdriver_options(self) -> dict:
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

    def _open_site(self) -> None:
        logger.info(f"Opening site {self.base_url}")
        try:
            options = self._create_webdriver_options()
            self.browser.open_available_browser(self.base_url, options=options)
        except Exception:
            self._finish_process("Failed to open site: ", traceback.format_exc())

    def _search(self) -> None:
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

    def _wait_loading_animation(self) -> None:
        with contextlib.suppress(AssertionError):
            self.browser.wait_until_element_is_visible(
                self.locators.loading_icon, timeout=5
            )
            self.browser.wait_until_element_is_not_visible(
                self.locators.loading_icon, timeout=3
            )

    def _select_topic(self) -> None:
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

            self._wait_loading_animation()
        except Exception:
            self._finish_process("Selecting topic failed: ", traceback.format_exc())

    def _parse_articles(self) -> None:
        try:
            search_results = self.browser.get_webelements(self.locators.search_results)

            for index, article in enumerate(search_results):
                date_element = self.browser.find_element(
                    self.locators.article_date, article
                )
                date_timestamp = self.browser.get_element_attribute(
                    date_element, "data-timestamp"
                )
                date = datetime.fromtimestamp(int(date_timestamp) / 1000, timezone.utc)

                is_within_date_range = self._is_within_date_range(date, self.months)

                if is_within_date_range:
                    logger.info(f"Article {article}")
                    title_element = self.browser.find_element(
                        self.locators.article_title, article
                    )
                    description_element = self.browser.find_element(
                        self.locators.article_description, article
                    )

                    title = self.browser.get_text(title_element)
                    description = self.browser.get_text(description_element)

                    image_url = self.browser.find_element(
                        self.locators.article_image, article
                    ).get_attribute("src")
                    self.articles.append(
                        {
                            "title": title,
                            "description": description,
                            "date": date,
                            "image_url": image_url,
                        }
                    )
                if index == len(search_results) - 1 and is_within_date_range:
                    self.browser.click_button(self.locators.next_page)
                    self._wait_loading_animation()
                    self._parse_articles()
        except Exception:
            self._finish_process("Parsing articles failed: ", traceback.format_exc())

    def _finish_process(self, message: str, traceback: str) -> None:
        logger.error(f"{message}\n\n{traceback}")
        self.close()
        raise

    def _calculate_month_range(self, months: int) -> tuple:
        today = datetime.now()
        current_year = today.year
        current_month = today.month

        if months <= 1:
            # Only the current month
            start_year, start_month = current_year, current_month
        else:
            start_year, start_month = self._get_start_date(
                current_year, current_month, months
            )

        end_year, end_month = current_year, current_month

        return (start_year, start_month), (end_year, end_month)

    def _get_start_date(self, current_year: int, current_month: int, months: int) -> tuple:
        """
        Calculate the start year and month by going back the specified number of months.
        """
        start_month = (current_month - months) % 12
        start_year = current_year + (current_month - months) // 12
        if start_month <= 0:
            start_month += 12
            start_year -= 1

        return start_year, start_month

    def _is_within_date_range(self, check_date: datetime, months: int) -> bool:
        """
        Check if the given date is within the range defined
        by the number of months back from the current date.
        """
        (start_year, start_month), (end_year, end_month) = self._calculate_month_range(
            months
        )

        check_year = check_date.year
        check_month = check_date.month

        start_period = start_year * 12 + start_month
        end_period = end_year * 12 + end_month
        check_period = check_year * 12 + check_month

        return start_period <= check_period <= end_period

    def close(self) -> None:
        logger.info("Closing browser")
        self.browser.close_all_browsers()

    def extract_data(self) -> None:
        self._open_site()
        self._search()
        self._select_topic()
        self._parse_articles()
        self.close()
