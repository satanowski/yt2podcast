from datetime import datetime
from pathlib import Path
from time import mktime

import youtube_dl
from feedparser import parse
from loguru import logger as log

YT_BASE = "http://www.youtube.com/feeds/videos.xml?channel_id={}"
OUT_FILE = None


def _get_feed(uuid: str) -> dict:
    channel = parse(YT_BASE.format(uuid))
    return {"feed": channel["feed"], "entries": channel["entries"]}


def get_channel_name(uuid: str) -> dict:
    channel = _get_feed(uuid)
    return channel["feed"]["title"]


def get_channel_entries(uuid: str) -> dict:
    channel = _get_feed(uuid)
    return {
        entry["yt_videoid"]: (
            entry["title"],
            datetime.fromtimestamp(mktime(entry["published_parsed"])),
        )
        for entry in channel["entries"]
    }


def ytdl_hook(data):
    global OUT_FILE
    if data["status"] == "finished":
        OUT_FILE = data["filename"]
        log.info("Done downloading, now converting ...")


def download_and_process(uuid: str) -> str:
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": f"{int(datetime.now().timestamp())}-%(title)s.%(ext)s",
        "logger": None,
        "progress_hooks": [ytdl_hook],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={uuid}"])
        path = Path(OUT_FILE)
        return path.name.replace(path.suffix, ".mp3")
