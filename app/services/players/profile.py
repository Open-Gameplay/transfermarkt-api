from dataclasses import dataclass
import json
import logging

from app.services.base import TransfermarktBase

logger = logging.getLogger(__name__)


@dataclass
class TransfermarktPlayerProfile(TransfermarktBase):
    """
    Retrieves player profile data from the tmapi JSON endpoint.

    Uses https://tmapi.transfermarkt.technology/player/{id} instead of
    scraping the HTML profile page (which gets blocked after ~15-20 requests).

    Args:
        player_id (str): The unique identifier of the player.
    """

    player_id: str = None
    URL: str = "https://www.transfermarkt.com/-/profil/spieler/{player_id}"
    URL_TMAPI: str = "https://tmapi.transfermarkt.technology/player/{player_id}"

    def __post_init__(self) -> None:
        self.URL = self.URL.format(player_id=self.player_id)
        self.URL_TMAPI = self.URL_TMAPI.format(player_id=self.player_id)
        try:
            self.profile_data = self.make_request(url=self.URL_TMAPI)
        except Exception as e:
            logger.error("Failed to fetch tmapi profile for player %s: %s", self.player_id, e)
            self.profile_data = None

    def _set_empty_defaults(self) -> None:
        """Set all required response fields to empty/default values."""
        self.response["url"] = f"https://www.transfermarkt.com/-/profil/spieler/{self.player_id}"
        self.response["name"] = ""
        self.response["description"] = ""
        self.response["fullName"] = ""
        self.response["nameInHomeCountry"] = ""
        self.response["imageUrl"] = None
        self.response["dateOfBirth"] = None
        self.response["placeOfBirth"] = {"city": "", "country": ""}
        self.response["age"] = None
        self.response["height"] = None
        self.response["citizenship"] = []
        self.response["isRetired"] = False
        self.response["retiredSince"] = None
        self.response["position"] = {"main": "", "other": []}
        self.response["foot"] = ""
        self.response["shirtNumber"] = ""
        self.response["club"] = {"id": None, "name": "", "joined": None, "contractExpires": None,
                                  "contractOption": None, "lastClubId": None, "lastClubName": None,
                                  "mostGamesFor": None}
        self.response["marketValue"] = None
        self.response["agent"] = {"name": "", "url": None}
        self.response["outfitter"] = ""
        self.response["socialMedia"] = []
        self.response["trainerProfile"] = {"id": None, "url": None, "position": None}
        self.response["relatives"] = []

    def get_player_profile(self) -> dict:
        """
        Retrieve player profile from tmapi JSON endpoint.

        Returns a dict with the same keys as the old HTML scraper for backward compatibility.
        """
        if self.profile_data is None:
            self.response["id"] = self.player_id
            self._set_empty_defaults()
            return self.response

        try:
            resp = json.loads(self.profile_data.content)
            data = resp.get("data", {})
        except (json.JSONDecodeError, AttributeError, TypeError):
            self.response["id"] = self.player_id
            self._set_empty_defaults()
            return self.response

        # Basic info
        self.response["id"] = data.get("id", self.player_id)
        rel_url = data.get("relativeUrl", "")
        self.response["url"] = f"https://www.transfermarkt.com{rel_url}" if rel_url.startswith("/") else (rel_url or f"https://www.transfermarkt.com/-/profil/spieler/{self.player_id}")
        self.response["name"] = data.get("name", "")
        self.response["description"] = ""
        self.response["fullName"] = data.get("name", "")
        self.response["nameInHomeCountry"] = data.get("nationalityDetails", {}).get("passportName", "")
        self.response["imageUrl"] = data.get("portraitUrl", "")

        # Life dates
        life = data.get("lifeDates", {})
        self.response["dateOfBirth"] = life.get("dateOfBirth")
        self.response["age"] = life.get("age")

        # Birth place
        birth = data.get("birthPlaceDetails", {})
        self.response["placeOfBirth"] = {
            "city": birth.get("placeOfBirth", ""),
            "country": None,  # countryOfBirthId is numeric, not name
        }

        # Nationality
        nat = data.get("nationalityDetails", {})
        nationalities = nat.get("nationalities", {})
        self.response["citizenship"] = []
        if nationalities.get("nationalityId"):
            self.response["citizenship"].append(str(nationalities["nationalityId"]))
        if nationalities.get("secondNationalityId"):
            self.response["citizenship"].append(str(nationalities["secondNationalityId"]))

        # Attributes
        attrs = data.get("attributes", {})
        self.response["height"] = attrs.get("height")
        self.response["isRetired"] = False
        self.response["retiredSince"] = None

        # Position
        pos = attrs.get("position", {})
        other_positions = []
        if attrs.get("firstSidePosition"):
            other_positions.append(attrs["firstSidePosition"].get("name", ""))
        if attrs.get("secondSidePosition"):
            other_positions.append(attrs["secondSidePosition"].get("name", ""))
        self.response["position"] = {
            "main": pos.get("name", ""),
            "other": other_positions,
        }

        # Foot
        foot = attrs.get("preferredFoot", {})
        self.response["foot"] = foot.get("name", "")

        # Outfitter
        outfitter = attrs.get("outfitter", {})
        self.response["outfitter"] = outfitter.get("name", "")

        # Shirt number (not in tmapi, set empty)
        self.response["shirtNumber"] = ""

        # Club info (not in tmapi profile, set empty)
        self.response["club"] = {
            "id": None,
            "name": "",
            "joined": None,
            "contractExpires": attrs.get("contractUntil"),
            "contractOption": None,
            "lastClubId": None,
            "lastClubName": None,
            "mostGamesFor": None,
        }

        # Market value
        mv = data.get("marketValueDetails", {})
        current_mv = mv.get("current", {})
        self.response["marketValue"] = current_mv.get("value")

        # Agent
        agent = attrs.get("consultantAgency", {})
        self.response["agent"] = {
            "name": agent.get("name", ""),
            "url": None,
        }

        # Social media (not in tmapi)
        self.response["socialMedia"] = []

        # Relatives (not in tmapi)
        self.response["relatives"] = []

        # Trainer profile (not in tmapi)
        self.response["trainerProfile"] = {"id": None, "url": None, "position": None}

        return self.response
