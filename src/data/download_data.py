# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime, date
from dotenv import find_dotenv, load_dotenv
import logging
import os
import pandas as pd
from pathlib import Path
import requests
from typing import List, Literal, Optional


class Post():
    """
    Класс описывает один пост

    Атрибуты
    --------
    rating: int
        рейтинг
    link: str
        ссылка на пост
    text: str
        текст
    tags: List[str]
        список тегов
    title: str
        название
    image_count: int
        число прикрепленных изображений
    publ_time: date
        дата и время публикации

    Методы
    ------

    """

    def __init__(self,
                 rating: Optional[int] = 0,
                 link: str = "",
                 text: str = "",
                 tags: List[str] = [""],
                 title: str = "",
                 image_count: int = 0,
                 publ_time: date = date(1, 1, 1),
                 author_name: str = "/@",
                 author_rating: int = 0):
        """Параметры см. в описании класса"""

        self.rating = rating
        self.link = link
        self.text = text
        self.tags = tags
        self.title = title
        self.image_count = image_count
        self.publ_time = publ_time
        self.author_name = author_name
        self.author_rating = author_rating
    
    def get_data(self, html_text):
        self.get_rating(html_text)
        self.get_link(html_text)
        self.get_text(html_text)
        self.get_tags(html_text)
        self.get_title(html_text)
        self.get_image_count(html_text)
        self.get_publ_time(html_text)
        self.get_author_name(html_text)
        self.get_author_rating()

    def get_text(self, html_text):
        paragraphs = html_text.findAll('p')
        text = ""
        for paragraph in paragraphs:
            text += paragraph.text + "\n"
        self.text = text

    def get_rating(self, html_text):
        self.rating = html_text.get('data-rating')

    def get_link(self, html_text):
        link = html_text.find(attrs=["story__title-link"])
        self.link = link['href'] if link else ""

    def get_tags(self, html_text):
        all_tags = html_text.findAll(attrs=['tags__tag'])
        tags = []
        for tag in all_tags:
            tag_data = tag.get("data-tag")
            if tag_data:
                tags.append(tag_data)
        self.tags = tags

    def get_title(self, html_text):
        title = html_text.find(attrs=["story__title-link"])
        self.title = title.text if title else "Ad"

    def get_image_count(self, html_text):
        images = html_text.findAll(attrs=['story-image__content'])
        self.image_count = len(images) if images else 0

    def get_publ_time(self, html_text):
        publ_time = html_text.find(attrs=["caption story__datetime hint"])
        publ_time = publ_time['datetime']
        publ_time = datetime.strptime(publ_time, "%Y-%m-%dT%H:%M:%S+03:00")
        self.publ_time = publ_time

    def get_author_name(self, html_text):
        author_name = html_text.find(attrs=["user__nick"])['href']
        self.author_name = author_name[2:]
    
    def get_author_rating(self):
        html = requests.get(Contents.SITE_URL + "/@" + self.author_name,
                            headers=Contents.DEFAULT_HEADERS)
        parsed_html = BeautifulSoup(html.text, "html.parser")
        if (rating_hidden := parsed_html.find(attrs=["profile__digital hint"])):
            rating_by_three_digits = rating_hidden["aria-label"].split("\u2005")
            author_rating = int("".join(rating_by_three_digits))
        else:
            rating = parsed_html.find(attrs=["profile__digital"])
            author_rating = int(rating.find('b').text)
        self.author_rating = author_rating


class Contents():
    """
    Класс описывает контент, состоящий из выгруженного с сайта кода страниц

    Статические атрибуты
    --------------------
    SITE_URL: str
        адрес сайта
    POSTS_SORTING_METHOD: dict
        дополнение к адресу сайта в зависимости от метода сортировки постов
    DEFAULT_HEADERS: dict
        хедеры для реквеста

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
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
        "Referer": "https://pikabu.ru/",
        "Host": "pikabu.ru",
        "Origin": "pikabu.ru"
    }

    def __init__(self, sorting_method: Literal["hot", "best", "new"],
                 page_count: int = 10):
        self.posts = []
        postfix = Contents.POSTS_SORTING_METHODS[sorting_method]
        self.url = Contents.SITE_URL + postfix
        self.df = pd.DataFrame()

    def download_posts(self, page_count: int = 10):
        """
        Скачать верхние посты с сайта

        Параметры
        ---------
        page_count: int
            число обрабатываемых страниц (на каждой странице 12 постов)
        """

        for page_number in range(1, page_count):
            html = requests.get(self.url + "?page=" + str(page_number),
                                headers=Contents.DEFAULT_HEADERS)
            parsed_html = BeautifulSoup(html.text, "html.parser")
            posts_html = parsed_html.findAll("article")

            for post_html in posts_html[:-1]:
                post = Post()
                post.get_data(post_html)
                self.posts.append(post)
        
    def create_dataframe(self, exclude: List[str] = []):
        columns = defaultdict(list)
        attributes = [attr for attr in Post().__dict__.keys()
        if attr not in exclude]
        for post in self.posts:
            for attribute in attributes:
                columns[attribute].append(getattr(post, attribute))
        self.df = pd.DataFrame(columns)


def main(output_dir_path):
    """Скачать данные с сайта и поместить в /data/raw/posts.csv"""

    logger = logging.getLogger(__name__)

    FILENAME = "posts.csv"

    logger.info("downloading data...")

    contents = Contents("best")
    contents.download_posts(page_count=4)
    contents.create_dataframe(["link", "author_name"])
    contents.df.to_csv(output_dir_path + FILENAME, index=False)


if __name__ == "__main__":
    log_fmt = "s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    load_dotenv(find_dotenv())

    project_dir = Path(__file__).resolve().parents[2]
    dirname = os.path.join(project_dir, "data/raw/")

    main(dirname)
