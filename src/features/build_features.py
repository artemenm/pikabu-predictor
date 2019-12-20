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

def open_csv(filenames):
    targets = []
    features = []
    for filename in filenames:
        df = pd.read_csv(os.path.join(path, filename))
        df.reset_index(inplace=True)
        df.head()
        print(filename)
        target, feature = create_features_csv(df)
        features.append(feature)
        targets.append(target)
    return targets, features

TARGET_VALUE = ['rate_class']
FEATURES_LIST = ["links_count", 'is_long_title', 'title_pos_sent', 'title_neg_sent', 'title_pos_sent', 'text', "popular_tags_count",
        "tags_count", "pos_tags_count", "neg_tags_count", "is_original",  'image_count', 'publ_hour', 'publ_weekday', 'is_holiday',
        'video_count', 'text_len', 'text_pos_sent', "geo_tags", 'text_neu_sent', 'text_neg_sent', 'author_name']
RATE_RANGES = {0: (-1e6, -1943.0), 1: (-1943.0, -18.0), 2: (-18.0, -9.0), 3: (-9.0, 0.0), 4: (0.0, 6.0), 5: (6.0, 12.0),
                 6: (12.0, 21.0), 7: (21.0, 48.0), 8: (48.0, 141.0), 9: (141.0, 633.0), 10: (633.0, 27021.0), 11: (27021.0, 1e6)}
popular_tags = []
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

def popular_tag_count(tags):
    k = 0
    for i in tags:
        if i in popular_tags:
            k += 1
    return k

def transform_rating_to_class(x):
    for i in range(len(x)):
        for j in range(len(RATE_RANGES)):
            if x[i] <= RATE_RANGES[j][1]:
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

def create_features_csv(df):
    x = df['rating']
    target = transform_rating_to_class(x)
    feature = {}
    x = df['text']
    feature['link_count'] = links_count(x)
    x = df['tags']
    feature["popular_tags_count"] = popular_tag_count(x)

    #print(df.columns)
    return target, feature

path = get_path(["data", "raw"])
popular_tags = get_popular_tags(get_tags())
f = get_csv_files(path)
open_csv(f)
