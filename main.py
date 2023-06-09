# Copyright (c) 2022 myl7
# SPDX-License-Identifier: Apache-2.0

import os
import xml.etree.ElementTree as ET
import logging
import asyncio

import dotenv
import telegram
import aiosqlite
import aiohttp

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
elif MSG_TEMPLATE.find('{title}') == -1 or MSG_TEMPLATE.find('{url}') == -1:
    logging.critical('MSG_TEMPLATE must contain {title} and {url}')
    exit(1)
DRY_RUN = os.getenv('DRY_RUN')

SCHEMA = '''
CREATE TABLE IF NOT EXISTS bookmarks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  bid INTEGER NOT NULL
);
'''


class AppException(Exception):
    pass


async def get_xbel():
    async with aiohttp.ClientSession() as session:
        async with session.get(XBEL_URL) as res:
            if res.status != 200:
                raise AppException(f'Req XBEL failed with status code {res.status}')
            body = await res.text()
            root = ET.fromstring(body)
            if root.tag != 'xbel':
                raise AppException(f'Invalid XBEL: Expected <xbel> but got <{root.tag}>')
            bookmarks = [child for child in root if child.tag == 'bookmark']
            logging.debug(f'Got {len(bookmarks)} bookmarks')
            return [{
                'url': bookmark.attrib['href'],
                'title': bookmark[0].text if bookmark[0].text else '<no title>',
                'bid': int(bookmark.attrib['id'])
            } for bookmark in bookmarks]


async def save_bookmark(db, bookmark):
    await db.execute(
        'INSERT INTO bookmarks (url, title, bid) VALUES (?, ?, ?)',
        (bookmark['url'], bookmark['title'], bookmark['bid'])
    )


async def check_bookmark(db, bookmark):
    async with db.execute(
        'SELECT * FROM bookmarks WHERE url = ?',
        (bookmark['url'],)
    ) as cursor:
        row = await cursor.fetchone()
        return row is not None


async def send_msg(bot: telegram.Bot, bookmark):
    text = MSG_TEMPLATE.format(title=bookmark['title'], url=bookmark['url'])
    if DRY_RUN:
        logging.info(f'Dry run: To send {text}')
    else:
        await bot.send_message(CHAN_NAME, text)


async def main():
    bot = telegram.Bot(token=BOT_TOKEN)
    me = await bot.get_me()
    logging.info(f'Bot {me.username} started')
    async with aiosqlite.connect(DB_PATH, isolation_level=None) as db:
        await db.execute(SCHEMA)
        while True:
            try:
                bookmarks = await get_xbel()
                for bookmark in bookmarks:
                    if not await check_bookmark(db, bookmark):
                        await send_msg(bot, bookmark)
                        await save_bookmark(db, bookmark)
                        logging.info(f'Sent and saved bookmark: {bookmark["title"]}')
            except aiosqlite.Error as e:
                # Critical
                logging.error(f'SQLite3 Error: {e}')
                exit(1)
            except Exception as e:
                logging.error(f'Error: {e}')
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    asyncio.run(main())
