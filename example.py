import asyncio
from pprint import pprint

import aiohttp

from pyairthings.api import API

email = "csacca@csacca.net"
password = "34FWfyam"


async def main():
    async with aiohttp.ClientSession() as session:
        api = API(email, password, session=session)
        await api.login()
        me: dict = await api.me.get()
        pprint(me)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
