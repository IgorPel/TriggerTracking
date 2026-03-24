import httpx
from typing import Dict, List


class CMClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    async def get_prices_batch(self, coin_ids: List[str]) -> Dict[str, float]:
        """
        Розумний метод: приймає список ['bitcoin', 'ethereum', 'solana']
        Робить ОДИН запит до API.
        Повертає словник: {'bitcoin': 95000.0, 'ethereum': 2500.0, ...}
        """
        if not coin_ids:
            return {}

        # CoinGecko вимагає список через кому: "bitcoin,ethereum,solana"
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

                # Перетворюємо відповідь у зручний формат {id: price}
                result = {}
                for coin, details in data.items():
                    result[coin] = details.get("usd")
                return result

            except Exception as e:
                print(f"Error fetching batch prices: {e}")
                return {}