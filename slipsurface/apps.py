"""Registry of installed geotechnical modules; LE is deliberately excluded."""
from dataclasses import dataclass


@dataclass(frozen=True)
class App:
    key: str
    name: str
    tr: str
    group: str
    description: str
    description_tr: str = ""


APPS = (
    App("kinematic", "Kinematic", "Kaya Şevi Kinematiği", "Rock", "Stereonet, planar, wedge and toppling", "Stereonet ile düzlemsel, kama ve devrilme analizleri."),
    App("rock", "Rock", "Kaya Kütlesi", "Rock", "Generalized Hoek–Brown strength and modulus", "Hoek–Brown dayanımı ve kaya kütlesi deformasyon modülü."),
    App("bearing", "Bearing", "Temel Taşıma Gücü", "Foundations", "Shallow foundation bearing capacity", "Sığ temeller için taşıma gücü ve güvenlik kontrolleri."),
    App("settle", "Settle", "Oturma", "Foundations", "Immediate and consolidation settlement", "Ani oturma, konsolidasyon ve zamana bağlı oturma."),
    App("correlation", "Correlation", "Zemin Korelasyonları", "Foundations", "SPT, CPT and laboratory correlations", "SPT, CPT ve laboratuvar deneylerinden zemin parametreleri."),
    App("liquefaction", "Liquefaction", "Sıvılaşma", "Foundations", "SPT/CPT liquefaction triggering", "SPT/CPT verileriyle sıvılaşma ve oturma değerlendirmesi."),
    App("pile", "Pile", "Kazık", "Foundations", "Axial capacity, group and socket assessment", "Kazıkların eksenel kapasitesi, grup etkisi ve soket analizi."),
    App("spwa", "Pile Wall Analysis", "Palplanş ve Kazık Perde", "Retaining", "Earth support and beam–spring analysis", "Palplanş ve fore kazık perdelerde ankrajlı kazı analizi."),
    App("msew", "MSEW", "Donatılı Zemin Duvarı", "Retaining", "Mechanically stabilized earth walls", "Donatılı zemin duvarlarında iç ve dış stabilite."),
    App("wall", "Wall", "İstinat Duvarı", "Retaining", "Reinforced concrete retaining walls", "Betonarme istinat duvarlarında stabilite ve tasarım."),
)

_BY_KEY = {app.key: app for app in APPS}


def keys() -> list[str]:
    return list(_BY_KEY)


def get(key: str) -> App:
    return _BY_KEY[key]


def catalogue() -> tuple[App, ...]:
    return APPS
