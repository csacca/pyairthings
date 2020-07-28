"""Define /me endpoint"""
from datetime import datetime
from typing import Awaitable, Callable, Optional

from aiohttp.hdrs import METH_GET, METH_POST

from .const import API_V1_BASE


class Me:
    """Define object to handle /me endpoint"""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get(self, include_hubs: Optional[bool] = True):
        params = {}
        if include_hubs is True:
            params["includeHubs"] = "true"
        elif include_hubs is False:
            params["includeHubs"] = "false"

        return await self._request(METH_GET, f"{API_V1_BASE}/me", params=params)

    async def set_push_notification_token(self, platform: str, token: str):
        """
        platform: str = APNS
        token: str = <64-digit hex string>
        """
        return await self._request(
            METH_POST,
            f"{API_V1_BASE}/me/push-notification-token",
            json={"platform": platform, "token": token},
        )

    async def get_devices_serialnumbers(self, include_hubs: Optional[bool] = True):
        params = {}
        if include_hubs is True:
            params["includeHubs"] = "true"
        elif include_hubs is False:
            params["includeHubs"] = "false"

        return await self._request(METH_GET, f"{API_V1_BASE}/devices/serialnumbers", params=params)

    async def get_device_latest_samples(
        self,
        serial_number: str,
        from_date: datetime,
        to_date: datetime,
        include_ids: Optional[bool] = True,
    ):
        params = {}
        params["from"] = from_date.isoformat()
        params["to"] = to_date.isoformat()
        if include_ids is True:
            params["includeHubs"] = "true"
        elif include_ids is False:
            params["includeHubs"] = "false"

        return await self._request(
            METH_GET,
            f"{API_V1_BASE}/devices/{serial_number}/segments/latest/samples",
            params=params,
        )
