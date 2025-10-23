import pandas as pd
from urlextract import URLExtract
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
import string
import re
import emoji
import nltk

# ------------------- Fetch Stats -------------------
def fetch_stats(selected_user, df):
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        return 0, 0, 0, 0

    num_messages = df.shape[0]

    words = []
    for message in df["Message"]:
        words.extend(message.split())
    num_words = len(words)

    num_media = df[df["Message"].str.contains(r'\b(?:image|video|audio|document|sticker) omitted\b', regex=True, na=False)].shape[0]

    extractor = URLExtract()
    link = []
    for message in df["Message"]:
        link.extend(extractor.find_urls(message))
    num_links = len(link)

    return num_messages, num_words, num_media, num_links


# ------------------- Most Busy Users -------------------
def most_busy_users(df):
    if df.empty:
        return pd.Series(dtype=int), pd.DataFrame(columns=['Name', 'Percentage'])
    x = df["User"].value_counts().head()
    df_perc = round((df['User'].value_counts() / df.shape[0]) * 100, 2).reset_index()
    df_perc = df_perc.rename(columns={df_perc.columns[0]: 'Name', df_perc.columns[1]: 'Percentage'})
    return x, df_perc


# ------------------- Word Cloud -------------------
def create_wordcloud(selected_user, df):
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        return None

    df = df[~df["Message"].str.contains(r'\b(?:image|video|audio|document|sticker) omitted\b', regex=True, na=False)]
    df = df[~df["Message"].str.contains("Waiting for this message", na=False)]
    df = df[~df["Message"].str.contains("This message was deleted", na=False)]
    df = df[df["Message"].notna()]
    df = df[df["Message"].str.strip() != ""]

    if df.empty:
        return None

    text = df['Message'].str.cat(sep=" ")
    if not text.strip():
        return None

    from wordcloud import STOPWORDS
    # Add random_state to make wordcloud deterministic
    wc = WordCloud(
        background_color="white",
        max_words=200,
        width=800,
        height=400,
        stopwords=STOPWORDS,
        random_state=42  # This makes the layout consistent
    ).generate(text)
    return wc


# ------------------- Most Common Words -------------------
def most_common_words(selected_user, df):
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        return pd.DataFrame(columns=[0, 1])

    nltk.download('stopwords', quiet=True)
    stop_words = set(stopwords.words('english'))

    temp = df[df["User"] != "Group_Notification"]
    temp = temp[~temp["Message"].str.contains(r'\b(?:image|video|audio|document|sticker) omitted\b', regex=True, na=False)]
    temp = temp[~temp["Message"].str.contains("Waiting for this message", na=False)]
    temp = temp[~temp["Message"].str.contains("This message was deleted", na=False)]
    temp = temp[~temp["Message"].str.contains("This message was edited", na=False)]
    temp = temp[temp["Message"].notna()]
    temp = temp[temp["Message"].str.strip() != ""]

    def clean_unicode(message):
        return re.sub(r'[\u200e\u200f\u202a-\u202e]', '', message).strip()

    temp['Message'] = temp['Message'].apply(clean_unicode)

    def remove_stopwords(message):
        words = message.split()
        filtered = [w.strip(string.punctuation) for w in words if w.lower() not in stop_words]
        filtered = [w for w in filtered if w and len(w) > 1]
        return ' '.join(filtered)

    temp['Message'] = temp['Message'].apply(remove_stopwords)
    temp = temp[temp["Message"].str.strip() != ""]

    if temp.empty:
        return pd.DataFrame(columns=[0, 1])

    words = []
    for message in temp["Message"]:
        words.extend(message.split())

    words = [w for w in words if len(w) > 1 and not all(c in string.punctuation for c in w)]
    most_common_df = pd.DataFrame(Counter(words).most_common(10))
    return most_common_df


# ------------------- Emoji Analysis -------------------
def emoji_helper(selected_user, df):
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        return pd.DataFrame(columns=['Emoji', 'Count', 'Percentage'])

    emojis = []
    for message in df["Message"]:
        emojis.extend([c for c in message if emoji.is_emoji(c)])

    if not emojis:
        return pd.DataFrame(columns=['Emoji', 'Count', 'Percentage'])

    emoji_df = pd.DataFrame(Counter(emojis).most_common(), columns=['Emoji', 'Count'])
    emoji_df['Count'] = pd.to_numeric(emoji_df['Count'], errors='coerce').fillna(0)

    total = emoji_df['Count'].sum()
    emoji_df['Percentage'] = round((emoji_df['Count'] / total * 100), 2) if total > 0 else 0

    return emoji_df


# ------------------- Monthly Timeline -------------------
def monthly_timeline(selected_user, df):
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        return pd.DataFrame(columns=['time', 'Message'])

    timeline = df.groupby(['year', 'month_num', 'month']).count()['Message'].reset_index()
    timeline['time'] = timeline['month'] + '-' + timeline['year'].astype(str)
    return timeline


# ------------------- Most Active Weekdays -------------------
def most_active_weekdays(selected_user, df):
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        return pd.Series([0]*7, index=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])

    df['only_date'] = pd.to_datetime(df['only_date'])
    df['weekday'] = df['only_date'].dt.day_name()
    weekday_counts = df.groupby('weekday').count()['Message']
    weekdays_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_counts = weekday_counts.reindex(weekdays_order, fill_value=0)
    return weekday_counts


# ------------------- Most Active Months -------------------
def most_active_months(selected_user, df):
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        return pd.Series(dtype=int)

    df['only_date'] = pd.to_datetime(df['only_date'])
    df['month_year'] = df['only_date'].dt.strftime('%b %Y')
    active_months = df.groupby('month_year').count()['Message'].sort_values(ascending=False)
    return active_months

def activity_heatmap_normalized(selected_user, df):
    """
    Returns a normalized pivot table (0-1) for heatmap: weekdays vs hours
    """
    if selected_user != "Overall":
        df = df[df['User'] == selected_user]

    if df.empty:
        weekdays_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        hours_order = list(range(24))
        return pd.DataFrame(0, index=weekdays_order, columns=hours_order)

    df['only_date'] = pd.to_datetime(df['only_date'], errors='coerce')
    df['weekday'] = df['only_date'].dt.day_name()
    df['hour'] = df['hour'].astype(int)

    heatmap_data = df.pivot_table(index='weekday', columns='hour', values='Message', aggfunc='count', fill_value=0)

    weekdays_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    hours_order = list(range(24))
    heatmap_data = heatmap_data.reindex(index=weekdays_order, columns=hours_order, fill_value=0)

    # Normalize by max
    heatmap_data = heatmap_data / heatmap_data.values.max()

    return heatmap_data