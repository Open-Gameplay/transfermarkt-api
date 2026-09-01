import json
from dataclasses import dataclass
import logging

from app.services.base import TransfermarktBase

logger = logging.getLogger(__name__)


@dataclass
class TransfermarktPlayerMarketValue(TransfermarktBase):
    """
    Retrieves market value history from the tmapi JSON endpoint.

    Uses https://tmapi.transfermarkt.technology/player/{id}/market-value-history
    instead of scraping the HTML page (which gets blocked after ~15-20 requests).

    Args:
        player_id (str): The unique identifier of the player.
    """

    player_id: str = None
    URL: str = "https://www.transfermarkt.com/-/marktwertverlauf/spieler/{player_id}"
    URL_TMAPI: str = "https://tmapi.transfermarkt.technology/player/{player_id}/market-value-history"

    def __post_init__(self) -> None:
        self.URL = self.URL.format(player_id=self.player_id)
        self.URL_TMAPI = self.URL_TMAPI.format(player_id=self.player_id)
        try:
            self.market_value_data = self.make_request(url=self.URL_TMAPI)
        except Exception as e:
            logger.error("Failed to fetch tmapi market value for player %s: %s", self.player_id, e)
            self.market_value_data = None

    def __parse_market_value_history(self) -> list:
        """Parse market value history from tmapi JSON."""
        if self.market_value_data is None:
            return []

        try:
            resp = json.loads(self.market_value_data.content)
            data = resp.get("data", {})
        except (json.JSONDecodeError, AttributeError, TypeError):
            return []

        history = data.get("history", [])
        result = []
        for entry in history:
            mv = entry.get("marketValue", {})
            result.append({
                "age": entry.get("age"),
                "date": mv.get("determined"),
                "clubId": str(entry.get("clubId", "")),
                "clubName": str(entry.get("clubId", "")),  # tmapi doesn't include club name, use ID
                "marketValue": mv.get("value"),
            })

        return result

    def get_player_market_value(self) -> dict:
        """
        Retrieve market value history from tmapi.

        Returns a dict with the same keys as the old HTML scraper for backward compatibility.
        """
        self.response["id"] = self.player_id

        if self.market_value_data is None:
            self.response["marketValue"] = None
            self.response["marketValueHistory"] = []
            self.response["ranking"] = {}
            return self.response

        try:
            resp = json.loads(self.market_value_data.content)
            data = resp.get("data", {})
        except (json.JSONDecodeError, AttributeError, TypeError):
            self.response["marketValue"] = None
            self.response["marketValueHistory"] = []
            self.response["ranking"] = {}
            return self.response

        # Current market value from the data
        current = data.get("current", {})
        self.response["marketValue"] = current.get("marketValue", {}).get("value")

        # Parse history
        self.response["marketValueHistory"] = self.__parse_market_value_history()

        # Ranking (not available in tmapi, return empty)
        self.response["ranking"] = {}

        return self.response
