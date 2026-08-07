from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class SearchQuery:
    area: str
    check_in: date
    check_out: date
    adults: int = 2
    rooms: int = 1
    min_stars: float = 4.0


@dataclass
class ProviderPrice:
    provider: str
    price_inr: int
    currency: str = "INR"
    url: str | None = None
    freebies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HotelOffer:
    hotel: str
    area: str
    check_in: date
    stars: float
    lowest_price_inr: int
    lowest_provider: str
    providers: list[ProviderPrice] = field(default_factory=list)
    source: str = "kayak"
    rating: float | None = None
    review_count: int | None = None
    hotel_id: str | None = None
    details_url: str | None = None
    neighborhood: str | None = None

    @property
    def day(self) -> str:
        return self.check_in.strftime("%A")

    def to_dict(self) -> dict[str, Any]:
        return {
            "hotel": self.hotel,
            "area": self.area,
            "date": self.check_in.isoformat(),
            "day": self.day,
            "stars": self.stars,
            "lowest_price_inr": self.lowest_price_inr,
            "lowest_provider": self.lowest_provider,
            "providers": [p.to_dict() for p in self.providers],
            "provider_count": len(self.providers),
            "source": self.source,
            "rating": self.rating,
            "review_count": self.review_count,
            "hotel_id": self.hotel_id,
            "details_url": self.details_url,
            "neighborhood": self.neighborhood,
        }
