"""Registry of installed geotechnical modules; LE is deliberately excluded."""
from dataclasses import dataclass


@dataclass(frozen=True)
class App:
    key: str
    name: str
    tr: str
    group: str
    description: str


APPS = (
    App("kinematic", "Kinematic", "Kaya Şevi Kinematiği", "Rock", "Stereonet, planar, wedge and toppling"),
    App("rock", "Rock", "Kaya Kütlesi", "Rock", "Generalized Hoek–Brown strength and modulus"),
    App("bearing", "Bearing", "Temel Taşıma Gücü", "Foundations", "Shallow foundation bearing capacity"),
    App("settle", "Settle", "Oturma", "Foundations", "Immediate and consolidation settlement"),
    App("correlation", "Correlation", "Zemin Korelasyonları", "Foundations", "SPT, CPT and laboratory correlations"),
    App("liquefaction", "Liquefaction", "Sıvılaşma", "Foundations", "SPT/CPT liquefaction triggering"),
    App("pile", "Pile", "Kazık", "Foundations", "Axial capacity, group and socket assessment"),
    App("spwa", "Pile Wall Analysis", "Palplanş ve Kazık Perde", "Retaining", "Earth support and beam–spring analysis"),
    App("msew", "MSEW", "Donatılı Zemin Duvarı", "Retaining", "Mechanically stabilized earth walls"),
    App("wall", "Wall", "İstinat Duvarı", "Retaining", "Reinforced concrete retaining walls"),
)

_BY_KEY = {app.key: app for app in APPS}


def keys() -> list[str]:
    return list(_BY_KEY)


def get(key: str) -> App:
    return _BY_KEY[key]


def catalogue() -> tuple[App, ...]:
    return APPS
