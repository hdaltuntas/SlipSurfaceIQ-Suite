"""
Text of the interface shell.

Nothing is written into the page: the browser fetches this dictionary from
`/api/meta`, so changing the language is handled in one place and the wording
sits beside the rest of the program's translations. Whatever `i18n` already
says is reused; only what the web shell adds of its own is spelled out here.
"""

from __future__ import annotations

from ..i18n import TRANSLATIONS

#: Text the web shell needs and the rest of the program does not.
#: key -> (English, Turkish)
SHELL = {
    "tagline": ("cantilever reinforced concrete retaining walls",
                "konsol betonarme istinat duvarları"),
    "language": ("Language", "Dil"),
    "open": ("Open…", "Aç…"),
    "save": ("Save", "Kaydet"),
    "theme": ("Theme", "Tema"),
    "ready": ("Ready.", "Hazır."),
    "section_wall": ("Wall and soils", "Duvar ve zeminler"),
    "section_options": ("Methods, criteria and earthquake", "Yöntemler, ölçütler ve deprem"),
    "section_concrete": ("Reinforced concrete", "Betonarme"),
    "suggest": ("Suggest dimensions", "Ön boyutlandır"),
    "suggested": ("Preliminary dimensions filled in from H; run the analysis to check them.",
                  "Ön boyutlar H'den dolduruldu; kontrol için çözümlemeyi çalıştırın."),
    "stability_title": ("Stability", "Duraylılık"),
    "bearing_title": ("Bearing capacity by method", "Yönteme göre taşıma gücü"),
    "methods_title": ("Earth pressure by method", "Yönteme göre toprak basıncı"),
    "forces_title": ("Forces on the wall", "Duvara etkiyen kuvvetler"),
    "seismic_title": ("Earthquake (TBDY 2018)", "Deprem (TBDY 2018)"),
    "design_title": ("Member design (TS 500)", "Eleman tasarımı (TS 500)"),
    "schedule_title": ("Bar bending schedule (per metre of wall)",
                       "Donatı açılımı (duvarın metresi başına)"),
    "view_summary": ("Summary", "Özet"),
    "view_stability": ("Stability", "Duraylılık"),
    "view_design": ("Reinforcement", "Donatı"),
    "view_text": ("Results", "Sonuçlar"),
    "view_figures": ("Figures", "Şekiller"),
    "figure": ("Figure", "Şekil"),
    "report_format": ("Report", "Rapor"),
    "report_pdf": ("PDF report", "PDF rapor"),
    "report_html": ("HTML report", "HTML rapor"),
    "report_docx": ("Word report", "Word rapor"),
    "dxf": ("Drawing (DXF)", "Çizim (DXF)"),
    "dxf_done": ("Drawing downloaded.", "Çizim indirildi."),
    "no_results": ("Run the analysis.", "Analizi çalıştırın."),
    "error": ("Error", "Hata"),
    "saved": ("Saved.", "Kaydedildi."),
    "loaded": ("Project loaded.", "Proje yüklendi."),
    "bad_file": ("That file is not a SlipSurface IQ Wall project.",
                 "Bu dosya bir SlipSurface IQ Wall projesi değil."),
    "stop_hint": ("Press Ctrl+C to stop.", "Durdurmak için Ctrl+C."),
    "stopped": ("stopped", "durduruldu"),
}

#: Keys taken straight from the program's translations, under the same name.
REUSED = [
    "run_analysis_button", "running_analysis", "analysis_complete", "report_action",
    "report_running", "warnings_title",
]


def shell_strings(lang: str = "en") -> dict:
    """Every string the page needs, in one language."""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    strings = {key: (tr if lang == "tr" else en) for key, (en, tr) in SHELL.items()}
    strings.update({key: translations[key] for key in REUSED})
    return strings
