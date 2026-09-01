from dataclasses import dataclass
import json
import logging

from app.services.base import TransfermarktBase

logger = logging.getLogger(__name__)


@dataclass
class TransfermarktPlayerStats(TransfermarktBase):
    """
    A class for retrieving and parsing the player's stats from Transfermarkt.

    Uses the ceapi/performance-game endpoint which returns detailed per-game
    statistics. The old HTML scraping approach broke when TM moved stats to
    client-side rendered web components.

    Args:
        player_id (str): The unique identifier of the player.
    """

    player_id: str = None
    URL: str = "https://www.transfermarkt.com/-/leistungsdatendetails/spieler/{player_id}"
    URL_PERFORMANCE: str = "https://www.transfermarkt.com/ceapi/performance-game/{player_id}"

    def __post_init__(self) -> None:
        self.URL = self.URL.format(player_id=self.player_id)
        self.URL_PERFORMANCE = self.URL_PERFORMANCE.format(player_id=self.player_id)
        try:
            self.performance_data = self.make_request(url=self.URL_PERFORMANCE)
        except Exception as e:
            logger.error("Failed to fetch performance data for player %s: %s", self.player_id, e)
            self.performance_data = None

    def __parse_player_stats(self) -> list:
        """
        Parse and aggregate player statistics by competition and season.

        Returns:
            list: A list of dictionaries with aggregated stats per competition/season.
        """
        if self.performance_data is None:
            return []

        try:
            resp = json.loads(self.performance_data.content)
            data = resp.get("data", {})
        except (json.JSONDecodeError, AttributeError, TypeError):
            return []

        performances = data.get("performance", [])

        # Aggregate by (competition_id, season_id)
        agg: dict[tuple, dict] = {}

        for game in performances:
            gi = game.get("gameInformation", {})
            stats = game.get("statistics", {})

            comp_id = gi.get("competitionId", "unknown")
            season_id = gi.get("seasonId", 0)
            key = (comp_id, str(season_id))

            if key not in agg:
                agg[key] = {
                    "competition_id": comp_id,
                    "competition_name": comp_id,
                    "season_id": str(season_id),
                    "club_id": None,
                    "appearances": 0,
                    "goals": 0,
                    "assists": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "minutes_played": 0,
                }

            gs = stats.get("generalStatistics", {})
            goal_stats = stats.get("goalStatistics", {})
            card_stats = stats.get("cardStatistics", {})
            play_stats = stats.get("playingTimeStatistics", {})
            club_info = game.get("clubsInformation", {}).get("club", {})

            # Only count if the player actually played
            participation = gs.get("participationState", "")
            if participation == "played":
                agg[key]["appearances"] += 1

            # Use club from clubInformation (player's club, not opponent)
            club_id = club_info.get("clubId")
            if club_id and agg[key]["club_id"] is None:
                agg[key]["club_id"] = str(club_id)

            agg[key]["goals"] += goal_stats.get("goalsScoredTotalOfficial", 0) or 0
            agg[key]["assists"] += goal_stats.get("assistsOfficial", 0) or 0

            yellow = card_stats.get("yellowCardNet", 0) or 0
            agg[key]["yellow_cards"] += yellow

            # TM counts a red card as 2 yellow cards in net
            if yellow >= 2:
                agg[key]["red_cards"] += 1

            agg[key]["minutes_played"] += play_stats.get("playedMinutes", 0) or 0

        # Sort by season desc, then competition
        result = sorted(agg.values(), key=lambda x: (-int(x["season_id"]), x["competition_id"]))

        return result

    def get_player_stats(self) -> dict:
        """
        Retrieve and parse player statistics data for the specified player from Transfermarkt.

        Returns:
            dict: A dictionary containing the player's unique identifier and parsed player statistics.
        """
        self.response["id"] = self.player_id
        self.response["stats"] = self.__parse_player_stats()
        return self.response
