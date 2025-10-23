import re

import pandas as pd


def preprocess(data):
    pattern = r'\[(\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)\]\s+(.*?)(?=\[\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M\]|$)'
    matches = re.findall(pattern, data, re.DOTALL)

    df = pd.DataFrame(matches, columns=['Timestamp', 'Message'])

    df['Message'] = df['Message'].str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%m/%d/%y, %I:%M:%S %p')

    df[['User', 'Message']] = df['Message'].str.split(':', n=1, expand=True)
    df['User'] = df['User'].str.strip()
    df['Message'] = df['Message'].str.strip()

    df['User'] = df['User'].str.replace('~', '').str.strip()
    df['User'] = df['User'].fillna('Group Notification')

    df["year"] = df["Timestamp"].dt.year
    df["month"] = df["Timestamp"].dt.month_name()
    df["month_num"] = df["Timestamp"].dt.month
    df["day"] = df["Timestamp"].dt.day
    df["hour"] = df["Timestamp"].dt.hour
    df["minute"] = df["Timestamp"].dt.minute
    df['only_date'] = df['Timestamp'].dt.date

    # In your preprocessor.py, after creating the dataframe and before returning it:

    # Filter out system messages and common non-user entries
    system_keywords = [
        'You',  # When you perform actions
        'Messages and calls are end-to-end encrypted',
        'created this group',
        'added',
        'removed',
        'left',
        'changed',
        'deleted this message',
        'This message was deleted',
        'image omitted',
        'video omitted',
        'audio omitted',
        'document omitted',
        'sticker omitted',
        'GIF omitted',
        'Waiting for this message'
    ]

    # Remove rows where User column contains any system keywords
    for keyword in system_keywords:
        df = df[~df['User'].str.contains(keyword, case=False, na=False)]

    # Remove rows where User contains group names (usually has ':' in the name)
    # But keep actual users who might have ':' in saved contact names
    df = df[~df['User'].str.contains(r'^[A-Z\s]+:', regex=True, na=False)]

    # Remove rows where Message is a system message
    system_message_patterns = [
        r'^\s*$',  # Empty messages
        r'Messages and calls are end-to-end encrypted',
        r'created this group',
        r'added you',
        r'changed the',
        r'Security code changed'
    ]

    for pattern in system_message_patterns:
        df = df[~df['Message'].str.contains(pattern, case=False, na=False, regex=True)]

    # Remove any rows where User is NaN or empty
    df = df[df['User'].notna()]
    df = df[df['User'].str.strip() != '']


    return df