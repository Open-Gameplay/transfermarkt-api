from typing import Optional

from app.schemas.base import AuditMixin, TransfermarktBaseModel


class NationalTeamPlayer(TransfermarktBaseModel):
    id: str
    name: str
    shirt_number: Optional[str] = None
    position: Optional[str] = None
    age: Optional[int] = None
    club: Optional[str] = None
    market_value: Optional[int] = None
    image_url: Optional[str] = None


class NationalTeamPlayers(TransfermarktBaseModel, AuditMixin):
    id: str
    season_id: Optional[str] = None
    players: list[NationalTeamPlayer]
