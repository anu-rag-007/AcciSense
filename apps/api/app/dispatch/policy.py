from dataclasses import dataclass

@dataclass(frozen=True)
class WaveSpec:
    wave: int
    radius_m: int
    timeout_s: int
    required_caps: tuple[str, ...]

DISPATCH_POLICY: dict[str, list[WaveSpec]] = {
    "CRITICAL": [
        WaveSpec(1,  3_000,  20, ("ALS",)),
        WaveSpec(2,  8_000,  30, ("ALS", "BLS", "trauma")),
        WaveSpec(3, 15_000,  60, ("ALS", "BLS", "bike_first_responder")),
    ],
    "HIGH": [
        WaveSpec(1,  5_000,  45, ("ALS", "BLS")),
        WaveSpec(2, 12_000,  60, ("ALS", "BLS", "bike_first_responder")),
    ],
    "MEDIUM": [
        WaveSpec(1,  8_000,  90, ("BLS", "bike_first_responder")),
        WaveSpec(2, 20_000, 120, ("BLS", "bike_first_responder")),
    ],
    "LOW": [
        WaveSpec(1, 10_000, 180, ("bike_first_responder", "BLS")),
    ],
}

CATEGORY_REQUIRED_CAPS: dict[str, tuple[str, ...]] = {
    "cardiac": ("ALS",),
    "stroke":  ("ALS",),
    "trauma":  ("ALS", "trauma"),
    "fire":    ("fire_engine",),
    "assault": ("police_unit",),
}