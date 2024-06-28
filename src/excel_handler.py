from RPA.Excel.Files import Files
from loguru import logger
import re


class ExcelHandler:
    def __init__(self, file_name):
        self.file_name = file_name
        self.excel = Files()
        self.excel.create_workbook(file_name)
        self.excel.append_rows_to_worksheet(
            [
                [
                    "Title",
                    "Date",
                    "Description",
                    "Image File",
                    "Phrase Count",
                    "Contains Money",
                ]
            ],
            header=True,
        )
        logger.info(f"Excel file {self.file_name} created")

    def add_article(self, article, search_phrase):
        phrase_count = self.count_search_phrases(
            article["title"], article["description"], search_phrase
        )
        contains_money = self.contains_money(article["title"], article["description"])
        self.excel.append_rows_to_worksheet(
            [
                [
                    article["title"],
                    article["date"].strftime("%Y-%m-%d"),
                    article["description"],
                    article["image_file"],
                    phrase_count,
                    contains_money,
                ]
            ]
        )
        logger.info(f"Article added to Excel: {article['title']}")

    def save(self):
        self.excel.save_workbook(self.file_name)
        self.excel.close_workbook()
        logger.info(f"Excel file {self.file_name} saved")

    @staticmethod
    def count_search_phrases(title, description, search_phrase):
        return title.lower().count(search_phrase.lower()) + description.lower().count(
            search_phrase.lower()
        )

    @staticmethod
    def contains_money(title, description):
        money_patterns = [
            r"\$\d+(\.\d+)?",  # $100 or $100.50
            r"\d+ dollars",  # 100 dollars
            r"\d+ USD",  # 100 USD
            r"\d+k USD",  # 100k USD
            r"\d+m USD",  # 100m USD
            r"\d+(\.\d+)?k dollars",  # 100k dollars or 100.5k dollars
            r"\d+(\.\d+)?m dollars",  # 100m dollars or 100.5m dollars
        ]
        combined_text = f"{title} {description}"
        return any(re.search(pattern, combined_text) for pattern in money_patterns)
