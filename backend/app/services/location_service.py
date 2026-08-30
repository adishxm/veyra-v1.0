import re
import httpx
from typing import Optional, Tuple, Dict

# Regional dictionary for prominent sub-regions, administrative states, and common aliases
REGIONAL_ALIASES: Dict[str, Tuple[float, float]] = {
    # States & Territories (Centroid / Capital)
    "meghalaya": (25.5788, 91.8933),       # Shillong / Meghalaya
    "assam": (26.1445, 91.7362),           # Guwahati / Assam
    "sikkim": (27.3389, 88.6065),          # Gangtok / Sikkim
    "west bengal": (22.9868, 87.8550),
    "odisha": (20.2961, 85.8245),
    "bihar": (25.5941, 85.1376),
    "karnataka": (12.9716, 77.5946),
    "maharashtra": (19.0760, 72.8777),
    "ladakh": (34.1526, 77.5771),

    # Urban Sub-Localities & Neighborhoods
    "saltlake": (22.5800, 88.4200),
    "salt lake": (22.5800, 88.4200),
    "salt lake city": (22.5800, 88.4200),
    "bidhannagar": (22.5800, 88.4200),
    "new town": (22.5867, 88.4754),
    "howrah": (22.5958, 88.2636),
    "ballygunge": (22.5280, 88.3656),
    "alipore": (22.5300, 88.3300),
    "dum dum": (22.6420, 88.4312),
}

class LocationService:
    """Robust multi-tier geocoding resolver with syntax sanitation and alias fallbacks."""

    @classmethod
    def _parse_raw_coords(cls, query: str) -> Optional[Tuple[float, float]]:
        """Parses raw numerical coordinate strings like '22.5726, 88.3639'."""
        coord_pattern = r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$"
        if re.match(coord_pattern, query.strip()):
            parts = query.strip().split(",")
            return float(parts[0].strip()), float(parts[1].strip())
        return None

    @classmethod
    async def resolve_location(cls, query: str) -> Optional[Tuple[float, float, str]]:
        if not query or not query.strip():
            return None

        clean_query = query.strip().lower()

        # 1. Check raw coordinates
        raw_coords = cls._parse_raw_coords(clean_query)
        if raw_coords:
            return raw_coords[0], raw_coords[1], f"Coords ({raw_coords[0]:.4f}, {raw_coords[1]:.4f})"

        # 2. Check local alias lookup table (direct match)
        if clean_query in REGIONAL_ALIASES:
            lat, lon = REGIONAL_ALIASES[clean_query]
            return lat, lon, query.strip().title()

        # 3. Tokenize queries with commas (e.g., "saltlake, kolkata" -> ["saltlake", "kolkata"])
        tokens = [t.strip() for t in re.split(r"[,/]+", clean_query) if t.strip()]

        for token in tokens:
            if token in REGIONAL_ALIASES:
                lat, lon = REGIONAL_ALIASES[token]
                return lat, lon, f"{token.title()} ({query.strip().title()})"

        # 4. Search via Open-Meteo Geocoding API with multi-token strategy
        search_candidates = [
            clean_query.replace(",", " "),      # "saltlake kolkata"
            tokens[0] if tokens else clean_query # primary token "saltlake"
        ]

        async with httpx.AsyncClient(timeout=6.0) as client:
            for candidate in search_candidates:
                try:
                    url = f"https://geocoding-api.open-meteo.com/v1/search?name={candidate}&count=5&language=en&format=json"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        if results:
                            best = results[0]
                            return (
                                float(best["latitude"]),
                                float(best["longitude"]),
                                f"{best.get('name', query.title())}, {best.get('country', '')}".strip(", ")
                            )
                except Exception:
                    continue

        return None