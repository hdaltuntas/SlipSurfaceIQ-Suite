"""
Calculation report for SlipSurface IQ Liquefaction.

The report is assembled as HTML (inputs, susceptibility, triggering test by
test, settlement and indices, comparison of the procedures, checks, figures,
warnings, method notes and, if one was run, the study) and exported as
  * PDF   — through reportlab (see `slipsurface.liquefaction.pdf`)
  * HTML  — a single self-contained file (figures embedded as base64)
  * DOCX  — optional, needs `python-docx`

There is one assembly, `build_html()`, so all three formats say the same thing.
"""

from __future__ import annotations

import base64
import datetime
import html
import io
import math
from typing import Any, Dict, List, Optional

from matplotlib.figure import Figure

from . import study_plots
from .config import APP_NAME, APP_VERSION
from .i18n import TRANSLATIONS, warning_text
from .plotting import Plotter, available
from .study import OUTPUTS
from .summary import fs_text

TEXTS = {
    "en": {
        "title": f"{APP_NAME} — Calculation Report",
        "date": "Date", "analyst": "Analyst", "software": "Software",
        "sec_inputs": "1. Input data", "sec_quake": "1.1 Earthquake and groundwater",
        "sec_setup": "1.2 SPT set-up", "sec_soil": "1.3 Soil profile",
        "sec_tests": "1.4 SPT tests", "sec_opts": "1.5 Analysis options and criteria",
        "sec_susc": "2. Susceptibility", "sec_trig": "3. Liquefaction triggering",
        "sec_cons": "4. Consequences", "sec_cons_tests": "4.1 Volumetric strain and settlement",
        "sec_soft": "4.2 Cyclic softening of clay-like soils",
        "sec_cons_total": "4.3 Over the borehole", "sec_compare": "4.4 Comparison of the procedures",
        "sec_checks": "4.5 Checks", "sec_setup_cpt": "1.2 CPT set-up",
        "sec_tests_cpt": "1.4 CPT sounding", "layers_more": "Grain size and clay parameters",
        "area_ratio": "Net area ratio of the cone a", "ic_limit": "Clay-like above Ic",
        "cfc": "CFC (fines content from Ic)", "nkt": "Cone factor Nkt", "n_read": "Readings",
        "gravel": "Gravel correction (JRA 1996)", "test_type": "Field test",
        "dry": "Settlement of dry sand (Pradel 1998)",
        "soft": "Cyclic softening of clay-like soils (Boulanger & Idriss 2007)",
        "geometry": "Ground geometry (lateral spreading)", "slope": "Ground slope S",
        "face_l": "Distance to the free face L", "face_h": "Height of the free face H",
        "susc_cpt": "A reading with Ic above {ic:.2f} is taken as clay-like (Robertson & Wride "
                    "1998); the others as sand-like. Ic and the fines content implied by it are "
                    "in the tables of sections 1.4 and 3.",
        "ds_dry": "Δs dry (mm)", "no_soft": "No clay-like soil below the water table was checked.",
        "h_soft": "Thickness that softens cyclically (FS < 1)",
        "settlement_sat": "Settlement of the saturated soil",
        "settlement_dry": "Settlement of the dry sand",
        "ldi": "Lateral displacement index LDI", "ld": "Lateral displacement LD",
        "sec_figs": "5. Figures", "sec_warn": "6. Warnings", "sec_notes": "7. Method notes",
        "parameter": "Parameter", "value": "Value", "unit": "Unit",
        "magnitude": "Moment magnitude Mw", "amax": "Peak ground acceleration a_max",
        "sds": "Short-period design spectral acceleration S_DS",
        "amax_src": "a_max taken as", "zw": "Water table during the earthquake",
        "zw_test": "Water table when the SPT was made", "gw": "Unit weight of water γw",
        "energy": "Hammer energy ratio ER", "borehole": "Borehole diameter",
        "stickup": "Rod length above the ground", "rod": "Short-rod correction CR",
        "liner": "Sampler without liners", "yes": "yes", "no": "no",
        "layer": "Layer", "top": "Top", "bottom": "Bottom", "kind": "Soil",
        "method": "Triggering procedure", "susc": "Fine-grained soil criterion",
        "fine": "Fine-grained from FC ≥", "uncertain": "'To be tested' soils taken as susceptible",
        "sdepth": "Depth of the settlement", "pl": "Cetin et al.: probability of liquefaction PL",
        "vs12": "Cetin et al.: Vs,12", "fs_req": "Required factor of safety",
        "s_allow": "Allowable settlement",
        "class": "Class", "state": "State", "interval": "Represents",
        "fs_min": "Lowest factor of safety", "at": "at depth", "h_liq": "Thickness with FS < 1",
        "settlement": "Total settlement", "lpi": "Liquefaction potential index LPI",
        "lsn": "Liquefaction severity number LSN", "grade": "Grade",
        "procedure": "Procedure", "n_liq": "Tests with FS < 1",
        "check": "Check", "actual": "Actual", "allowable": "Required / allowable",
        "status": "Status", "c_fs": "Factor of safety against liquefaction",
        "c_s": "Settlement", "ok": "OK", "notok": "NOT OK", "risk": "RISK", "na": "n/a",
        "estimated": "estimated from the SPT",
        "soil_units": "γ, γsat: kN/m³ · FC, clay, LL, PI, wn: % · Vs: m/s · NP: non-plastic",
        "sec_study": "8. Parametric / reliability study", "sec_study_vars": "8.1 Variables",
        "sec_study_stats": "8.2 Statistics of the outputs",
        "sec_study_rel": "8.3 Probability of exceeding the criteria",
        "sec_study_sens": "8.4 Sensitivities (Spearman ρ)", "sec_study_figs": "8.5 Figures",
        "study_method": "Sampling method", "study_n": "Samples", "study_ok": "Successful analyses",
        "variable": "Variable", "mode": "Mode", "range": "Range", "dist": "Distribution",
        "mean": "Mean", "cov": "CoV", "min": "Min", "max": "Max", "output": "Output",
        "std": "Std", "criterion": "Criterion", "n_fail": "Exceeded", "pf": "P",
        "pf_ci": "95 % CI", "beta_idx": "β",
        "notes": [
            "Demand: CSR = 0.65·(a_max/g)·(σv/σ'v)·rd (Seed & Idriss 1971), with σv and σ'v for "
            "the water table during the earthquake. The blow count is normalised with σ'v at "
            "the time of the test.",
            "SPT: N60 = N·CE·CB·CR·CS with CE = ER/60, CB from the borehole diameter, CR from "
            "the rod length (depth + stick-up) and CS = 1 + (N1)60/100 (1.1 – 1.3) for a "
            "sampler without liners (Youd et al. 2001; Idriss & Boulanger 2014).",
            "Idriss & Boulanger (2014): rd(z, M) of Idriss (1999); CN = (Pa/σ'v)^m ≤ 1.7 with "
            "m = 0.784 − 0.0768·√(N1)60cs; Δ(N1)60 = exp(1.63 + 9.7/(FC+0.01) − "
            "(15.7/(FC+0.01))²); CRR7.5 = exp(N/14.1 + (N/126)² − (N/23.6)³ + (N/25.4)⁴ − 2.8); "
            "MSF = 1 + (MSFmax − 1)(8.64·e^(−M/4) − 1.325), MSFmax = 1.09 + (N/31.5)² ≤ 2.2; "
            "Kσ = 1 − Cσ·ln(σ'v/Pa) ≤ 1.1, Cσ = 1/(18.9 − 2.55·√N) ≤ 0.3.",
            "Youd et al. (2001): rd of Blake (to 23 m, then Liao & Whitman); CN = (Pa/σ'v)^0.5 "
            "≤ 1.7; (N1)60cs = α + β·(N1)60; the NCEER curve for (N1)60cs < 30, non-liquefiable "
            "above; MSF = 10^2.24/M^2.56; Kσ = (σ'v/Pa)^(f−1) ≤ 1 with f from the relative "
            "density (0.8 – 0.6).",
            "Cetin et al. (2004): CRR = exp[((N1)60·(1 + 0.004·FC) − 29.53·ln Mw − "
            "3.70·ln(σ'v/Pa) + 0.05·FC + 16.85 + 2.70·Φ⁻¹(PL))/13.32], FC between 5 and 35 %, "
            "CN ≤ 1.6, and their rd(z, Mw, a_max, Vs,12). The magnitude and the overburden are "
            "inside the expression.",
            "TBDY 2018 (§ 16.6): τ_eq = 0.65·σv0·(a_max/g)·rd with the linear rd, a_max = "
            "0.4·S_DS·g; CN = (100/σ'v0)^0.5 ≤ 1.7; (N1)60f = α + β·(N1)60; the NCEER curve; "
            "C_M = 10^2.24/M^2.56; FL = τ_R/τ_eq, and FL ≥ 1.1 is required.",
            "Andrus & Stokoe (2000), where the layers carry Vs: Vs1 = Vs·(Pa/σ'v)^0.25; "
            "CRR7.5 = 0.022·(Vs1/100)² + 2.8·(1/(Vs1* − Vs1) − 1/Vs1*), Vs1* = 215 – 200 m/s "
            "with FC; MSF = (M/7.5)^−2.56. Shown for comparison only.",
            "Susceptibility: a soil below the FC threshold or non-plastic is sand-like; a "
            "fine-grained one is judged by the chosen criterion (Chinese criteria; Andrews & "
            "Martin 2000; Seed et al. 2003; Bray & Sancio 2006; Boulanger & Idriss 2006). "
            "Clay-like soils may soften cyclically; that is not assessed here.",
            "Volumetric strain: Ishihara & Yoshimine (1992) as fitted by Yoshimine et al. (2006): "
            "εv = 1.5·exp(−2.5·Dr)·min(0.08, γmax), Dr = √((N1)60cs/46). Settlement: Σ εv·Δz "
            "below the water table, down to the chosen depth. Each test stands for the part of "
            "its layer nearest to it.",
            "LPI = ∫₀²⁰ F·(10 − 0.5z) dz, F = 1 − FS for FS < 1 (Iwasaki et al. 1978); "
            "LSN = 1000·∫ εv/z dz (van Ballegooy et al. 2014).",
            "CPT: qt = qc + (1 − a)·u2; Ic from Q and F (Robertson & Wride 1998 for their "
            "procedure, Robertson 2009 for Idriss & Boulanger); FC = 80·(Ic + CFC) − 137. "
            "Idriss & Boulanger (2014): qc1N = CN·qc/Pa, m = 1.338 − 0.249·qc1Ncs^0.264, "
            "Δqc1N = (11.9 + qc1N/14.6)·exp(1.63 − 9.7/(FC+2) − (15.7/(FC+2))²), CRR7.5 = "
            "exp(q/113 + (q/1000)² − (q/140)³ + (q/137)⁴ − 2.8), MSFmax = 1.09 + (q/180)³, "
            "Cσ = 1/(37.3 − 8.27·q^0.264). Robertson & Wride (1998): qc1Ncs = Kc·qc1N, CRR7.5 = "
            "0.833·q/1000 + 0.05 (q < 50) or 93·(q/1000)³ + 0.08 (50 ≤ q < 160); Ic > 2.6 "
            "clay-like. Dr = 0.478·qc1Ncs^0.264 − 1.063 for the strains.",
            "Cyclic softening of clay-like soils (Boulanger & Idriss 2007): CRR = 0.8·(su/σ'v)·"
            "MSF, MSF = 1.12·exp(−M/4) + 0.828 ≤ 1.13; su/σ'v measured, from the CPT as "
            "(qt − σv)/Nkt, or 0.22·OCR^0.8. Level ground (Kα = 1).",
            "Dry sand above the water table (Pradel 1998): γ from τav = 0.65·a_max·σv·rd and "
            "Gmax = 447·Pa·(N1)60^(1/3)·(p/Pa)^0.5; ε15 = γ·((N1)60/20)^−1.2, εv = "
            "2·ε15·(Neq/15)^0.45, Neq = (M − 4)^2.17. For the CPT, N60 = (qt/Pa)/10^(1.1268 − "
            "0.2817·Ic) (Robertson 2012).",
            "Lateral spreading (Zhang et al. 2004): LDI = ∫ γmax dz over the liquefiable soil "
            "(to 2H for a free face); LD = (S + 0.2)·LDI for gently sloping ground "
            "(0.2 < S < 3.5 %), LD = 6·(L/H)^−0.8·LDI for level ground with a free face "
            "(4 < L/H < 40). γmax as in the strain note above.",
            "Gravelly layers (D50 ≥ 2 mm): the blow count is reduced by 1 − 0.36·log10(D50/2) "
            "(Japan Road Association 1996). The SPT over-reads in gravel; the result is "
            "indicative, and a Vs or large-penetration test is the better check.",
        ],
    },
    "tr": {
        "title": f"{APP_NAME} — Hesap Raporu",
        "date": "Tarih", "analyst": "Hazırlayan", "software": "Yazılım",
        "sec_inputs": "1. Girdi verileri", "sec_quake": "1.1 Deprem ve yeraltı suyu",
        "sec_setup": "1.2 SPT düzeni", "sec_soil": "1.3 Zemin profili",
        "sec_tests": "1.4 SPT deneyleri", "sec_opts": "1.5 Analiz seçenekleri ve ölçütler",
        "sec_susc": "2. Sıvılaşabilirlik", "sec_trig": "3. Sıvılaşmanın tetiklenmesi",
        "sec_cons": "4. Sonuçlar", "sec_cons_tests": "4.1 Hacimsel deformasyon ve oturma",
        "sec_soft": "4.2 Kil benzeri zeminlerde tekrarlı yumuşama",
        "sec_cons_total": "4.3 Sondaj boyunca", "sec_compare": "4.4 Yöntemlerin karşılaştırması",
        "sec_checks": "4.5 Kontroller", "sec_setup_cpt": "1.2 CPT düzeni",
        "sec_tests_cpt": "1.4 CPT sondajı", "layers_more": "Dane boyu ve kil parametreleri",
        "area_ratio": "Koni net alan oranı a", "ic_limit": "Kil benzeri: Ic >",
        "cfc": "CFC (Ic'den ince dane oranı)", "nkt": "Koni faktörü Nkt", "n_read": "Okuma sayısı",
        "gravel": "Çakıl düzeltmesi (JRA 1996)", "test_type": "Arazi deneyi",
        "dry": "Kuru kum oturması (Pradel 1998)",
        "soft": "Kil benzeri zeminlerde tekrarlı yumuşama (Boulanger & Idriss 2007)",
        "geometry": "Zemin geometrisi (yanal yayılma)", "slope": "Zemin eğimi S",
        "face_l": "Serbest yüze uzaklık L", "face_h": "Serbest yüz yüksekliği H",
        "susc_cpt": "Ic değeri {ic:.2f}'den büyük okumalar kil benzeri (Robertson & Wride 1998), "
                    "diğerleri kum benzeri kabul edilmiştir. Ic ve ondan bulunan ince dane "
                    "oranı 1.4 ve 3. bölümlerin tablolarındadır.",
        "ds_dry": "Δs kuru (mm)", "no_soft": "Su seviyesi altında kontrol edilen kil benzeri "
                                              "zemin yok.",
        "h_soft": "Tekrarlı yumuşayan kalınlık (FS < 1)",
        "settlement_sat": "Doygun zeminin oturması",
        "settlement_dry": "Kuru kumun oturması",
        "ldi": "Yanal yer değiştirme indeksi LDI", "ld": "Yanal yer değiştirme LD",
        "sec_figs": "5. Şekiller", "sec_warn": "6. Uyarılar", "sec_notes": "7. Yöntem notları",
        "parameter": "Parametre", "value": "Değer", "unit": "Birim",
        "magnitude": "Moment büyüklüğü Mw", "amax": "En büyük yer ivmesi a_max",
        "sds": "Kısa periyot tasarım spektral ivmesi S_DS",
        "amax_src": "a_max şöyle alındı", "zw": "Deprem sırasında su seviyesi",
        "zw_test": "SPT sırasında su seviyesi", "gw": "Suyun birim hacim ağırlığı γw",
        "energy": "Tokmak enerji oranı ER", "borehole": "Sondaj çapı",
        "stickup": "Yüzey üstü tij boyu", "rod": "Kısa tij düzeltmesi CR",
        "liner": "Kılıfsız numune alıcı", "yes": "evet", "no": "hayır",
        "layer": "Tabaka", "top": "Üst", "bottom": "Alt", "kind": "Zemin",
        "method": "Tetiklenme yöntemi", "susc": "İnce daneli zemin ölçütü",
        "fine": "İnce daneli sayılma FC ≥", "uncertain": "'Deneyle belirlenmeli' zeminler "
                                                         "sıvılaşabilir sayıldı",
        "sdepth": "Oturma hesap derinliği", "pl": "Cetin vd.: sıvılaşma olasılığı PL",
        "vs12": "Cetin vd.: Vs,12", "fs_req": "Gerekli güvenlik sayısı",
        "s_allow": "İzin verilen oturma",
        "class": "Sınıf", "state": "Durum", "interval": "Temsil ettiği",
        "fs_min": "En küçük güvenlik sayısı", "at": "derinlik", "h_liq": "FS < 1 olan kalınlık",
        "settlement": "Toplam oturma", "lpi": "Sıvılaşma potansiyel indeksi LPI",
        "lsn": "Sıvılaşma şiddet sayısı LSN", "grade": "Derece",
        "procedure": "Yöntem", "n_liq": "FS < 1 olan deney",
        "check": "Kontrol", "actual": "Hesaplanan", "allowable": "Gerekli / izin verilen",
        "status": "Durum", "c_fs": "Sıvılaşmaya karşı güvenlik sayısı",
        "c_s": "Oturma", "ok": "UYGUN", "notok": "UYGUN DEĞİL", "risk": "RİSK VAR", "na": "yok",
        "estimated": "SPT'den tahmin",
        "soil_units": "γ, γdoy: kN/m³ · FC, kil, LL, PI, wn: % · Vs: m/s · NP: plastik değil",
        "sec_study": "8. Parametrik / güvenilirlik çalışması", "sec_study_vars": "8.1 Değişkenler",
        "sec_study_stats": "8.2 Çıktıların istatistikleri",
        "sec_study_rel": "8.3 Ölçütlerin aşılma olasılığı",
        "sec_study_sens": "8.4 Duyarlılıklar (Spearman ρ)", "sec_study_figs": "8.5 Şekiller",
        "study_method": "Örnekleme yöntemi", "study_n": "Örnek sayısı",
        "study_ok": "Başarılı analiz",
        "variable": "Değişken", "mode": "Mod", "range": "Aralık", "dist": "Dağılım",
        "mean": "Ortalama", "cov": "CoV", "min": "Min", "max": "Maks", "output": "Çıktı",
        "std": "Std", "criterion": "Ölçüt", "n_fail": "Aşan", "pf": "P",
        "pf_ci": "%95 GA", "beta_idx": "β",
        "notes": [
            "İstem: CSR = 0.65·(a_max/g)·(σv/σ'v)·rd (Seed & Idriss 1971); σv ve σ'v deprem "
            "sırasındaki su seviyesiyle. Darbe sayısı deney anındaki σ'v ile normalize edilir.",
            "SPT: N60 = N·CE·CB·CR·CS; CE = ER/60, CB sondaj çapından, CR tij boyundan (derinlik "
            "+ yüzey üstü) ve kılıfsız numune alıcıda CS = 1 + (N1)60/100 (1.1 – 1.3) (Youd vd. "
            "2001; Idriss & Boulanger 2014).",
            "Idriss & Boulanger (2014): Idriss (1999) rd(z, M); CN = (Pa/σ'v)^m ≤ 1.7, "
            "m = 0.784 − 0.0768·√(N1)60cs; Δ(N1)60 = exp(1.63 + 9.7/(FC+0.01) − "
            "(15.7/(FC+0.01))²); CRR7.5 = exp(N/14.1 + (N/126)² − (N/23.6)³ + (N/25.4)⁴ − 2.8); "
            "MSF = 1 + (MSFmax − 1)(8.64·e^(−M/4) − 1.325), MSFmax = 1.09 + (N/31.5)² ≤ 2.2; "
            "Kσ = 1 − Cσ·ln(σ'v/Pa) ≤ 1.1, Cσ = 1/(18.9 − 2.55·√N) ≤ 0.3.",
            "Youd vd. (2001): Blake rd'si (23 m'ye kadar, sonra Liao & Whitman); CN = "
            "(Pa/σ'v)^0.5 ≤ 1.7; (N1)60cs = α + β·(N1)60; (N1)60cs < 30 için NCEER eğrisi, "
            "üstünde sıvılaşmaz; MSF = 10^2.24/M^2.56; Kσ = (σ'v/Pa)^(f−1) ≤ 1, f rölatif "
            "sıkılıktan (0.8 – 0.6).",
            "Cetin vd. (2004): CRR = exp[((N1)60·(1 + 0.004·FC) − 29.53·ln Mw − "
            "3.70·ln(σ'v/Pa) + 0.05·FC + 16.85 + 2.70·Φ⁻¹(PL))/13.32], FC %5 – %35 arasında, "
            "CN ≤ 1.6 ve kendi rd(z, Mw, a_max, Vs,12) bağıntıları. Büyüklük ve örtü gerilmesi "
            "ifadenin içindedir.",
            "TBDY 2018 (§ 16.6): τ_deprem = 0.65·σv0·(a_max/g)·rd, doğrusal rd, a_max = "
            "0.4·S_DS·g; CN = (100/σ'v0)^0.5 ≤ 1.7; (N1)60f = α + β·(N1)60; NCEER eğrisi; "
            "C_M = 10^2.24/M^2.56; FL = τ_R/τ_deprem ve FL ≥ 1.1 istenir.",
            "Andrus & Stokoe (2000), tabakalarda Vs varsa: Vs1 = Vs·(Pa/σ'v)^0.25; "
            "CRR7.5 = 0.022·(Vs1/100)² + 2.8·(1/(Vs1* − Vs1) − 1/Vs1*), FC ile Vs1* = 215 – 200 "
            "m/s; MSF = (M/7.5)^−2.56. Yalnız karşılaştırma içindir.",
            "Sıvılaşabilirlik: FC eşiğinin altındaki ya da plastik olmayan zemin kum benzeridir; "
            "ince daneli zemin seçilen ölçütle değerlendirilir (Çin ölçütü; Andrews & Martin "
            "2000; Seed vd. 2003; Bray & Sancio 2006; Boulanger & Idriss 2006). Kil benzeri "
            "zeminler tekrarlı yükte yumuşayabilir; bu burada değerlendirilmez.",
            "Hacimsel deformasyon: Ishihara & Yoshimine (1992), Yoshimine vd. (2006) uyarlaması: "
            "εv = 1.5·exp(−2.5·Dr)·min(0.08, γmax), Dr = √((N1)60cs/46). Oturma: su seviyesi "
            "altında, seçilen derinliğe kadar Σ εv·Δz. Her deney, tabakasının kendisine en yakın "
            "kısmını temsil eder.",
            "LPI = ∫₀²⁰ F·(10 − 0.5z) dz, FS < 1 için F = 1 − FS (Iwasaki vd. 1978); "
            "LSN = 1000·∫ εv/z dz (van Ballegooy vd. 2014).",
            "CPT: qt = qc + (1 − a)·u2; Ic, Q ve F'den (kendi yöntemleri için Robertson & Wride "
            "1998, Idriss & Boulanger için Robertson 2009); FC = 80·(Ic + CFC) − 137. Idriss & "
            "Boulanger (2014): qc1N = CN·qc/Pa, m = 1.338 − 0.249·qc1Ncs^0.264, Δqc1N = "
            "(11.9 + qc1N/14.6)·exp(1.63 − 9.7/(FC+2) − (15.7/(FC+2))²), CRR7.5 = exp(q/113 + "
            "(q/1000)² − (q/140)³ + (q/137)⁴ − 2.8), MSFmax = 1.09 + (q/180)³, Cσ = 1/(37.3 − "
            "8.27·q^0.264). Robertson & Wride (1998): qc1Ncs = Kc·qc1N, CRR7.5 = 0.833·q/1000 + "
            "0.05 (q < 50) ya da 93·(q/1000)³ + 0.08 (50 ≤ q < 160); Ic > 2.6 kil benzeri. "
            "Deformasyonlar için Dr = 0.478·qc1Ncs^0.264 − 1.063.",
            "Kil benzeri zeminlerde tekrarlı yumuşama (Boulanger & Idriss 2007): CRR = "
            "0.8·(su/σ'v)·MSF, MSF = 1.12·exp(−M/4) + 0.828 ≤ 1.13; su/σ'v ölçülen, CPT'den "
            "(qt − σv)/Nkt ya da 0.22·OCR^0.8. Düz zemin (Kα = 1).",
            "Su seviyesi üstündeki kuru kum (Pradel 1998): τav = 0.65·a_max·σv·rd ve Gmax = "
            "447·Pa·(N1)60^(1/3)·(p/Pa)^0.5 ile γ; ε15 = γ·((N1)60/20)^−1.2, εv = "
            "2·ε15·(Neq/15)^0.45, Neq = (M − 4)^2.17. CPT için N60 = (qt/Pa)/10^(1.1268 − "
            "0.2817·Ic) (Robertson 2012).",
            "Yanal yayılma (Zhang vd. 2004): sıvılaşan zeminde LDI = ∫ γmax dz (serbest yüzde 2H'ye "
            "kadar); hafif eğimli zeminde LD = (S + 0.2)·LDI (%0.2 < S < %3.5), serbest yüzlü düz "
            "zeminde LD = 6·(L/H)^−0.8·LDI (4 < L/H < 40). γmax yukarıdaki deformasyon notundaki "
            "gibidir.",
            "Çakıllı tabakalar (D50 ≥ 2 mm): darbe sayısı 1 − 0.36·log10(D50/2) ile azaltılır "
            "(Japonya Karayolları Birliği 1996). SPT çakılda yüksek okur; sonuç göstergedir, Vs "
            "ya da büyük penetrasyon deneyi daha iyi bir kontroldür.",
        ],
    },
}

#: The interface's palette: warm paper, ink, terracotta; serif headings
_CSS = """
body { font-family: system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
       font-size: 10pt; color: #141413; }
h1, h2, h3 { font-family: 'Tiempos Text', 'Source Serif 4', 'Iowan Old Style', Palatino,
             Georgia, 'DejaVu Serif', serif; font-weight: 500; }
h1 { font-size: 20pt; color: #141413; margin-bottom: 2px; }
h2 { font-size: 14pt; color: #C6613F; border-bottom: 1px solid #E3E0D5; padding-bottom: 2px;
     margin-top: 20px; }
h3 { font-size: 11.5pt; color: #141413; margin-top: 12px; }
table { border-collapse: collapse; margin: 4px 0 8px 0; }
th { background: #F0EEE6; text-align: left; padding: 3px 6px; border: 1px solid #E3E0D5;
     font-size: 9pt; }
td { padding: 3px 6px; border: 1px solid #E3E0D5; font-size: 9pt; }
.ok { color: #3F7F4F; font-weight: bold; } .bad { color: #B0413E; font-weight: bold; }
.meta { color: #73726C; } .note { color: #73726C; font-size: 9pt; }
"""


def _esc(x) -> str:
    return html.escape(str(x))


def _f(x, nd=2) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    return f"{x:,.{nd}f}"


def _status(T, s: str, risk: bool = False) -> str:
    if s == "N/A":
        return T["na"]
    return (f'<span class="ok">{T["ok"]}</span>' if s == "OK"
            else f'<span class="bad">{T["risk"] if risk else T["notok"]}</span>')


def _state(L, state: str) -> str:
    text = _esc(L["state_" + state])
    if state == "liquefied":
        return f'<span class="bad">{text}</span>'
    return text


def _table(headers: List[str], rows: List[List[Any]], widths: Optional[List[int]] = None) -> str:
    out = ["<table width='100%'>"]
    if widths:
        cells = "".join(f"<th width='{w}%'>{_esc(h)}</th>" for h, w in zip(headers, widths))
    else:
        cells = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    out.append("<tr>" + cells + "</tr>")
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


def _kv_table(T, rows: List[List[Any]]) -> str:
    return _table([T["parameter"], T["value"], T["unit"]], rows, [50, 36, 14])


# ----------------------------------------------------------------------
def _png(fig: Figure, dpi: int) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    return buf.getvalue()


def render_figures(analysis, lang: str, keys=None, dpi: int = 130) -> Dict[str, bytes]:
    """The report figures as PNG bytes (off-screen, white, untitled); by default
    every figure that applies to the analysis."""
    if keys is None:
        keys = available(analysis)
    # white paper, and no title inside: the report prints the figure's name above it
    plotter = Plotter(analysis, lang, "paper", titles=False)
    out = {}
    for key in keys:
        fig = Figure(figsize=(10, 7), dpi=dpi)
        plotter.draw(key, fig)
        out[key] = _png(fig, dpi)
    return out


def render_study_figures(study, lang: str, dpi: int = 110) -> Dict[str, bytes]:
    """Study figures keyed 'study_<view>' (only the views that apply)."""
    if study is None or not study.rows:
        return {}
    L = TRANSLATIONS[lang]
    views = ["oat", "hist"] if study.method == "oat" else ["hist", "scatter", "tornado"]
    draw = {"oat": study_plots.plot_oat, "hist": study_plots.plot_hist,
            "scatter": study_plots.plot_scatter, "tornado": study_plots.plot_tornado}
    out = {}
    for view in views:
        fig = Figure(figsize=(10, 7), dpi=dpi)
        draw[view](fig, study, L, "s_total", theme="paper")
        out[f"study_{view}"] = _png(fig, dpi)
    return out


def _study_section(T, L, study, figures, img_src) -> List[str]:
    parts = [f"<h2 style='page-break-before:always'>{T['sec_study']}</h2>"]
    s = study.summary
    parts.append(_kv_table(T, [
        [T["study_method"], L[f"method_{study.method}"], ""],
        [T["study_n"], str(s.get("n_total", 0)), ""],
        [T["study_ok"], str(s.get("n_ok", 0)), ""],
    ]))
    parts.append(f"<h3>{T['sec_study_vars']}</h3>")
    rows = []
    for v in study.variables:
        if v.mode == "range":
            rows.append([_esc(v.label), T["range"], _f(v.vmin, 3), _f(v.vmax, 3), "—", "—", "—",
                         v.n_points])
        else:
            rows.append([_esc(v.label), T["dist"], "—", "—", L[f"dist_{v.dist}"], _f(v.mean, 3),
                         _f(v.cov, 3), "—"])
    parts.append(_table([T["variable"], T["mode"], T["min"], T["max"], T["dist"], T["mean"],
                         T["cov"], "n"], rows, [28, 12, 10, 10, 14, 10, 8, 8]))
    parts.append(f"<h3>{T['sec_study_stats']}</h3>")
    rows = [[_esc(L.get(f"out_{k}", k)), st["n"], _f(st["mean"]), _f(st["std"]), _f(st["p5"]),
             _f(st["p50"]), _f(st["p95"])]
            for k, _ in OUTPUTS if k in s.get("stats", {}) for st in [s["stats"][k]]]
    parts.append(_table([T["output"], "n", T["mean"], T["std"], "P5", "P50", "P95"],
                        rows, [34, 8, 12, 12, 11, 11, 12]))
    if s.get("reliability"):
        parts.append(f"<h3>{T['sec_study_rel']}</h3>")
        rows = []
        for name, r in s["reliability"].items():
            rows.append([_esc(L[name]), r["n"], r["n_fail"], f"{r['pf']:.3g}",
                         f"[{r['pf_lo']:.2g}, {r['pf_hi']:.2g}]",
                         _esc(study_plots._beta_text(r["beta"], r["n"]))])
        parts.append(_table([T["criterion"], "n", T["n_fail"], T["pf"], T["pf_ci"], T["beta_idx"]],
                            rows, [30, 10, 12, 14, 20, 14]))
    if s.get("spearman"):
        parts.append(f"<h3>{T['sec_study_sens']}</h3>")
        outs = [k for k, _ in OUTPUTS if k in s["spearman"]]
        rows = [[_esc(v.label)] + [f"{s['spearman'][k].get(v.path, float('nan')):+.2f}"
                                   for k in outs] for v in study.variables]
        parts.append(_table([T["variable"]] + [L.get(f"out_{k}", k) for k in outs], rows))
    parts.append(f"<h3>{T['sec_study_figs']}</h3>")
    for key in figures:
        if key.startswith("study_"):
            parts.append(f"<p><img src='{img_src(key)}' width='640'></p>")
    return parts


def build_html(analysis, lang: str, figures: Dict[str, bytes], img_src=None,
               study=None) -> str:
    """
    Builds the report HTML. img_src(key) -> value for the <img src> attribute;
    the default embeds base64 data URIs (the self-contained HTML file). The PDF
    and DOCX writers pass a `fig://<key>` mapper and resolve the keys against
    the figure dictionary themselves.
    """
    T = TEXTS.get(lang, TEXTS["en"])
    L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    a, res = analysis, analysis.results
    t = res["tests"]
    m = res["methods"][a.method]
    info = a.config.get("project_info", {})
    if img_src is None:
        def img_src(key):
            return "data:image/png;base64," + base64.b64encode(figures[key]).decode()

    yn = lambda b: T["yes"] if b else T["no"]  # noqa: E731
    parts = [f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head><body>"]
    parts.append(f"<h1>{_esc(info.get('title', ''))}</h1>")
    parts.append(f"<p class='meta'>{_esc(T['title'])}<br>"
                 f"{T['date']}: {datetime.date.today().isoformat()} &nbsp;|&nbsp; "
                 f"{T['analyst']}: {_esc(info.get('analyst', ''))} &nbsp;|&nbsp; "
                 f"{T['software']}: {APP_NAME} v{APP_VERSION}</p>")

    # ---------------- 1. inputs
    parts.append(f"<h2>{T['sec_inputs']}</h2>")
    parts.append(f"<h3>{T['sec_quake']}</h3>")
    rows = [[T["magnitude"], _f(a.magnitude), ""]]
    if a.pga_source == "tbdy":
        rows += [[T["sds"], _f(a.sds, 3), ""], [T["amax_src"], "0.4 · S_DS", ""]]
    rows += [[T["amax"], _f(a.amax, 3), "g"], [T["zw"], _f(a.zw), "m"],
             [T["zw_test"], _f(a.zw_test), "m"], [T["gw"], _f(a.profile.gw), "kN/m³"]]
    parts.append(_kv_table(T, rows))

    if res["kind"] == "cpt":
        parts.append(f"<h3>{T['sec_setup_cpt']}</h3>")
        parts.append(_kv_table(T, [
            [T["area_ratio"], _f(a.area_ratio), ""], [T["ic_limit"], _f(a.ic_limit), ""],
            [T["cfc"], _f(a.cfc), ""], [T["nkt"], _f(a.nkt, 1), ""],
            [T["n_read"], str(len(t["z"])), ""],
        ]))
    else:
        parts.append(f"<h3>{T['sec_setup']}</h3>")
        parts.append(_kv_table(T, [
            [T["energy"], f"{_f(a.energy, 0)} (CE = {_f(res['factors']['CE'], 3)})", "%"],
            [T["borehole"], f"{_f(a.borehole, 0)} (CB = {_f(res['factors']['CB'], 3)})", "mm"],
            [T["stickup"], _f(a.stickup), "m"], [T["rod"], yn(a.rod_correction), ""],
            [T["liner"], yn(a.no_liner), ""], [T["gravel"], yn(a.gravel_correction), ""],
        ]))

    parts.append(f"<h3>{T['sec_soil']}</h3>")
    rows = [[i, _esc(lay["name"]), _f(lay["top"]), _f(lay["bottom"]), _f(lay["gamma"], 1),
             _f(lay["gamma_sat"], 1), _f(lay["FC"], 0), _f(lay["clay"], 0),
             _f(lay["LL"], 0) if lay["LL"] > 0 else "—",
             _f(lay["PI"], 0) if lay["PI"] > 0 else "NP", _f(lay["wn"], 0),
             _f(lay["Vs"], 0) if lay["Vs"] > 0 else "—"]
            for i, lay in enumerate(a.profile.layers, 1)]
    parts.append(_table(["#", T["layer"], f"{T['top']} (m)", f"{T['bottom']} (m)", "γ",
                         L["col_gamma_sat"].split(" ")[0], "FC", L["col_clay"].split(" ")[0],
                         "LL", "PI", "wn", "Vs"], rows,
                        [3, 22, 8, 9, 6, 6, 6, 6, 6, 6, 6, 6]))
    parts.append(f"<p class='note'>{_esc(T['soil_units'])}</p>")
    parts.append(f"<p class='lead'><b>{_esc(T['layers_more'])}</b></p>")
    rows = [[i, _esc(lay["name"]), _f(lay["D50"], 3) if lay["D50"] > 0 else "—",
             _f(lay["OCR"]), _f(lay["su"], 1) if lay["su"] > 0 else "0.22·OCR^0.8·σ'v"]
            for i, lay in enumerate(a.profile.layers, 1)]
    parts.append(_table(["#", T["layer"], "D50 (mm)", "OCR", "su (kPa)"], rows,
                        [4, 40, 16, 12, 28]))

    if res["kind"] == "cpt":
        parts.append(f"<h3>{T['sec_tests_cpt']}</h3>")
        rows = [[_f(t["z"][i]), _f(t["qc"][i]), _f(t["fs_cpt"][i], 1), _f(t["u2"][i], 1),
                 _f(t["qt"][i] / 1000.0), _f(t["Ic"][i]), _f(t["FC"][i], 0),
                 _esc(a.profile.layers[t["layer"][i]]["name"])] for i in range(len(t["z"]))]
        parts.append(_table(["z (m)", "qc (MPa)", "fs (kPa)", "u2 (kPa)", "qt (MPa)", "Ic",
                             "FC (%)", T["layer"]], rows, [9, 10, 10, 10, 10, 8, 9, 34]))
    else:
        parts.append(f"<h3>{T['sec_tests']}</h3>")
        rows = [[_f(t["z"][i]), f"{t['N'][i]:g}",
                 _esc(a.profile.layers[t["layer"][i]]["name"]), _f(t["FC"][i], 0),
                 _f(t["clay"][i], 0), _f(t["LL"][i], 0) if t["LL"][i] > 0 else "—",
                 _f(t["PI"][i], 0) if t["PI"][i] > 0 else "NP", _f(t["wn"][i], 0)]
                for i in range(len(t["z"]))]
        parts.append(_table(["z (m)", "N", T["layer"], "FC (%)", L["col_clay"], "LL (%)",
                             "PI (%)", "wn (%)"], rows, [9, 7, 32, 9, 9, 9, 9, 9]))

    parts.append(f"<h3>{T['sec_opts']}</h3>")
    rows = [[T["test_type"], L["test_" + res["kind"]], ""],
            [T["method"], L["method_" + a.method], ""]]
    if res["kind"] == "spt":
        rows += [[T["susc"], L["susc_" + a.criterion], ""],
                 [T["fine"], _f(a.fine_threshold, 0), "%"],
                 [T["uncertain"], yn(a.uncertain_susceptible), ""]]
    rows += [[T["sdepth"], _f(a.settlement_depth, 1), "m"],
             [T["dry"], yn(a.dry_settlement), ""], [T["soft"], yn(a.softening), ""]]
    if a.method == "cetin2004":
        vs12 = _f(res["vs12"], 0) + (f" ({T['estimated']})" if res["vs12_estimated"] else "")
        rows += [[T["pl"], _f(a.cetin_pl, 0), "%"], [T["vs12"], vs12, "m/s"]]
    rows.append([T["geometry"], L["geometry_" + a.geometry], ""])
    if a.geometry == "slope":
        rows.append([T["slope"], _f(a.slope), "%"])
    elif a.geometry == "free_face":
        rows += [[T["face_l"], _f(a.face_length, 1), "m"], [T["face_h"], _f(a.face_height), "m"]]
    rows += [[T["fs_req"], _f(a.fs_required), ""],
             [T["s_allow"], _f(a.s_allow, 1) if a.s_allow > 0 else T["na"], "mm"]]
    parts.append(_kv_table(T, rows))

    # ---------------- 2. susceptibility
    parts.append(f"<h2>{T['sec_susc']}</h2>")
    if res["kind"] == "cpt":
        parts.append(f"<p>{_esc(T['susc_cpt'].format(ic=a.ic_limit))}</p>")
    else:
        rows = []
        for i in range(len(t["z"])):
            ratio = t["wn"][i] / t["LL"][i] if t["LL"][i] > 0 else None
            rows.append([_f(t["z"][i]), _f(t["FC"][i], 0), _f(t["clay"][i], 0),
                         _f(t["LL"][i], 0) if t["LL"][i] > 0 else "—",
                         _f(t["PI"][i], 0) if t["PI"][i] > 0 else "NP", _f(t["wn"][i], 0),
                         _f(ratio), _esc(L["class_" + t["class"][i]])])
        parts.append(_table(["z (m)", "FC (%)", L["col_clay"], "LL (%)", "PI (%)", "wn (%)",
                             "wn/LL", T["class"]], rows, [10, 10, 10, 10, 10, 10, 10, 30]))

    # ---------------- 3. triggering
    parts.append(f"<h2>{T['sec_trig']}</h2>")
    parts.append(f"<p class='lead'><b>{_esc(L['method_' + a.method])}</b></p>")
    cpt_based = res["kind"] == "cpt"
    rows = []
    for i in range(len(t["z"])):
        assessed = bool(t["assessed"][i])
        first = ([_f(t["Ic"][i]), _f(m["n1"][i], 1)] if cpt_based
                 else [_f(t["N60"][i], 1), _f(m["n1"][i], 1)])
        rows.append([_f(t["z"][i]), _f(t["sigma_v"][i], 1), _f(t["sigma_eff"][i], 1)] + first
                    + [_f(m["ncs"][i], 1), _f(m["rd"][i], 3), _f(m["csr"][i], 3),
                       _f(m["crr75"][i], 3), _f(m["msf"][i], 3), _f(m["ksigma"][i], 3),
                       _f(m["crr"][i], 3) if assessed else "—",
                       f"<b>{fs_text(m['fs'][i])}</b>" if assessed else "—",
                       _state(L, t["state"][i])])
    heads = (["Ic", "qc1N", "qc1Ncs"] if cpt_based else ["N60", "(N1)60", "(N1)60cs"])
    parts.append(_table(["z (m)", "σv (kPa)", "σ'v (kPa)"] + heads
                        + ["rd", "CSR", "CRR7.5", "MSF", "Kσ", "CRR", "FS", T["state"]], rows,
                        [6, 7, 7, 5, 6, 8, 6, 6, 7, 6, 6, 6, 6, 14]))

    # ---------------- 4. consequences
    parts.append(f"<h2>{T['sec_cons']}</h2>")
    parts.append(f"<h3>{T['sec_cons_tests']}</h3>")
    rows = []
    for i in range(len(t["z"])):
        rows.append([_f(t["z"][i]), f"{_f(t['top'][i])} – {_f(t['bot'][i])}",
                     fs_text(m["fs"][i]) if t["assessed"][i] else "—",
                     _f(100.0 * m["eps"][i]), _f(100.0 * m["gamma"][i], 1),
                     _f(t["ds"][i], 1), _f(t["ds_dry"][i], 1), _f(t["lpi"][i]),
                     _f(t["lsn"][i], 1), _f(t["ldi"][i], 3)])
    parts.append(_table(["z (m)", f"{T['interval']} (m)", "FS", "εv (%)", "γmax (%)",
                         "Δs (mm)", T["ds_dry"], "LPI", "LSN", "LDI (m)"], rows,
                        [8, 15, 8, 9, 9, 9, 11, 9, 9, 13]))

    parts.append(f"<h3>{T['sec_soft']}</h3>")
    clay = [i for i in range(len(t["z"])) if math.isfinite(t["fs_soft"][i])]
    if clay:
        rows = [[_f(t["z"][i]), _esc(a.profile.layers[t["layer"][i]]["name"]),
                 _f(t["su_ratio"][i], 3), _f(m["csr"][i], 3), _f(0.8 * t["su_ratio"][i], 3),
                 f"<b>{fs_text(t['fs_soft'][i])}</b>", _state(L, t["state"][i])] for i in clay]
        parts.append(_table(["z (m)", T["layer"], "su/σ'v", "CSR", "CRR7.5", "FS", T["state"]],
                            rows, [9, 31, 12, 11, 12, 10, 15]))
    else:
        parts.append(f"<p class='note'>{_esc(T['no_soft'])}</p>")

    parts.append(f"<h3>{T['sec_cons_total']}</h3>")
    rows = []
    if math.isfinite(res["fs_min"]):
        rows.append([T["fs_min"], f"{fs_text(res['fs_min'])} ({T['at']} "
                                  f"{_f(res['z_fs_min'])} m)", ""])
    rows += [[T["h_liq"], _f(res["h_liq"]), "m"], [T["h_soft"], _f(res["h_soft"]), "m"],
             [T["settlement_sat"], _f(res["settlement_sat"], 1), "mm"],
             [T["settlement_dry"], _f(res["settlement_dry"], 1), "mm"],
             [T["settlement"], f"<b>{_f(res['settlement'], 1)}</b>", "mm"],
             [T["lpi"], f"{_f(res['lpi'], 1)} — {_esc(L['lpi_' + res['lpi_class']])}", ""],
             [T["lsn"], f"{_f(res['lsn'], 1)} — {_esc(L['lsn_' + res['lsn_class']])}", ""],
             [T["ldi"], _f(res["ldi"], 3), "m"]]
    if a.geometry != "level":
        rows.append([T["ld"], f"<b>{_f(res['ld'])}</b>", "m"])
    parts.append(_kv_table(T, rows))

    parts.append(f"<h3>{T['sec_compare']}</h3>")
    rows = [[_esc(L["method_" + key]) + (" ◀" if key == a.method else ""),
             fs_text(c["fs_min"]), _f(c["settlement"], 1), _f(c["lpi"], 1), _f(c["ld"]),
             c["n_liq"]]
            for key, c in res["comparison"].items()]
    parts.append(_table([T["procedure"], "FS,min", "s (mm)", "LPI", "LD (m)", T["n_liq"]], rows,
                        [36, 13, 13, 12, 12, 14]))

    parts.append(f"<h3>{T['sec_checks']}</h3>")
    check_fs, check_s = res["checks"]["fs"], res["checks"]["settlement"]
    rows = [[T["c_fs"], fs_text(check_fs["actual"]), f"≥ {_f(check_fs['required'])}",
             _status(T, check_fs["status"], risk=True)],
            [T["c_s"], f"{_f(check_s['actual'], 1)} mm",
             f"≤ {_f(check_s['allowable'], 1)} mm" if check_s["status"] != "N/A" else T["na"],
             _status(T, check_s["status"])]]
    parts.append(_table([T["check"], T["actual"], T["allowable"], T["status"]], rows,
                        [40, 20, 20, 20]))

    # ---------------- 5. figures
    parts.append(f"<h2 style='page-break-before:always'>{T['sec_figs']}</h2>")
    for key in [k for k in figures if not k.startswith("study_")]:
        parts.append(f"<p class='lead'><b>{_esc(L.get(f'fig_{key}', key))}</b></p>")
        parts.append(f"<p><img src='{img_src(key)}' width='640'></p>")

    # ---------------- 6/7. warnings & notes
    if res.get("warnings"):
        parts.append(f"<h2>{T['sec_warn']}</h2><ul>")
        parts.extend(f"<li>{_esc(warning_text(lang, w))}</li>" for w in res["warnings"])
        parts.append("</ul>")
    parts.append(f"<h2>{T['sec_notes']}</h2><ul class='note'>")
    parts.extend(f"<li>{_esc(n)}</li>" for n in T["notes"])
    parts.append("</ul>")
    if study is not None and study.rows:
        parts.extend(_study_section(T, L, study, figures, img_src))
    parts.append("</body></html>")
    return "\n".join(parts)


# ----------------------------------------------------------------------
# exporters
# ----------------------------------------------------------------------
def _all_figures(analysis, lang, study):
    figures = render_figures(analysis, lang)
    figures.update(render_study_figures(study, lang))
    return figures


def export_html(path: str, analysis, lang: str, study=None) -> None:
    figures = _all_figures(analysis, lang, study)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(build_html(analysis, lang, figures, study=study))


def export_pdf(path: str, analysis, lang: str, study=None) -> None:
    """PDF through reportlab; the figures travel as `fig://<key>` references."""
    from . import pdf as pdf_writer

    T = TEXTS.get(lang, TEXTS["en"])
    info = analysis.config.get("project_info", {})
    figures = _all_figures(analysis, lang, study)
    html_text = build_html(analysis, lang, figures, img_src=lambda k: f"fig://{k}", study=study)
    pdf_writer.html_to_pdf(path, html_text, figures,
                           title=info.get("title", T["title"]),
                           author=info.get("analyst", ""),
                           footer=f"{info.get('title', '')} — {APP_NAME} v{APP_VERSION}")


def export_docx(path: str, analysis, lang: str, study=None) -> None:
    """Word report; requires python-docx."""
    try:
        import docx
        from docx.shared import Inches, Pt
    except ImportError as exc:
        raise RuntimeError("python-docx is not installed (pip install python-docx).") from exc
    import re

    figures = _all_figures(analysis, lang, study)
    html_text = build_html(analysis, lang, figures, img_src=lambda k: f"fig://{k}", study=study)
    d = docx.Document()
    from docx.shared import RGBColor
    d.styles["Normal"].font.size = Pt(10)
    d.styles["Normal"].font.color.rgb = RGBColor(0x14, 0x14, 0x13)
    # the interface's look: serif headings, the title in ink, sections in terracotta
    for name, colour in (("Title", (0x14, 0x14, 0x13)), ("Heading 1", (0xC6, 0x61, 0x3F)),
                         ("Heading 2", (0x14, 0x14, 0x13))):
        style = d.styles[name]
        style.font.name = "Georgia"
        style.font.bold = False
        style.font.color.rgb = RGBColor(*colour)

    # a small HTML -> docx walker (headings, paragraphs, tables, lists, images)
    tokens = re.split(r"(<h1>.*?</h1>|<h2[^>]*>.*?</h2>|<h3>.*?</h3>|<table[^>]*>.*?</table>|"
                      r"<p[^>]*>.*?</p>|<li>.*?</li>)", html_text, flags=re.S)

    def strip(s):
        return html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "\n", s))).strip()

    for tok in tokens:
        if tok.startswith("<h1>"):
            d.add_heading(strip(tok), level=0)
        elif tok.startswith("<h2"):
            d.add_heading(strip(tok), level=1)
        elif tok.startswith("<h3>"):
            d.add_heading(strip(tok), level=2)
        elif tok.startswith("<li>"):
            d.add_paragraph(strip(tok), style="List Bullet")
        elif tok.startswith("<table"):
            rows = re.findall(r"<tr>(.*?)</tr>", tok, flags=re.S)
            cells = [re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, flags=re.S) for r in rows]
            if cells:
                table = d.add_table(rows=len(cells), cols=len(cells[0]))
                table.style = "Light Grid Accent 1"
                for i, row in enumerate(cells):
                    for j, c in enumerate(row):
                        if j < len(table.columns):
                            table.cell(i, j).text = strip(c)
        elif tok.startswith("<p"):
            m = re.search(r"src='fig://([a-z_]+)'", tok)
            if m:
                d.add_picture(io.BytesIO(figures[m.group(1)]), width=Inches(6.3))
            else:
                text = strip(tok)
                if text:
                    d.add_paragraph(text)
    d.save(path)


def export_report(path: str, analysis, lang: str, study=None) -> None:
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        export_pdf(path, analysis, lang, study)
    elif ext == "docx":
        export_docx(path, analysis, lang, study)
    else:
        export_html(path if ext in ("html", "htm") else path + ".html", analysis, lang, study)
