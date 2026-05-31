from __future__ import annotations

import json
import logging
import re
import urllib.parse
from http import HTTPStatus
from typing import TYPE_CHECKING, TypedDict

from enea_client.utils.connection import get_cookie_header, open_connection

if TYPE_CHECKING:
    from enea_client.config import Config

logger = logging.getLogger(__name__)

class Response(TypedDict, total=False):
    success: int
    data: str

class Client:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session_cookie_name = "EBOK_SESSION"
        self.signed_cookie: str = ""

    def authenticate(self) -> bool:
        logger.info("Authenticating")

        session = self._create_session()

        if session is None:
            return False

        unsigned_cookie, token = session

        signed_cookie = self._sign_session(unsigned_cookie, token)

        if signed_cookie is None:
            return False

        self.signed_cookie = signed_cookie

        return True

    def get_data(self, date: str) -> str | None:
        logger.info("Getting data for date: %s", date)

        with open_connection(self.config.enea_url, self.config.connection_timeout) as connection:
            connection.request(
                "POST",
                "/meter/summaryBalancingChart/csv",
                body=urllib.parse.urlencode({
                    "duration": "month",
                    "date": date,
                    "pointOfDeliveryId": self.config.enea_pod_guid,
                }),
                headers={
                    "Content-type": "application/x-www-form-urlencoded",
                    "Cookie": self.signed_cookie,
                    "User-Agent": self.config.enea_user_agent,
                },
            )

            response = connection.getresponse()

            if response.status != HTTPStatus.OK:
                logger.error("Error: status - %s, reason - %s", response.status, response.reason)
                return None

            body = response.read().decode()
            parsed_body: Response = json.loads(body)

            if parsed_body.get("success") != 1:
                logger.error("Error: message - %s", parsed_body)
                return None

            return parsed_body.get("data")

    def _create_session(self) -> tuple[str, str] | None:
        with open_connection(self.config.enea_url, self.config.connection_timeout) as connection:
            connection.request("GET", "/logowanie")
            response = connection.getresponse()

            if response.status != HTTPStatus.OK:
                logger.error("Error: status - %s, reason - %s", response.status, response.reason)
                return None

            session_cookie = get_cookie_header(
                response.headers.get_all("Set-Cookie"),
                self.session_cookie_name,
            )
            if session_cookie is None:
                logger.error("Error: %s cookie not found", self.session_cookie_name)
                return None

            body = response.read().decode()
            token = re.findall(r'name="token" value="([^"]+)"', body)[0]

            return session_cookie, token

    def _sign_session(self, cookie: str, token: str) -> str | None:
        with open_connection(self.config.enea_url, self.config.connection_timeout) as connection:
            connection.request(
                "POST",
                "/logowanie",
                body=urllib.parse.urlencode({
                    "email": self.config.enea_login,
                    "password": self.config.enea_password,
                    "token": token,
                }),
                headers={
                    "Content-type": "application/x-www-form-urlencoded",
                    "Cookie": cookie,
                },
            )
            response = connection.getresponse()

            if response.status != HTTPStatus.FOUND:
                logger.error("Error: status - %s, reason - %s", response.status, response.reason)
                return None

            session_cookie = get_cookie_header(
                response.headers.get_all("Set-Cookie"),
                self.session_cookie_name,
            )
            if session_cookie is None:
                logger.error("Error: %s cookie not found", self.session_cookie_name)
                return None

            connection.request(
                "GET",
                "/dashboard",
                headers={
                    "Cookie": session_cookie,
                    "User-Agent": self.config.enea_user_agent,
                },
            )

            return session_cookie
