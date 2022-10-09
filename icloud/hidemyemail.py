import asyncio
import aiohttp


class HideMyEmail:
    base_url = 'https://p68-maildomainws.icloud.com/v1/hme'
    params = {
        "clientBuildNumber": "2206Hotfix11",
        "clientMasteringNumber": "2206Hotfix11",
        "clientId": "",
        "dsid": ""
    }

    def __init__(self, label: str = "rtuna's gen", cookies: str = ''):
        """Initializes the HideMyEmail class.

        Args:
            label (str)     Label that will be set for all emails generated, defaults to `rtuna's gen`
            cookies (str)   Cookie string to be used with requests. Required for authorization. 
        """
        # Label that will be set for all emails generated, defaults to `rtuna's gen`
        self.label = label

        # Cookie string to be used with requests. Required for authorization.
        self.cookies = cookies

    async def __aenter__(self):
        self.s = aiohttp.ClientSession(
            headers={
                'Connection': "keep-alive",
                'Pragma': "no-cache",
                'Cache-Control': "no-cache",
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36",
                'Content-Type': "text/plain",
                'Accept': "*/*",
                'Sec-GPC': "1",
                'Origin': "https://www.icloud.com",
                'Sec-Fetch-Site': "same-site",
                'Sec-Fetch-Mode': "cors",
                'Sec-Fetch-Dest': "empty",
                'Referer': "https://www.icloud.com/",
                'Accept-Language': "en-US,en-GB;q=0.9,en;q=0.8,cs;q=0.7",
                'Cookie': self.__cookies.strip()
            },
            timeout=aiohttp.ClientTimeout(total=10),
        )

        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self.s.close()

    @property
    def cookies(self) -> str:
        return self.__cookies

    @cookies.setter
    def cookies(self, cookies: str):
        # remove new lines/whitespace for security reasons
        self.__cookies = cookies.strip()

    async def generate_email(self) -> dict:
        """Generates an email"""
        try:
            async with self.s.post(f'{self.base_url}/generate', params=self.params) as resp:
                res = await resp.json()
                return res
        except asyncio.TimeoutError:
            return {'error': 1, 'reason': "Request timed out"}

    async def reserve_email(self, email: str) -> dict:
        """Reserves an email and registers it for forwarding"""
        try:
            payload = {"hme": email, "label": self.label,
                       "note": "由 rtuna 的 iCloud 匿名邮箱生成器生成"}
            async with self.s.post(f'{self.base_url}/reserve', params=self.params, json=payload) as resp:
                res = await resp.json()
            return res
        except asyncio.TimeoutError:
            return {'error': 1, 'reason': "Request timed out"}

    async def list_email(self) -> dict:
        """List all HME"""
        try:
            async with self.s.get(f'{self.base_url}/list', params=self.params) as resp:
                res = await resp.json()
                return res
        except asyncio.TimeoutError:
            return {'error': 1, 'reason': "Request timed out"}
