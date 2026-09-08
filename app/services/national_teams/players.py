from dataclasses import dataclass

from app.services.base import TransfermarktBase
from app.utils.regex import REGEX_DOB
from app.utils.utils import extract_from_url, safe_regex
from app.utils.xpath import NationalTeams


@dataclass
class TransfermarktNationalTeamPlayers(TransfermarktBase):
    """
    A class for retrieving and parsing national team players from Transfermarkt.

    Args:
        team_id (str): The unique identifier of the national team.
        season_id (str): The season identifier. If not provided, the current season is used.
    """

    team_id: str = None
    season_id: str = None
    URL: str = "https://www.transfermarkt.com/-/kader/verein/{team_id}/saison_id/{season_id}/plus/1"

    def __post_init__(self) -> None:
        self.URL = self.URL.format(team_id=self.team_id, season_id=self.season_id or "")
        self.page = self.request_url_page()
        self.raise_exception_if_not_found(xpath=NationalTeams.Players.TEAM_NAME)
        self.__update_season_id()

    def __update_season_id(self) -> None:
        if self.season_id is None:
            self.season_id = extract_from_url(self.get_text_by_xpath(NationalTeams.Players.TEAM_URL), "season_id")

    def __parse_players(self) -> list:
        rows = self.page.xpath(NationalTeams.Players.ROWS)
        players = []

        for row in rows:
            player_url = row.xpath(NationalTeams.Players.PLAYER_URL)
            player_name = row.xpath(NationalTeams.Players.PLAYER_NAME)
            shirt_number = row.xpath(NationalTeams.Players.SHIRT_NUMBER)
            position = row.xpath(NationalTeams.Players.POSITION)
            fine_position = row.xpath(NationalTeams.Players.FINE_POSITION)
            # precise position lives in the row's inline-table; the jersey-number
            # title (coarse "Defender"/"Midfield"/"Attack") is only a fallback
            precise_position = (fine_position[-1].strip() if fine_position
                                else (position[-1].strip() if position else None))
            dob_age = row.xpath(NationalTeams.Players.DOB_AGE)
            club_name = row.xpath(NationalTeams.Players.CLUB_NAME)
            height_raw = row.xpath(NationalTeams.Players.HEIGHT)
            foot = row.xpath(NationalTeams.Players.FOOT)
            market_value = row.xpath(NationalTeams.Players.MARKET_VALUE)
            photo = row.xpath(NationalTeams.Players.PHOTO)

            player_url = player_url[0].strip() if player_url else None
            image_url = photo[0].strip().split("?")[0] if photo else None

            dob_text = dob_age[0].strip() if dob_age else None
            dob, age = (None, None)
            if dob_text:
                dob, age = safe_regex(dob_text, REGEX_DOB, "dob"), safe_regex(dob_text, REGEX_DOB, "age")

            height = None
            if height_raw:
                h = height_raw[0].strip().replace(",", ".").replace("m", "")
                try:
                    height = int(float(h) * 100)
                except (ValueError, TypeError):
                    height = None

            players.append(
                {
                    "id": extract_from_url(player_url) if player_url else None,
                    "name": player_name[0].strip() if player_name else None,
                    "shirtNumber": shirt_number[0].strip() if shirt_number else None,
                    "position": precise_position,
                    "dateOfBirth": dob,
                    "age": age,
                    "club": club_name[0].strip() if club_name else None,
                    "height": height,
                    "foot": foot[0].strip() if foot else None,
                    "marketValue": market_value[0].strip() if market_value else None,
                    "imageUrl": image_url,
                }
            )

        return [player for player in players if player.get("id") and player.get("name")]

    def get_national_team_players(self) -> dict:
        self.response["id"] = self.team_id
        self.response["seasonId"] = self.season_id
        self.response["players"] = self.__parse_players()

        return self.response
