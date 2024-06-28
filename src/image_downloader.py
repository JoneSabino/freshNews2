import os
import requests
from robocorp import log
import uuid


class ImageDownloader:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        log.info(f"Output directory {self.output_dir} created")
    
    def _extract_filename(self, url):
        start_pos = url.rfind('%2F')
        return url[start_pos + 3:] if start_pos != -1 else "unnamed.jpg"

    def download_image(self, url):
        log.info(f"Downloading image from {url}")
        filename = self._extract_filename(url)
        response = requests.get(url)
        if response.status_code == 200:
            image_name = os.path.basename(f"{str(uuid.uuid4())}_{filename}")
            image_path = os.path.join(self.output_dir, image_name)
            with open(image_path, "wb") as file:
                file.write(response.content)
            log.info(f"Image saved to {image_path}")
            return image_name
        else:
            log.critical(
                f"Failed to download image from {url} with status code {response.status_code}"
            )
            response.raise_for_status()
