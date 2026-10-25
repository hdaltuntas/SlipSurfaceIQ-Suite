"""Per-program workspace organization; calculation engines remain unchanged."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from slipsurface.apps import keys


@dataclass(frozen=True)
class WorkspaceProfile:
    module: str
    primary_tab: str
    hint_tr: str
    hint_en: str


PROFILES = {
    "kinematic": WorkspaceProfile("kinematic", "Kinematik Tarama",
        "Şev yönelimini, süreksizlik takımlarını ve göçme türünü tanımlayın.",
        "Define slope orientation, discontinuities and failure mode."),
    "rock": WorkspaceProfile("rock", "Sağlam Kaya",
        "Sağlam kaya deney verilerini girin; ardından kaya kütlesi parametrelerini değerlendirin.",
        "Enter intact-rock test data, then evaluate rock-mass parameters."),
    "bearing": WorkspaceProfile("bearing", "Temel",
        "Temel geometrisini ve yükleri belirleyin; zemin tabakalarını ayrıca kontrol edin.",
        "Set foundation geometry and actions; review the soil profile as well."),
    "settle": WorkspaceProfile("settle", "Temel",
        "Temel geometrisini ve yükleri girin; konsolidasyon parametrelerini doğrulayın.",
        "Enter foundation dimensions and loading, then check consolidation inputs."),
    "correlation": WorkspaceProfile("correlation", "Deneyler",
        "SPT, CPT veya deney verilerini tablolara girerek tasarım parametrelerini oluşturun.",
        "Use SPT, CPT or laboratory tables to derive design parameters."),
    "liquefaction": WorkspaceProfile("liquefaction", "Saha Verileri",
        "Deprem hareketi, yeraltı suyu ve SPT/CPT ölçümlerini birlikte değerlendirin.",
        "Review earthquake demand, groundwater and SPT/CPT observations."),
    "pile": WorkspaceProfile("pile", "Kazık",
        "Kazık geometrisi, zemin direnci ve varsa kaya soketini birlikte tanımlayın.",
        "Define pile geometry, shaft resistance and any rock socket."),
    "spwa": WorkspaceProfile("spwa", "Yapısal Sistem",
        "Kazı geometrisini, perde kesitini ve ankrajları kontrol edin.",
        "Check excavation geometry, retaining system and anchors."),
    "msew": WorkspaceProfile("msew", "Duvar",
        "Donatılı dolgu, katman geometrisi ve donatı yerleşimini oluşturun.",
        "Define reinforced fill, geometry and reinforcement arrangement."),
    "wall": WorkspaceProfile("wall", "Duvar",
        "İstinat duvarının boyutlarını ve stabilite girdilerini kontrol edin.",
        "Review retaining-wall dimensions and stability inputs."),
}


def profile(key: str) -> WorkspaceProfile:
    return PROFILES[key]


assert set(PROFILES) == set(keys()), "Every active module needs a workspace profile"
