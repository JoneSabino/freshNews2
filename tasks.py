from RPA.Robocorp.WorkItems import WorkItems
from loguru import logger
from src.config import Config
from src.rpa_news_scraper import RPANewsScraper
from src.excel_handler import ExcelHandler
from src.image_downloader import ImageDownloader
from robocorp.tasks import task
from box import Box


@task
def main():
    # logger.add("logs/scraper.log", rotation="500 MB")

    work_items = WorkItems()
    work_items.get_input_work_item()
    params = Box(work_items.get_work_item_variables())

    news_scraper = RPANewsScraper(params.search_phrase, params.topic, params.months)
    news_scraper.extract_data()

    excel_handler = ExcelHandler(Config.EXCEL_FILE)
    image_downloader = ImageDownloader(Config.OUTPUT_DIR)

    for article in news_scraper.articles:
        article["image_file"] = image_downloader.download_image(article["image_url"])
        excel_handler.add_article(article, params.search_phrase)

    excel_handler.save()
    work_items.create_output_work_item(files=Config.OUTPUT_DIR, save=True)


if __name__ == "__main__":
    main()
