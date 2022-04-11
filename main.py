# Copyright (c) 2022 myl7
# SPDX-License-Identifier: Apache-2.0

import os
import xml.etree.ElementTree as ET
import logging
import sqlite3
from time import sleep

import requests
import dotenv

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if BOT_TOKEN is None:
    logging.critical('BOT_TOKEN not set')
XBEL_URL = os.getenv('XBEL_URL')
if XBEL_URL is None:
    logging.critical('XBEL_URL not set')
DB_PATH = os.getenv('DB_PATH')
if DB_PATH is None:
    DB_PATH = 'db.sqlite3'
POLL_INTERVAL = os.getenv('POLL_INTERVAL')  # Seconds
if POLL_INTERVAL is None:
    POLL_INTERVAL = 360


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


def main():
    cursor = get_db()
    init_db(cursor)
    while True:
        try:
            bookmarks = get_xbel()
            for bookmark in bookmarks:
                if not check_bookmark(cursor, bookmark):
                    save_bookmark(cursor, bookmark)
                    logging.info(f'Saved bookmark: {bookmark["title"]}')
        except Exception as e:
            logging.error(f'Error: {e}')
        sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
