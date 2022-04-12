# Copyright (c) 2022 myl7
# SPDX-License-Identifier: Apache-2.0

import os
import xml.etree.ElementTree as ET
import logging
import sqlite3
from time import sleep

import requests
import dotenv
import telegram

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if BOT_TOKEN is None:
    logging.critical('BOT_TOKEN not set')
    exit(1)
XBEL_URL = os.getenv('XBEL_URL')
if XBEL_URL is None:
    logging.critical('XBEL_URL not set')
    exit(1)
DB_PATH = os.getenv('DB_PATH')
if DB_PATH is None:
    DB_PATH = 'db.sqlite3'
POLL_INTERVAL = os.getenv('POLL_INTERVAL')  # Seconds
if POLL_INTERVAL is None:
    POLL_INTERVAL = 360
CHAN_NAME = os.getenv('CHAN_NAME')
if CHAN_NAME is None:
    logging.critical('CHAN_NAME not set')
    exit(1)
elif not CHAN_NAME.startswith('@'):
    CHAN_NAME = f'@{CHAN_NAME}'
MSG_TEMPLATE = os.getenv('MSG_TEMPLATE')
if MSG_TEMPLATE is None:
    MSG_TEMPLATE = 'New bookmark: {title} {url}'
elif MSG_TEMPLATE.find('{title}') == -1 or MSG_TEMPLATE.find('{title}') == -1:
    logging.critical('MSG_TEMPLATE must contain {title} and {url}')
    exit(1)

bot = telegram.Bot(token=BOT_TOKEN)
me = bot.get_me()
logging.info(f'Bot {me.username} started')


class AppException(Exception):
    pass


def get_xbel():
    res = requests.get(XBEL_URL)
    if res.status_code != 200:
        raise AppException(f'Req XBEL failed with status code {res.status_code}')
    body = res.content.decode()
    root = ET.fromstring(body)
    if root.tag != 'xbel':
        raise AppException(f'Invalid XBEL: Expected <xbel> but got <{root.tag}>')
    bookmarks = [child for child in root if child.tag == 'bookmark']
    logging.debug(f'Got {len(bookmarks)} bookmarks')
    return [{
        'url': bookmark.attrib['href'],
        'title': bookmark[0].text,
        'bid': int(bookmark.attrib['id'])
    } for bookmark in bookmarks]


def get_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    cursor = conn.cursor()
    return cursor


def init_db(cursor):
    with open('schema.sql') as f:
        cursor.execute(f.read())


def save_bookmark(cursor, bookmark):
    cursor.execute(
        'INSERT INTO bookmarks (url, title, bid) VALUES (?, ?, ?)',
        (bookmark['url'], bookmark['title'], bookmark['bid'])
    )


def check_bookmark(cursor, bookmark):
    cursor.execute(
        'SELECT * FROM bookmarks WHERE url = ?',
        (bookmark['url'],)
    )
    row = cursor.fetchone()
    return row is not None


def send_msg(bookmark):
    text = MSG_TEMPLATE.format(title=bookmark['title'], url=bookmark['url'])
    bot.send_message(CHAN_NAME, text)


def main():
    cursor = get_db()
    init_db(cursor)
    while True:
        try:
            bookmarks = get_xbel()
            for bookmark in bookmarks:
                if not check_bookmark(cursor, bookmark):
                    send_msg(bookmark)
                    save_bookmark(cursor, bookmark)
                    logging.info(f'Sent and saved bookmark: {bookmark["title"]}')
        except Exception as e:
            logging.error(f'Error: {e}')
        sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
