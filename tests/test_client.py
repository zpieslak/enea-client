from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from enea_client.client import Client

if TYPE_CHECKING:
    from pytest import LogCaptureFixture
    from pytest_httpserver import HTTPServer

    from enea_client.config import Config


def test_client_aithenticate_success(httpserver: HTTPServer, config: Config) -> None:
    httpserver.expect_request("/logowanie", method="GET").respond_with_data(
        '<input type="hidden" name="token" value="token-123">',
        status=HTTPStatus.OK,
        headers={
            "Set-Cookie": "SESSION=unsigned; Path=/; HttpOnly",
            "Content-Type": "text/html",
        },
    )

    httpserver.expect_request("/logowanie", method="POST").respond_with_data(
        "",
        status=HTTPStatus.FOUND,
        headers={
            "Set-Cookie": "SESSION=signed; Path=/; HttpOnly",
            "Location": "/",
        },
    )

    client = Client(config)
    assert client.authenticate() is True
    assert client.signed_cookie == "SESSION=signed; Path=/; HttpOnly"

def test_client_authenticate_session_none(config: Config, httpserver: HTTPServer) -> None:
    config.enea_url = httpserver.url_for("")

    httpserver.expect_request("/logowanie", method="GET").respond_with_data(
        "Internal Server Error",
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    client = Client(config)
    assert client.authenticate() is False
    assert client.signed_cookie == ""

def test_client_authenticate_signed_cookie_none(config: Config, httpserver: HTTPServer) -> None:
    config.enea_url = httpserver.url_for("")

    httpserver.expect_request("/logowanie", method="GET").respond_with_data(
        '<input type="hidden" name="token" value="token-123">',
        status=HTTPStatus.OK,
        headers={
            "Set-Cookie": "SESSION=unsigned; Path=/; HttpOnly",
            "Content-Type": "text/html",
        },
    )

    httpserver.expect_request("/logowanie", method="POST").respond_with_data(
        "Unauthorized",
        status=HTTPStatus.UNAUTHORIZED,
    )

    client = Client(config)
    assert client.authenticate() is False
    assert client.signed_cookie == ""

def test_client_authenticate_no_cookie(config: Config, httpserver: HTTPServer, caplog: LogCaptureFixture) -> None:
    config.enea_url = httpserver.url_for("")

    httpserver.expect_request("/logowanie", method="GET").respond_with_data(
        '<input type="hidden" name="token" value="token-123">',
        status=HTTPStatus.OK,
        headers={
            "Content-Type": "text/html",
        },
    )

    client = Client(config)

    with caplog.at_level(logging.ERROR):
        result = client.authenticate()

    assert result is False
    assert client.signed_cookie == ""
    assert "Error: No cookie" in caplog.text

def test_client_get_data_success(config: Config, httpserver: HTTPServer) -> None:
    data = (
        'Data;"Wolumen energii elektrycznej pobranej z\n'
        'sieci przed bilansowaniem godzinowym";'
        '"Wolumen energii elektrycznej oddanej\n'
        'do sieci przed bilansowaniem godzinowym";'
        '"Wolumen energii elektrycznej pobranej z\n'
        'sieci po bilansowaniu godzinowym";'
        '"Wolumen energii elektrycznej oddanej\n'
        'do sieci po bilansowaniu godzinowym"\n'
        '\u0000"=""2025-09-01 00:59"""\u0000;"0,507";"0";"0,507";"0"\n'
        '\u0000"=""2025-09-01 01:59"""\u0000;"0,503";"0";"0,503";"0"\n'
        '\u0000"=""2025-09-01 02:59"""\u0000;"0,561";"0";"0,561";"0"'
    )

    httpserver.expect_request(
        "/meter/summaryBalancingChart/csv",
        method="POST",
    ).respond_with_data(
        json.dumps(
            {
                "success": 1,
                "data": data,
            },
        ),
        status=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    client = Client(config)
    client.signed_cookie = "SESSION=signed; Path=/; HttpOnly"

    result = client.get_data(config.dates[0])
    assert result == data

def test_client_get_data_http_error(config: Config, httpserver: HTTPServer, caplog: LogCaptureFixture) -> None:
    config.enea_url = httpserver.url_for("")

    httpserver.expect_request(
        "/meter/summaryBalancingChart/csv",
        method="POST",
    ).respond_with_data(
        "Internal Server Error",
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    client = Client(config)
    client.signed_cookie = "SESSION=signed; Path=/; HttpOnly"

    with caplog.at_level(logging.ERROR):
        result = client.get_data(config.dates[0])

    assert result is None
    assert "Error: status - 500, reason - INTERNAL SERVER ERROR" in caplog.text


def test_client_get_data_success_not_success(config: Config, httpserver: HTTPServer, caplog: LogCaptureFixture) -> None:
    config.enea_url = httpserver.url_for("")

    error_response = '{"success":0,"error":"Authentication failed"}'

    httpserver.expect_request(
        "/meter/summaryBalancingChart/csv",
        method="POST",
    ).respond_with_data(
        error_response,
        status=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    client = Client(config)
    client.signed_cookie = "SESSION=signed; Path=/; HttpOnly"

    with caplog.at_level(logging.ERROR):
        result = client.get_data(config.dates[0])

    assert result is None
    assert "Error: message - {'success': 0, 'error': 'Authentication failed'}" in caplog.text
