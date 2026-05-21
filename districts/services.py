import logging
import math
from dataclasses import dataclass

from django.db.models import Prefetch
from shapely.geometry import Point, Polygon

from districts.models import District, DistrictBoundary

logger = logging.getLogger(__name__)


@dataclass
class DistrictMatch:
    district: District
    distance_km: float
    is_inside_boundary: bool
    match_method: str  # "inside_polygon" | "nearest_center"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Ikki nuqta orasidagi masofa (km)."""
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_polygon(district: District) -> Polygon | None:
    points = list(
        district.boundary_points.order_by("order").values_list("longitude", "latitude")
    )
    if len(points) < 3:
        return None
    try:
        return Polygon(points)
    except Exception as exc:
        logger.warning("Invalid polygon for district %s: %s", district.code, exc)
        return None


def find_district_for_location(latitude: float, longitude: float) -> DistrictMatch | None:
    """
    SOS nuqtasi uchun eng mos tumanni topadi:
    1. Avval polygon ichida ekanligini tekshiradi
    2. Topilmasa, markazga eng yaqin tumanni tanlaydi
    """
    point = Point(longitude, latitude)

    districts = District.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "boundary_points",
            queryset=DistrictBoundary.objects.order_by("order"),
        )
    )

    inside_matches: list[DistrictMatch] = []
    nearest: DistrictMatch | None = None

    for district in districts:
        polygon = _build_polygon(district)
        center_lat, center_lon = district.center_coords
        distance = haversine_km(latitude, longitude, center_lat, center_lon)

        if polygon and polygon.contains(point):
            inside_matches.append(
                DistrictMatch(
                    district=district,
                    distance_km=round(distance, 3),
                    is_inside_boundary=True,
                    match_method="inside_polygon",
                )
            )
            continue

        candidate = DistrictMatch(
            district=district,
            distance_km=round(distance, 3),
            is_inside_boundary=False,
            match_method="nearest_center",
        )
        if nearest is None or candidate.distance_km < nearest.distance_km:
            nearest = candidate

    if inside_matches:
        return min(inside_matches, key=lambda m: m.distance_km)

    return nearest
