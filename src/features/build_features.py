from bs4 import BeautifulSoup
from collections import defaultdict
import datetime
from dotenv import find_dotenv, load_dotenv
import logging
import os
import numpy as np
import pandas as pd
from pathlib import Path
import requests
from typing import List, Literal, Optional
import re
import math 
from collections import Counter

def get_csv_files(path):
    _, _, filenames = next(os.walk(path))
    filenames = filter(lambda x : x.endswith('.csv'), filenames)
    return filenames

def get_path(dir):
    project_dir = os.path.abspath('')
    image_dir = os.path.join(project_dir, *dir)
    path = os.path.join(project_dir , image_dir)
    return path

def open_all_csv(filenames):
    dfs = []
    for filename in filenames:
        dfs.append(pd.read_csv(os.path.join(path, filename)))
    df = pd.concat(dfs)
    df.reset_index(inplace=True)
    df["publ_time"] = pd.to_datetime(df.publ_time)
    df.head()
    rate_ranges = get_rate_ranges(df)
    popular_tags = get_popular_tags(get_tags())
    features = Features(popular_tags, rate_ranges)
    features.target, feature = create_features_csv(df, features)
    for i in feature.keys():
        features.features[i].append(feature[i])
    return features

def get_rate_ranges(df):
    rate_dec_quantile = [-np.inf]
    for i in range(0, 11):
        rate_dec_quantile.append(df.quantile(i / 10).rating)
    rate_dec_quantile.append(np.inf)
    rate_ranges = {}

    for i in range(0, len(rate_dec_quantile) - 1):
        rate_ranges[i] = (rate_dec_quantile[i], rate_dec_quantile[i + 1])

    return rate_ranges
class Features:
    def __init__(self, popular_tags, rate_ranges):
        self.TARGET_VALUE = ['rate_class']
        self.FEATURES_LIST = ["links_count", 'is_long_title', 'title_pos_sent', 'title_neg_sent', 'title_pos_sent', 'text', "popular_tags_count",
                "tags_count", "pos_tags_count", "neg_tags_count", "is_original",  'image_count', 'publ_hour', 'publ_weekday', 'is_holiday',
                'video_count', 'text_len', 'text_pos_sent', "geo_tags", 'text_neu_sent', 'text_neg_sent', 'author_name']
        self.rate_ranges =  {}
        self.popular_tags = []
        self.target = []
        self.features = {i: pd.Series() for i in self.FEATURES_LIST}


def get_tags():
    path = get_path(["data", "raw"])
    filenames = get_csv_files(path)
    all_tags = []
    for filename in filenames:
        df = pd.read_csv(os.path.join(path, filename))
        all_tags += collect_all_data(df)
    tags_and_counts = Counter(all_tags)
   
    return tags_and_counts

def get_popular_tags(tags_and_counts):
    popular_tags = []
    for i in range(50):
        popular_tags.append(tags_and_counts.most_common(50)[i][0])
    print(popular_tags)
    return popular_tags

def popular_tag_count(tags, popular_tags):
    x = []
    for j in tags:
        k = 0
        for i in j:
            if i in popular_tags:
                k += 1
        x.append(k)
    return pd.Series(x)

def transform_rating_to_class(x, rate_ranges):
    for i in range(len(x)):
        for j in range(len(rate_ranges)):
            if x[i] <= rate_ranges[j][1]:
                x[i] = j
                break
    return x

def links_count(x):
    for i in range(len(x)):
        if isinstance(x[i], str):
            s = len(re.findall(r'http', x[i]))
            x[i] = s
        else:
            x[i] = 0
    return x

def collect_all_data(df):
    df.reset_index(inplace=True)
    df.head()
    all_tags = []
    for i in df.tags:
        all_tags += i[2:-2].split("', '")
    return all_tags
    
def is_long_title(x):
    return  pd.Series([1 if len(s.split()) > 3 else 0 for s in x])

def create_features_csv(df, features):
    x = df['rating']
    target = transform_rating_to_class(x, features.rate_ranges)
    feature = {}
    x = df['text']
    feature['links_count'] = links_count(x)
    x = df['tags']
    feature["popular_tags_count"] = popular_tag_count(x, features.popular_tags)
    x = df['title'] 
    feature['is_long_title'] = is_long_title(x)
    #print(df.columns)
    return target, feature

path = get_path(["data", "raw"])
f = get_csv_files(path)
open_all_csv(f)
