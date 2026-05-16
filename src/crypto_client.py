import httpx
from typing import Dict, List


class CMClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    async def get_prices_batch(self, coin_ids: List[str]) -> Dict[str, float]:
        if not coin_ids:
            return {}

        ids_string = ",".join(coin_ids)

        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": ids_string,
            "vs_currencies": "usd"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                data = response.json()

                result = {}
                for coin, details in data.items():
                    result[coin] = details.get("usd")
                return result

            except Exception as e:
                print(f"Error fetching batch prices: {e}")
                return {}
