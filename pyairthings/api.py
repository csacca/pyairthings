import logging
from datetime import datetime
from pprint import pprint
from typing import Optional
from urllib.parse import urlparse

import jwt
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError
from aiohttp.hdrs import (
    ACCEPT,
    ACCEPT_ENCODING,
    ACCEPT_LANGUAGE,
    AUTHORIZATION,
    CONTENT_TYPE,
    HOST,
    METH_POST,
    USER_AGENT,
)
from multidict import istr

from .const import API_V1_BASE
from .errors import RequestError
from .me import Me

_LOGGER = logging.getLogger(__name__)


X_API_KEY = istr("x-api-key")

DEFAULT_HEADERS = {
    ACCEPT: "*/*",
    ACCEPT_ENCODING: "gzip;q=1.0, compress;q=0.5",
    ACCEPT_LANGUAGE: "en-US;q=1.0, ja-JP;q=0.9",
    CONTENT_TYPE: "application/json",
    USER_AGENT: "airthings-ios/3.1.2 334",
    X_API_KEY: "MfssuMLy3otowbaoCbDp2bfjSJjnWH29C8W96lZ9",
}

DEFAULT_TIMEOUT: int = 10


class API:
    """Define pyairthings API object"""

    def __init__(
        self, email: str, password: str, *, session: Optional[ClientSession] = None
    ) -> None:
        """Initialize"""
        self._email: str = email
        self._password: str = password
        self._session: ClientSession = session
        self._access_token: Optional[str] = None
        self._access_token_expiration: Optional[datetime] = None
        self._refresh_token: Optional[str] = None
        self._refresh_token_expiration: Optional[datetime] = None
        self._id_token: Optional[str] = None

        self.me: Me = Me(self._request)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict = None,
        params: dict = None,
        json: dict = None,
    ) -> dict:
        """Make a request against the API"""
        if self._access_token_expiration and datetime.now() >= self._access_token_expiration:
            _LOGGER.info("Token expired, requesting refresh...")

            # Nullify the token so that the authentication request doesn't use it:
            self._access_token = None

            # Nullify the expiration so the authentication request doesn't get caught
            # here:
            self._access_token_expiration = None

            await self.refresh_token()

        _headers = headers or {}
        _headers.update(DEFAULT_HEADERS)
        _headers[HOST] = urlparse(url).netloc

        if self._access_token:
            _headers[AUTHORIZATION] = self._access_token

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        try:
            async with session.request(
                method, url, headers=_headers, params=params, json=json
            ) as resp:
                data: dict = await resp.json(content_type=None)
                #
                pprint(data)
                #
                resp.raise_for_status()
                return data
        except ClientError as err:
            raise RequestError(f"There was an error while requesting {url}: {err}")
        finally:
            if not use_running_session:
                await session.close()

    def _parse_auth_response(self, response: dict) -> None:
        self._id_token = response["idToken"]
        self._access_token = response["accessToken"]
        self._access_token_expiration = datetime.fromtimestamp(
            datetime.now().timestamp() + response["expiresIn"]
        )
        self._refresh_token = response["refreshToken"]
        refresh_token_decode = jwt.decode(self._refresh_token, verify=False)
        self._refresh_token_expiration = datetime.fromtimestamp(
            datetime.now().timestamp() + refresh_token_decode["exp"] - refresh_token_decode["iat"]
        )

    async def login(self):
        """Login to account server"""
        login_response: dict = await self._request(
            METH_POST,
            f"{API_V1_BASE}/login",
            json={"email": self._email, "password": self._password},
        )
        self._parse_auth_response(login_response)

    async def refresh_token(self):
        """Refresh authentication token"""
        if not self._refresh_token:
            # raise no refresh token - need to login
            pass
        if self._refresh_token_expiration and datetime.now() >= self._refresh_token_expiration:
            _LOGGER.info("Refresh token expired, doing login...")
            self._refresh_token = None
            self._refresh_token_expiration = None
            return await self.login()

        refresh_response: dict = await self._request(
            METH_POST, f"{API_V1_BASE}/refresh", json={"refreshToken": self._refresh_token}
        )
        self._parse_auth_response(refresh_response)
