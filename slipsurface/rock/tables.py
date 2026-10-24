"""
The tables an engineer picks typical values from — RocLab's "pickers".

    ROCK_TYPES        mi of the intact rock (Marinos & Hoek 2000, Hoek 2007)
                      and the modulus ratio MR = Ei/σci (Deere 1968, Palmström
                      & Singh 2001, as tabulated by Hoek & Diederichs 2006)
    STRENGTH_GRADES   field estimates of σci, ISRM grades R0–R6 (Hoek 2007)
    DISTURBANCE       guidelines for the disturbance factor D (Hoek,
                      Carranza-Torres & Corkum 2002)
    STRUCTURES,
    SURFACES          the classes of the GSI chart, placed on the quantified
                      chart of Hoek, Carter & Diederichs (2013)

Each entry carries its own English and Turkish name, so the tables are read
in one place and written into the interface, the report and the figures from
there. The values are typical, not design values: they are where an
estimate starts when no test says otherwise.
"""

from __future__ import annotations

from typing import Dict, List, Optional

__all__ = ["ROCK_TYPES", "ROCK_CLASSES", "STRENGTH_GRADES", "DISTURBANCE",
           "STRUCTURES", "SURFACES", "rock_type", "strength_grade", "disturbance",
           "name", "chart_gsi", "picker_options"]

#: Rock classes, in the order the rock types are listed
ROCK_CLASSES = ["sedimentary", "metamorphic", "igneous"]

#: key -> class, mi, ± spread of mi, MR low, MR high, English, Turkish
ROCK_TYPES: Dict[str, dict] = {}
for _key, _cls, _mi, _pm, _mr_lo, _mr_hi, _en, _tr in [
    # sedimentary — clastic
    ("conglomerate", "sedimentary", 21, 3, 300, 400, "Conglomerate", "Konglomera"),
    ("breccia_sed", "sedimentary", 19, 5, 230, 350, "Breccia (sedimentary)", "Breş (tortul)"),
    ("sandstone", "sedimentary", 17, 4, 200, 350, "Sandstone", "Kumtaşı"),
    ("siltstone", "sedimentary", 7, 2, 350, 400, "Siltstone", "Silttaşı"),
    ("greywacke", "sedimentary", 18, 3, 350, 350, "Greywacke", "Grovak"),
    ("claystone", "sedimentary", 4, 2, 200, 300, "Claystone", "Kiltaşı"),
    ("shale", "sedimentary", 6, 2, 150, 250, "Shale", "Şeyl"),
    ("marl", "sedimentary", 7, 2, 150, 200, "Marl", "Marn"),
    # sedimentary — carbonates, evaporites, organic
    ("crystalline_limestone", "sedimentary", 12, 3, 400, 600, "Crystalline limestone",
     "Kristalen kireçtaşı"),
    ("sparitic_limestone", "sedimentary", 10, 2, 600, 800, "Sparitic limestone",
     "Sparitik kireçtaşı"),
    ("micritic_limestone", "sedimentary", 9, 2, 800, 1000, "Micritic limestone",
     "Mikritik kireçtaşı"),
    ("dolomite", "sedimentary", 9, 3, 350, 500, "Dolomite", "Dolomit"),
    ("gypsum", "sedimentary", 8, 2, 350, 350, "Gypsum", "Jips"),
    ("anhydrite", "sedimentary", 12, 2, 350, 350, "Anhydrite", "Anhidrit"),
    ("chalk", "sedimentary", 7, 2, 1000, 1000, "Chalk", "Tebeşir"),
    # metamorphic
    ("marble", "metamorphic", 9, 3, 700, 1000, "Marble", "Mermer"),
    ("hornfels", "metamorphic", 19, 4, 400, 700, "Hornfels", "Hornfels"),
    ("metasandstone", "metamorphic", 19, 3, 200, 300, "Metasandstone", "Metakumtaşı"),
    ("quartzite", "metamorphic", 20, 3, 300, 450, "Quartzite", "Kuvarsit"),
    ("migmatite", "metamorphic", 29, 3, 350, 400, "Migmatite", "Migmatit"),
    ("amphibolite", "metamorphic", 26, 6, 400, 500, "Amphibolite", "Amfibolit"),
    ("gneiss", "metamorphic", 28, 5, 300, 750, "Gneiss", "Gnays"),
    ("schist", "metamorphic", 12, 3, 250, 1100, "Schist", "Şist"),
    ("phyllite", "metamorphic", 7, 3, 300, 800, "Phyllite", "Fillit"),
    ("slate", "metamorphic", 7, 4, 400, 600, "Slate", "Arduvaz"),
    # igneous — plutonic, hypabyssal, volcanic, pyroclastic
    ("granite", "igneous", 32, 3, 300, 550, "Granite", "Granit"),
    ("granodiorite", "igneous", 29, 3, 400, 450, "Granodiorite", "Granodiyorit"),
    ("diorite", "igneous", 25, 5, 300, 350, "Diorite", "Diyorit"),
    ("gabbro", "igneous", 27, 3, 400, 500, "Gabbro", "Gabro"),
    ("norite", "igneous", 20, 5, 350, 400, "Norite", "Norit"),
    ("dolerite", "igneous", 16, 5, 300, 400, "Dolerite", "Dolerit"),
    ("porphyry", "igneous", 20, 5, 400, 400, "Porphyry", "Porfiri"),
    ("diabase", "igneous", 15, 5, 300, 350, "Diabase", "Diyabaz"),
    ("peridotite", "igneous", 25, 5, 250, 300, "Peridotite", "Peridotit"),
    ("rhyolite", "igneous", 25, 5, 300, 500, "Rhyolite", "Riyolit"),
    ("dacite", "igneous", 25, 3, 350, 450, "Dacite", "Dasit"),
    ("andesite", "igneous", 25, 5, 300, 500, "Andesite", "Andezit"),
    ("basalt", "igneous", 25, 5, 250, 450, "Basalt", "Bazalt"),
    ("agglomerate", "igneous", 19, 3, 400, 600, "Agglomerate", "Aglomera"),
    ("breccia_volc", "igneous", 19, 5, 500, 500, "Volcanic breccia", "Volkanik breş"),
    ("tuff", "igneous", 13, 5, 200, 400, "Tuff", "Tüf"),
]:
    ROCK_TYPES[_key] = {"class": _cls, "mi": float(_mi), "mi_pm": float(_pm),
                        "MR_lo": float(_mr_lo), "MR_hi": float(_mr_hi),
                        "MR": 0.5 * (_mr_lo + _mr_hi), "en": _en, "tr": _tr}

#: ISRM field estimates of σci [MPa]: key -> low, high, the value picked, texts
STRENGTH_GRADES: Dict[str, dict] = {}
for _key, _lo, _hi, _pick, _en, _tr, _en_field, _tr_field in [
    ("R6", 250, None, 300, "R6 · Extremely strong (> 250 MPa)",
     "R6 · Aşırı dayanımlı (> 250 MPa)",
     "Specimen can only be chipped with a geological hammer",
     "Örnek jeolog çekiciyle ancak yontulabilir"),
    ("R5", 100, 250, 150, "R5 · Very strong (100–250 MPa)", "R5 · Çok dayanımlı (100–250 MPa)",
     "Specimen requires many blows of a geological hammer to fracture it",
     "Örneği kırmak için jeolog çekicinin çok sayıda darbesi gerekir"),
    ("R4", 50, 100, 75, "R4 · Strong (50–100 MPa)", "R4 · Dayanımlı (50–100 MPa)",
     "Specimen requires more than one blow of a geological hammer to fracture it",
     "Örneği kırmak için jeolog çekicinin birden fazla darbesi gerekir"),
    ("R3", 25, 50, 37.5, "R3 · Medium strong (25–50 MPa)", "R3 · Orta dayanımlı (25–50 MPa)",
     "Cannot be scraped or peeled with a pocket knife; fractures with a single blow",
     "Çakıyla kazınamaz; tek çekiç darbesiyle kırılır"),
    ("R2", 5, 25, 15, "R2 · Weak (5–25 MPa)", "R2 · Zayıf (5–25 MPa)",
     "Can be peeled with a pocket knife with difficulty; a firm blow with the point "
     "of a hammer leaves a shallow indentation",
     "Çakıyla güçlükle soyulur; çekicin sivri ucuyla sert vuruş sığ bir iz bırakır"),
    ("R1", 1, 5, 3, "R1 · Very weak (1–5 MPa)", "R1 · Çok zayıf (1–5 MPa)",
     "Crumbles under firm blows with the point of a hammer; can be peeled by a knife",
     "Çekicin sivri ucuyla sert vuruşta ufalanır; çakıyla soyulabilir"),
    ("R0", 0.25, 1, 0.6, "R0 · Extremely weak (0.25–1 MPa)",
     "R0 · Aşırı zayıf (0.25–1 MPa)",
     "Indented by thumbnail", "Tırnakla iz bırakılabilir"),
]:
    STRENGTH_GRADES[_key] = {"lo": float(_lo), "hi": None if _hi is None else float(_hi),
                             "sigma_ci": float(_pick), "en": _en, "tr": _tr,
                             "field_en": _en_field, "field_tr": _tr_field}

#: Guidelines for D (Hoek, Carranza-Torres & Corkum 2002, Table 1)
DISTURBANCE: Dict[str, dict] = {}
for _key, _d, _en, _tr in [
    ("tunnel_excellent", 0.0, "Tunnel — excellent controlled blasting or TBM (D = 0)",
     "Tünel — çok iyi kontrollü patlatma ya da TBM (D = 0)"),
    ("tunnel_mechanical", 0.0, "Tunnel — mechanical or hand excavation, poor rock, "
     "no squeezing (D = 0)",
     "Tünel — zayıf kayada mekanik ya da elle kazı, sıkışma yok (D = 0)"),
    ("tunnel_squeezing", 0.5, "Tunnel — mechanical excavation with severe floor heave "
     "(D = 0.5)", "Tünel — tabanda şiddetli kabarmayla mekanik kazı (D = 0.5)"),
    ("tunnel_poor_blast", 0.8, "Tunnel — very poor blasting, severe local damage "
     "(D = 0.8)", "Tünel — çok kötü patlatma, yerel ağır hasar (D = 0.8)"),
    ("slope_good_blast", 0.7, "Small slope — good controlled blasting (D = 0.7)",
     "Küçük şev — iyi kontrollü patlatma (D = 0.7)"),
    ("slope_poor_blast", 1.0, "Small slope — poor blasting (D = 1.0)",
     "Küçük şev — kötü patlatma (D = 1.0)"),
    ("pit_blasting", 1.0, "Open pit — heavy production blasting (D = 1.0)",
     "Açık ocak — ağır üretim patlatması (D = 1.0)"),
    ("pit_mechanical", 0.7, "Open pit — mechanical excavation (D = 0.7)",
     "Açık ocak — mekanik kazı (D = 0.7)"),
]:
    DISTURBANCE[_key] = {"D": _d, "en": _en, "tr": _tr}

#: The structure classes of the GSI chart, with the RQD each stands for on the
#: quantified chart (Hoek, Carter & Diederichs 2013: GSI = 1.5·JCond89 + RQD/2)
STRUCTURES: Dict[str, dict] = {}
for _key, _rqd, _en, _tr in [
    ("intact", 90.0, "Intact or massive", "Sağlam ya da masif"),
    ("blocky", 70.0, "Blocky — three joint sets", "Bloklu — üç süreksizlik takımı"),
    ("very_blocky", 50.0, "Very blocky — four or more sets",
     "Çok bloklu — dört ya da daha fazla takım"),
    ("disturbed", 30.0, "Blocky / disturbed / seamy — folded, faulted",
     "Bloklu / örselenmiş / damarlı — kıvrımlı, faylı"),
    ("disintegrated", 10.0, "Disintegrated — heavily broken",
     "Parçalanmış — aşırı kırıklı"),
]:
    STRUCTURES[_key] = {"RQD": _rqd, "en": _en, "tr": _tr}

#: The surface condition classes of the GSI chart, with the JCond89 each stands for
SURFACES: Dict[str, dict] = {}
for _key, _jc, _en, _tr in [
    ("very_good", 27.0, "Very good — very rough, fresh", "Çok iyi — çok pürüzlü, taze"),
    ("good", 21.0, "Good — rough, slightly weathered", "İyi — pürüzlü, az ayrışmış"),
    ("fair", 15.0, "Fair — smooth, moderately weathered", "Orta — düz, orta ayrışmış"),
    ("poor", 9.0, "Poor — slickensided, highly weathered",
     "Kötü — kayma çizikli, çok ayrışmış"),
    ("very_poor", 3.0, "Very poor — slickensided, soft clay coatings",
     "Çok kötü — kayma çizikli, yumuşak kil dolgulu"),
]:
    SURFACES[_key] = {"JCond89": _jc, "en": _en, "tr": _tr}


def _entry(table: Dict[str, dict], key: str) -> Optional[dict]:
    return table.get(key)


def rock_type(key: str) -> Optional[dict]:
    """A rock type's typical values, or None for a custom rock."""
    return _entry(ROCK_TYPES, key)


def strength_grade(key: str) -> Optional[dict]:
    return _entry(STRENGTH_GRADES, key)


def disturbance(key: str) -> Optional[dict]:
    return _entry(DISTURBANCE, key)


def name(table: Dict[str, dict], key: str, lang: str = "en") -> str:
    """The name of one entry of a table, in one language."""
    entry = table.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry["en"])


def chart_gsi(structure: str, surface: str) -> float:
    """GSI from the chart's two classes, through the quantified chart."""
    rqd = STRUCTURES.get(structure, STRUCTURES["very_blocky"])["RQD"]
    jcond = SURFACES.get(surface, SURFACES["fair"])["JCond89"]
    return 1.5 * jcond + rqd / 2.0


def picker_options(table: Dict[str, dict], lang: str = "en") -> List[tuple]:
    """(key, name) of every entry, in the table's order."""
    return [(key, name(table, key, lang)) for key in table]
