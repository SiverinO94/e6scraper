import os
import requests
import configparser
from PySide6.QtCore import QThread, Signal

CONFIG_FILE = "config.ini"

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        query = config["settings"].get("query", "")
        download_output = config["settings"].get("download_output", "downloads")
        download_limit = int(config["settings"].get("download_limit", 25))
    else:
        query = ""
        download_output = "downloads"
        download_limit = 25
    return query, download_output, download_limit

def save_config(query, download_output, download_limit):
    config = configparser.ConfigParser()
    config["settings"] = {
        "query": query,
        "download_output": download_output,
        "download_limit": str(download_limit)
    }
    with open(CONFIG_FILE, "w") as f:
        config.write(f)


# ------------------- Worker Thread -------------------
class DownloadWorker(QThread):
    progress_signal = Signal(int)      # Overall progress
    file_progress_signal = Signal(int) # Per-file progress
    log_signal = Signal(str)
    stopped_signal = Signal()

    def __init__(self, query, download_output, download_limit):
        super().__init__()
        self._stop_flag = False
        self.query = query
        self.download_output = download_output
        self.download_limit = download_limit
        self.USER_AGENT = f"https://github.com/SiverinO94/e6scraper (by SiverinO)"

    def stop(self):
        self._stop_flag = True

    def run(self):
        posts = self.fetch_posts(self.query, self.download_limit)
        total = len(posts)
        for i, post in enumerate(posts, start=1):
            if self._stop_flag:
                self.log_signal.emit("Download stopped by user.")
                self.stopped_signal.emit()
                break

            file_url = post.get("file", {}).get("url")
            if not file_url:
                md5 = post.get("file", {}).get("md5")
                ext = post.get("file", {}).get("ext", "")
                if md5:
                    file_url = f"https://static1.e621.net/data/{md5[:2]}/{md5[2:4]}/{md5}.{ext}"
                else:
                    self.log_signal.emit("No file URL or MD5 available for this post.")
                    continue

            filename = self.download_post(file_url, self.download_output, self.USER_AGENT)
            if filename:
                self.log_signal.emit(f"Downloaded: {filename}")
            self.progress_signal.emit(int(i / total * 100))

        self.stopped_signal.emit()

    def fetch_posts(self, query, limit):
        API_ENDPOINT = "https://e621.net/posts.json"
        posts = []
        page = 1

        while len(posts) < limit:
            params = {
                "page": page,
                "tags": query,
                "limit": 320
            }

            try:
                response = requests.get(API_ENDPOINT, headers={"User-Agent": self.USER_AGENT}, params=params)

                response.raise_for_status()
                data = response.json()

                if not data["posts"]:
                    break

                remaining = limit - len(posts)
                posts_to_add = data["posts"][:min(320, remaining)]
                posts.extend(posts_to_add)

                page += 1

            except Exception as e:
                self.log_signal.emit(f"Failed to fetch page {page}: {e}")
                break

        return posts[:limit]

    def download_post(self, url, output_dir, user_agent):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = os.path.join(output_dir, url.split("/")[-1])
        try:
            response = requests.get(url, headers={"User-Agent": user_agent}, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_flag:
                        return None
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        self.file_progress_signal.emit(int(downloaded / total_size * 100))
            return filename
        except Exception as e:
            self.log_signal.emit(f"Failed to download {url}: {e}")
            return None
