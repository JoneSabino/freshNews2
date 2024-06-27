import os
import requests
from loguru import logger


class ImageDownloader:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory {self.output_dir} created")

    def download_image(self, url):
        logger.info(f"Downloading image from {url}")
        response = requests.get(url)
        if response.status_code == 200:
            image_name = os.path.basename(url)
            image_path = os.path.join(self.output_dir, image_name)
            with open(image_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Image saved to {image_path}")
            return image_name
        else:
            logger.error(
                f"Failed to download image from {url} with status code {response.status_code}"
            )
            response.raise_for_status()
