# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from datetime import date
from dotenv import find_dotenv, load_dotenv
import logging
import os
import pandas as pd
from pathlib import Path
import requests
from typing import List, Literal


DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
        "Referer": "https://pikabu.ru/",
        "Host": "pikabu.ru",
        "Origin": "pikabu.ru"
    }


class Post():
    """
    Класс описывает один пост

    Атрибуты
    --------
    rating: int
        рейтинг
    link: str

    text: str
        текст
    tags: List[str]
        список тегов
    title: str
        название
    image_count: int
        число прикрепленных изображений
    datetime: date
        дата и время публикации

    Методы
    ------

    """

    def __init__(self,
                 rating: int = 0,
                 link: str = "",
                 text: str = "",
                 tags: List[str] = [""],
                 title: str = "",
                 image_count: int = 0,
                 datetime: date = date(1, 1, 1)):
        """Параметры см. в описании класса"""

        self.rating = rating
        self.link = link
        self.text = text
        self.tags = tags
        self.title = title
        self.image_count = image_count
        self.datetime = datetime

    # def get_rating(self, post)


class Contents():
    """
    Класс описывает контент, состоящий из выгруженного с сайта кода страниц

    Статические атрибуты
    --------------------
    SITE_URL: str
        адрес сайта
    POSTS_SORTING_METHOD: dict
        дополнение к адресу сайта в зависимости от метода сортировки постов

    Атрибуты
    --------
    posts: List[Post]
        список выгруженных постов
    url: str
        адрес, по которому располагаются посты
    """

    SITE_URL = "https://pikabu.ru/"
    POSTS_SORTING_METHODS = {
        "hot": "",
        "best": "best/",
        "new": "new/"
    }

    def __init__(self, sorting_method: Literal["hot", "best", "new"],
                 page_count: int = 10):
        self.posts = []
        self.url = Contents.SITE_URL + Contents.POSTS_SORTING_METHODS[sorting_method]

    def download_posts(self, page_count: int = 10):
        """
        Скачать верхние посты с сайта

        Параметры
        ---------
        page_count int
            число обрабатываемых страниц (на каждой странице 12 постов)"""

        for page_number in range(1, page_count):
            html = requests.get(self.url + "?page=" + str(page_number),
                                headers=DEFAULT_HEADERS)
            parsed_html = BeautifulSoup(html.text, "html.parser")
            posts = parsed_html.findAll("article")

            print(len(posts))
            for post in posts[:-1]:
                new_post = Post()
                #new_post.get_rating(post)
                self.posts.append(new_post)

def main(output_dir_path):
    """Скачать данные с сайта

    Скачать данные с сайта и поместить в файл /data/raw/posts.csv.
    """

    logger = logging.getLogger(__name__)

    FILENAME = "posts.csv"

    logger.info("скачиваем")

    contents = Contents("new")
    contents.download_posts(2)


if __name__ == "__main__":
    log_fmt = "s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    load_dotenv(find_dotenv())

    project_dir = Path(__file__).resolve().parents[2]
    dirname = os.path.join(project_dir, "data/raw")

    main(dirname)
