import os
import numpy as np
import pandas as pd
import re
from collections import Counter
from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel
from dostoevsky.data import DataDownloader, AVAILABLE_FILES


def download_dostoevsky_data():
    downloader = DataDownloader()
    filename = 'fasttext-social-network-model'
    source, destination = AVAILABLE_FILES[filename]
    downloader.download(source=source, destination=destination)


def get_csv_files(path):
    _, _, filenames = next(os.walk(path))
    filenames = filter(lambda x: x.endswith('.csv'), filenames)
    return filenames


def get_path(dir):
    project_dir = os.path.abspath('')
    image_dir = os.path.join(project_dir, *dir)
    path = os.path.join(project_dir, image_dir)
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
        features.features[i] = pd.Series(feature[i])
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


def get_text_length_ranges(df):
    lens = df.text.dropna().apply(lambda x: len(x))
    quantiles = [-np.inf] + [lens.quantile(i / 5) for i in range(4)] + [np.inf]

    ranges = {}
    for i in range(0, len(quantiles) - 1):
        ranges[i] = (quantiles[i], quantiles[i + 1])

    print(len(ranges))
    return ranges


class Features:
    def __init__(self, popular_tags, rate_ranges):
        self.TARGET_VALUE = ['rate_class']
        self.FEATURES_LIST = ["links_count", 'is_long_title', 'title_pos_sent', 'title_neg_sent', 'title_neu_sent', 'text', "popular_tags_count",
                              "tags_count", "pos_tags_count", "neg_tags_count", "is_original",  'image_count', 'publ_hour', 'publ_weekday', 'is_holiday',
                              'video_count', 'text_len', "geo_tags", 'text_pos_sent', 'text_neg_sent', 'text_neu_sent', 'author_name']
        self.rate_ranges = rate_ranges
        self.popular_tags = popular_tags
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
    return pd.Series([1 if len(s.split()) > 3 else 0 for s in x])


def get_sent(x):
    def one_hot_encode_sent(x):
        """
        (pos, neg, neu)
        """
        if x[0] == 'positive':
            return (1, 0, 0)
        elif x[0] == 'negative':
            return (0, 1, 0)
        else:
            return (0, 0, 1)

    tokenizer = RegexTokenizer()
    model = FastTextSocialNetworkModel(tokenizer=tokenizer)
    results = model.predict(x, k=1)
    results = [(list(r.keys())[0], list(r.values())[0]) for r in results]
    results = list(map(one_hot_encode_sent, results))
    results = [results[i] if x[i] != 'EMPTY_TEXT' else (0, 0, 0) for i in range(len(results))]
    return [pd.Series(x) for x in zip(*results)]  # return three series


def create_features_csv(df, features):
    #get_text_length_ranges(df)

    x = df['rating']
    target = transform_rating_to_class(x, features.rate_ranges)

    feature = {}

    x = df['tags']
    feature["popular_tags_count"] = popular_tag_count(x, features.popular_tags)

    x = df['title']
    feature['is_long_title'] = is_long_title(x)
    title_sent = get_sent(x)
    feature['title_pos_sent'], feature['title_neg_sent'], feature['title_neu_sent'] = title_sent

    x = df['text'].fillna('EMPTY_TEXT')
    text_sent = get_sent(x)
    feature['text_pos_sent'], feature['text_neg_sent'], feature['text_neu_sent'] = text_sent

    x = df['text']
    feature['links_count'] = links_count(x)

    #print(df.columns)
    return target, feature


download_dostoevsky_data()  # comment this if already downloaded
path = get_path(["data", "raw"])
f = get_csv_files(path)
features = open_all_csv(f)
print([str(key) + " " + str(features.features[key].sum()) for key in features.features.keys() if not features.features[key].empty])
