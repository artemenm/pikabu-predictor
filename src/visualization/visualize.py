import pandas as pd
import os
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from pathlib import Path
import numpy as np
from PIL import Image
from collections import Counter
from wordcloud import ImageColorGenerator

def collect_all_data(df):
    df.reset_index(inplace=True)
    df.head()
    all_tags = []
    for i in df.tags:
        all_tags += i[2:-2].split("', '")
    return all_tags

def get_csv_files(path):
    _, _, filenames = next(os.walk(path))
    filenames = filter(lambda x : x.endswith('.csv'), filenames)
    return filenames

def get_path(dir):
    project_dir = os.path.abspath('')
    image_dir = os.path.join(project_dir, *dir)
    path = os.path.join(project_dir , image_dir)
    return path

def get_tags():
    path = get_path(["data", "raw"])
    filenames = get_csv_files(path)
    all_tags = []
    for filename in filenames:
        df = pd.read_csv(os.path.join(path, filename))
        all_tags += collect_all_data(df)
    tags_and_counts = Counter(all_tags)
    popular_tags = []
    for i in range(50):
        popular_tags.append(tags_and_counts.most_common(50)[i][0])
    print(popular_tags)
    return tags_and_counts

def create_wordcloud(tags_and_counts):
    path = get_path(["notebooks", "picabu_ru.jpg"])
    mask = np.array(Image.open(path))
    image_colors = ImageColorGenerator(mask)
    wordcloud = WordCloud(max_words=200, background_color="black", width=2000, height=1000,
                     mask=mask, color_func = image_colors).fit_words(tags_and_counts) 
    return wordcloud

def save_wordcloud_as_image(wordcloud):
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig("wordcloud.jpg",facecolor='k')
    plt.show()

if __name__ == "__main__":
    tags_and_counts = get_tags()
    wordcloud = create_wordcloud(tags_and_counts)
    save_wordcloud_as_image(wordcloud)