import pytest
from unittest.mock import patch, MagicMock
from RPA.Robocorp.WorkItems import WorkItems
from src.rpa_news_scraper import RPANewsScraper
from src.excel_handler import ExcelHandler
from src.image_downloader import ImageDownloader
from tasks import main

@pytest.mark.parametrize(
    "search_phrase, topic, months, articles, image_url, image_file, excel_file, output_dir",
    [
        ("AI", "Technology", 3, [{"title": "AI News", "image_url": "http://example.com/image.jpg"}], "http://example.com/image.jpg", "image.jpg", "test.xlsx", "output"),
        ("Health", "Wellness", 6, [{"title": "Health News", "image_url": "http://example.com/health.jpg"}], "http://example.com/health.jpg", "health.jpg", "health.xlsx", "output"),
        ("Finance", "Economy", 1, [{"title": "Finance News", "image_url": "http://example.com/finance.jpg"}], "http://example.com/finance.jpg", "finance.jpg", "finance.xlsx", "output"),
    ],
    ids=["AI_Technology", "Health_Wellness", "Finance_Economy"]
)
def test_main_happy_path(search_phrase, topic, months, articles, image_url, image_file, excel_file, output_dir):

    # Arrange
    with patch.object(WorkItems, 'get_input_work_item'), \
         patch.object(WorkItems, 'get_work_item_variables', return_value={"search_phrase": search_phrase, "topic": topic, "months": months}), \
         patch.object(RPANewsScraper, 'extract_data'), \
         patch.object(RPANewsScraper, 'articles', new_callable=MagicMock(return_value=articles)), \
         patch.object(ImageDownloader, 'download_image', return_value=image_file), \
         patch.object(ExcelHandler, 'add_article'), \
         patch.object(ExcelHandler, 'save'), \
         patch.object(WorkItems, 'create_output_work_item'):

        # Act
        main()

        # Assert
        RPANewsScraper.extract_data.assert_called_once()
        ImageDownloader.download_image.assert_called_with(image_url)
        ExcelHandler.add_article.assert_called_with(articles[0], search_phrase)
        ExcelHandler.save.assert_called_once()
        WorkItems.create_output_work_item.assert_called_with(files=excel_file, save=True)

@pytest.mark.parametrize(
    "search_phrase, topic, months, articles, image_url, image_file, excel_file, output_dir",
    [
        ("", "Technology", 3, [{"title": "AI News", "image_url": "http://example.com/image.jpg"}], "http://example.com/image.jpg", "image.jpg", "test.xlsx", "output"),
        ("AI", "", 3, [{"title": "AI News", "image_url": "http://example.com/image.jpg"}], "http://example.com/image.jpg", "image.jpg", "test.xlsx", "output"),
        ("AI", "Technology", 0, [{"title": "AI News", "image_url": "http://example.com/image.jpg"}], "http://example.com/image.jpg", "image.jpg", "test.xlsx", "output"),
    ],
    ids=["Empty_Search_Phrase", "Empty_Topic", "Zero_Months"]
)
def test_main_edge_cases(search_phrase, topic, months, articles, image_url, image_file, excel_file, output_dir):

    # Arrange
    with patch.object(WorkItems, 'get_input_work_item'), \
         patch.object(WorkItems, 'get_work_item_variables', return_value={"search_phrase": search_phrase, "topic": topic, "months": months}), \
         patch.object(RPANewsScraper, 'extract_data'), \
         patch.object(RPANewsScraper, 'articles', new_callable=MagicMock(return_value=articles)), \
         patch.object(ImageDownloader, 'download_image', return_value=image_file), \
         patch.object(ExcelHandler, 'add_article'), \
         patch.object(ExcelHandler, 'save'), \
         patch.object(WorkItems, 'create_output_work_item'):

        # Act
        main()

        # Assert
        RPANewsScraper.extract_data.assert_called_once()
        ImageDownloader.download_image.assert_called_with(image_url)
        ExcelHandler.add_article.assert_called_with(articles[0], search_phrase)
        ExcelHandler.save.assert_called_once()
        WorkItems.create_output_work_item.assert_called_with(files=excel_file, save=True)

@pytest.mark.parametrize(
    "search_phrase, topic, months, articles, image_url, image_file, excel_file, output_dir, exception",
    [
        ("AI", "Technology", 3, [{"title": "AI News", "image_url": "http://example.com/image.jpg"}], "http://example.com/image.jpg", "image.jpg", "test.xlsx", "output", Exception("Test Exception")),
    ],
    ids=["Exception_Case"]
)
def test_main_error_cases(search_phrase, topic, months, articles, image_url, image_file, excel_file, output_dir, exception):

    # Arrange
    with patch.object(WorkItems, 'get_input_work_item'), \
         patch.object(WorkItems, 'get_work_item_variables', return_value={"search_phrase": search_phrase, "topic": topic, "months": months}), \
         patch.object(RPANewsScraper, 'extract_data', side_effect=exception), \
         patch.object(RPANewsScraper, 'articles', new_callable=MagicMock(return_value=articles)), \
         patch.object(ImageDownloader, 'download_image', return_value=image_file), \
         patch.object(ExcelHandler, 'add_article'), \
         patch.object(ExcelHandler, 'save'), \
         patch.object(WorkItems, 'create_output_work_item'):

        # Act
        with pytest.raises(Exception) as excinfo:
            main()

        # Assert
        assert str(excinfo.value) == str(exception)
