# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from collections import defaultdict
import datetime
from dotenv import find_dotenv, load_dotenv
import logging
import os
import pandas as pd
from pathlib import Path
import requests
from typing import List, Literal, Optional


class Post():
    """
    This class represents a post with the following attributes:
    post rating, url, text, list of tags, title, number of images, number
    of video, publication time, author's nickname, and (optionally, since
    it increases parsing time a lot) author's rating
    """

    def __init__(self,
                 rating: Optional[int] = None,
                 url: str = "",
                 text: str = "",
                 tags: List[str] = [],
                 title: str = "",
                 image_count: int = 0,
                 video_count: int = 0,
                 publ_time: datetime.date = datetime.date(1, 1, 1),
                 author_name: Optional[str] = None,
                 author_rating: Optional[int] = None):
        self.rating = rating
        self.url = url
        self.text = text
        self.tags = tags
        self.title = title
        self.image_count = image_count
        self.video_count = video_count
        self.publ_time = publ_time
        self.author_name = author_name
        self.author_rating = author_rating

    def __eq__(self, other):
        """Two posts are duplicates if they have similar url"""
        return self.url == other.url

    def get_data(self, html_text):
        """Download all the post data from the website"""
        self.get_rating(html_text)
        self.get_url(html_text)
        self.get_text(html_text)
        self.get_tags(html_text)
        self.get_title(html_text)
        self.get_image_count(html_text)
        self.get_video_count(html_text)
        self.get_publ_time(html_text)
        self.get_author_name(html_text)
        # self.get_author_rating()

    def get_text(self, html_text):
        paragraphs = html_text.findAll('p')
        text = ""
        for paragraph in paragraphs:
            text += paragraph.text + "\n"
        self.text = text[:-1] if text else text

    def get_rating(self, html_text):
        self.rating = html_text.get('data-rating')

    def get_url(self, html_text):
        url = html_text.find(attrs=["story__title-link"])
        self.url = url['href'] if url else ""

    def get_tags(self, html_text):
        all_tags = html_text.findAll(attrs=['tags__tag'])
        tags = []
        for tag in all_tags:
            tag_data = tag.get("data-tag")
            if tag_data:
                tags.append(tag_data)
        all_tags = html_text.findAll(attrs = ['tags__tag tags__tag_highlight'])
        if len(all_tags) > 0:
            tags.append("моё")
        self.tags = tags

    def get_title(self, html_text):
        title = html_text.find(attrs=["story__title-link"])
        self.title = title.text if title else "Ad"

    def get_image_count(self, html_text):
        images = html_text.findAll(attrs=['story-image__content'])
        self.image_count = len(images) if images else 0

    def get_video_count(self, html_text):
        videos = html_text.findAll(attrs=['player'])
        self.video_count = len(videos) if videos else 0

    def get_publ_time(self, html_text):
        publ_time = html_text.find(attrs=["caption story__datetime hint"])
        publ_time = publ_time['datetime']
        publ_time = datetime.datetime.strptime(publ_time, "%Y-%m-%dT%H:%M:%S%z")
        self.publ_time = publ_time

    def get_author_name(self, html_text):
        author_name = html_text.find(attrs=["user__nick"])['href']
        if author_name != "/404":
            self.author_name = author_name[2:]

    def get_author_rating(self):
        if not self.author_name:
            return
        html = requests.get(Contents.SITE_URL + "/@" + self.author_name,
                            headers=Contents.DEFAULT_HEADERS)
        parsed_html = BeautifulSoup(html.text, "html.parser")

        # check if rating is too large to show uncompressed
        rating_hidden = parsed_html.find(attrs=["profile__digital hint"])

        if rating_hidden:
            rating_by_three_digits = rating_hidden["aria-label"].split("\u2005")
            author_rating = int("".join(rating_by_three_digits))
        else:
            rating = parsed_html.find(attrs=["profile__digital"])
            author_rating = int(rating.find('b').text)

        self.author_rating = author_rating


class Contents():
    """
    This class represents a set of posts downloaded from a specific section
    of the website, based on sorting method (hot/best/new) or a date.
    It supports downoading data and exporting it to csv.
    """

    SITE_URL = "https://pikabu.ru/"
    POST_SORTING_METHODS = {
        "hot": "",
        "best": "best/",
        "new": "new/",
        "search": "search"
    }
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
        "Referer": "https://pikabu.ru/",
        "Host": "pikabu.ru",
        "Origin": "pikabu.ru"
    }
    START_DATE = datetime.date(2008, 1, 1)

    def __init__(self,
                 sorting_method: Literal[POST_SORTING_METHODS.keys()],
                 post_date: datetime.date = datetime.date.today()):
        self.posts = []
        postfix = Contents.POST_SORTING_METHODS[sorting_method]
        if sorting_method == "search":
            day_number = (post_date - Contents.START_DATE).days
            postfix += "?d=" + str(day_number) + "&"
        else:
            postfix += "?"
        self.url = Contents.SITE_URL + postfix
        self.data = pd.DataFrame()

    def download_posts(self, page_count: int = -1):
        """
        Download posts from the top, but no more then page_count
        (a single page contents 13 posts)
        """

        page_number = 1
        condition = True
        while condition:
            html = requests.get(self.url + "page=" + str(page_number),
                                headers=Contents.DEFAULT_HEADERS)
            parsed_html = BeautifulSoup(html.text, "html.parser")
            posts_html = parsed_html.findAll("article")

            for post_html in posts_html[:-1]:
                post = Post()
                post.get_data(post_html)
                self.posts.append(post)

            condition = len(posts_html[:-1]) > 0 and (page_count == -1 or page_number < page_count)
            page_number += 1

    def create_dataframe(self, exclude: List[str] = []):
        columns = defaultdict(list)
        attributes = [attr for attr in Post().__dict__.keys()
                      if attr not in exclude]
        for post in self.posts:
            for attribute in attributes:
                columns[attribute].append(getattr(post, attribute))
        self.data = pd.DataFrame(columns)


def daterange(start_date: datetime.date, end_date: datetime.date):
    """Return iterable range of dates"""
    for i in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(i)


def main(output_dir_path: str,
         start_date: datetime.date,
         end_date: datetime.date):
    """Download data from the website and put it to /data/raw"""

    FILENAME = "posts_{}.csv"

    logger.info("downloading data...")

    for cur_date in daterange(start_date, end_date):
        #try:
            contents = Contents("search", cur_date)
            contents.download_posts()
            contents.create_dataframe(exclude=["author_rating"])
            contents.data.drop_duplicates(subset=["url"], inplace=True)
            contents.data.to_csv(output_dir_path + FILENAME.format(cur_date),
                                 encoding='utf-8',
                                 index=False)

        #    logger.info("successfully downloaded data for " + str(cur_date))
        #except Exception:
        #    logger.error("failed to download data for " + str(cur_date))

    logger.info("data downloading finished")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    load_dotenv(find_dotenv())

    project_dir = Path(__file__).resolve().parents[2]
    dirname = os.path.join(project_dir, os.path.join("data", "raw"))

    main(dirname, datetime.date(2019, 11, 2), datetime.date(2019, 11, 3))
