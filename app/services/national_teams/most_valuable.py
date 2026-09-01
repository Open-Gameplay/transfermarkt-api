from dataclasses import dataclass

from app.services.base import TransfermarktBase
from app.utils.utils import extract_from_url
from app.utils.xpath import NationalTeams


@dataclass
class TransfermarktMostValuableNationalTeams(TransfermarktBase):
    """
    A class for scraping most valuable national teams from Transfermarkt.
    """

    URL: str = "https://www.transfermarkt.com/vereins-statistik/wertvollstenationalmannschaften/marktwertetop?page={page_number}"

    def __get_page(self, page_number: int):
        self.URL = self.URL.rsplit("=", 1)[0] + f"={page_number}"
        self.page = self.request_url_page()
        return self.page

    def __parse_results(self) -> list:
        urls = self.get_list_by_xpath(NationalTeams.MostValuable.URLS)
        names = self.get_list_by_xpath(NationalTeams.MostValuable.NAMES)
        countries = self.get_list_by_xpath(NationalTeams.MostValuable.COUNTRIES)
        confederations = self.get_list_by_xpath(NationalTeams.MostValuable.CONFEDERATIONS)
        market_values = self.get_list_by_xpath(NationalTeams.MostValuable.MARKET_VALUES)
        ids = [extract_from_url(url) for url in urls]

        return [
            {
                "id": idx,
                "url": url,
                "name": name,
                "country": country,
                "confederation": confederation,
                "marketValue": market_value,
            }
            for idx, url, name, country, confederation, market_value in zip(
                ids,
                urls,
                names,
                countries,
                confederations,
                market_values,
            )
        ]

    def get_most_valuable_national_teams(self) -> dict:
        self.__get_page(1)
        last_page_number = self.get_last_page_number()

        all_results = []

        for page_num in range(1, last_page_number + 1):
            self.__get_page(page_num)
            page_results = self.__parse_results()
            all_results.extend(page_results)

        return {
            "results": all_results
        }