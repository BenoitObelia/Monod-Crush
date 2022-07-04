from logging import LogRecord, Handler, Filter
from typing import List, Literal
import logging

import requests
from django.http import HttpRequest
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)


def user_or_ip(request: HttpRequest) -> str:
    """ Returns the user or IP of the request. """
    if request.user.is_authenticated:
        return f"{request.user.username}#{request.user.id}"
    else:
        return request.META.get('REMOTE_ADDR', 'no IP')


class DiscordHandler(Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a Discord Server using webhooks.
    """

    def __init__(self, webhook_url: str,
                 notify_users_level: int = logging.ERROR,
                 notify_users: List[int] = (),
                 max_length: int = 2000):
        super().__init__()

        self._url = webhook_url
        self._notify_level = notify_users_level
        self._notify_users = notify_users
        self._url = webhook_url
        self._max_length = max_length

    def emit(self, record: logging.LogRecord) -> None:
        """ Emit a record. """
        msg = self.format(record)
        trimmed_msg = [msg[i:i + self._max_length] for i in range(0, len(msg), self._max_length)]
        trimmed_msg = [f"```{m}```" for m in trimmed_msg]

        if record.levelno >= self._notify_level and self._notify_users:
            users = '\n'.join(f'<@{user}>' for user in self._notify_users)
            trimmed_msg += [f"\n{users}"]

        try:
            for msg in trimmed_msg:
                self.write_to_discord(msg)
        except Exception:
            self.handleError(record)

    def write_to_discord(self, message: str) -> None:
        """ Sends a message to Discord using a webhook. """
        request = requests.post(self._url, data={"content": message})

        if not request.ok:
            raise HTTPError(f"HTTP Error: {request.status_code}")


class UserOrIPFilter(Filter):
    """ A filter class that adds user information if the user is logged in, otherwise adds the client's IP address to the log record."""

    def filter(self, record: LogRecord) -> bool:
        """
        Add user information to the log record if the user is logged in, otherwise add the client's IP address.

        example log record:
        log.info("User: %s, IP: %s", user, ip)
        """
        if hasattr(record, 'user'):
            record.user_or_ip = f"{record.user.username} ({record.user.id})"
        else:
            record.user_or_ip = record.client_ip
        return True
