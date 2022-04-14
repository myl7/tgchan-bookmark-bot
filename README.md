# tgchan-bookmark-bot

After you save a page as bookmark, post it in the Telegram channel

## Config

Config options are passed by either envs or dotenv

| name          | description                                     | default value                 | extra                                                                                                                                                                             |
| ------------- | ----------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BOT_TOKEN     | Telegram bot token                              | /                             |                                                                                                                                                                                   |
| XBEL_URL      | URL of the XBEL bookmark file                   | /                             |                                                                                                                                                                                   |
| DB_PATH       | SQLite database file path                       | `db.sqlite3`                  |                                                                                                                                                                                   |
| POLL_INTERVAL | interval of requests to the XBEL URL            | 360                           | unit: second                                                                                                                                                                      |
| CHAN_NAME     | Telegram channel name sent messages to          | /                             | Either starting with @ or not is OK, like `@myl7s` or `myl7s`                                                                                                                     |
| MSG_TEMPLATE  | Message format string to generate sent messages | `New bookmark: {title} {url}` | Python `.format()` style format string, whose `{title}` and `{url}` will be replaced with bookmark title and URL. Here string without `{title}` or `{url}` will cause exceptions. |

## Usage

Docker image `myl7/tgchan-bookmark-bot` is available in Docker Hub.
Tag `edge` is bleeding edge build from CI and tag `latest` is latest release with a version.
Semantic versioning is available so feel free to use tag `1`, `1.1` or `1.1.1`.
Dir `/db` is created in advance and it is suggested to store the database file in it for Docker binding mounting.

Run the image like:

```bash
docker run -d --name=bookmark --restart=unless-stopped \
  -e BOT_TOKEN=<...> \
  -e XBEL_URL=<...> \
  -e DB_PATH=/db/db.sqlite3 \
  -e CHAN_NAME=<...> \
  -v <...>:/db \
  myl7/tgchan-bookmark-bot:latest
```

## License

Copyright (c) 2022 myl7

SPDX-License-Identifier: Apache-2.0
