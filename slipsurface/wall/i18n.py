"""
Every text of SlipSurface IQ Wall, in English and Turkish.

Each entry is written once as ``key: (English, Turkish)`` so the two languages
cannot drift apart: a key without its translation is a syntax error, not a
blank on the screen. `TRANSLATIONS[lang][key]` is how the rest of the program
reads them.
"""

from __future__ import annotations

ENTRIES = {
    # ------------------------------------------------------------------ input errors
    "err_height": ("The wall height must be greater than zero.",
                   "Duvar yüksekliği sıfırdan büyük olmalıdır."),
    "err_stem": ("The stem needs a thickness at the top, and at least as much at its base.",
                 "Gövdenin tepede bir kalınlığı olmalı, tabanda en az bu kadar olmalıdır."),
    "err_footing": ("The footing needs a thickness, and the stem at least 0.3 m of height "
                    "above it.",
                    "Temelin bir kalınlığı olmalı ve gövde temelin üstünde en az 0.3 m "
                    "yükselmelidir."),
    "err_toe_heel": ("The toe and the heel cannot be negative.",
                     "Ön ve arka ampatman boyu negatif olamaz."),
    "err_cover": ("The soil over the toe must be positive and end below the top of the wall.",
                  "Ön ampatman üzerindeki zemin pozitif olmalı ve duvar tepesinin altında "
                  "kalmalıdır."),
    "err_backslope": ("The backslope must be positive and flatter than the friction angle of "
                      "the backfill ({phi:.1f}°).",
                      "Arka şev açısı pozitif ve geri dolgunun içsel sürtünme açısından "
                      "({phi:.1f}°) küçük olmalıdır."),
    "err_toe_slope": ("The slope in front of the wall must be between 0 and 45°.",
                      "Duvar önündeki şev açısı 0 ile 45° arasında olmalıdır."),
    "err_gamma": ("{soil}: the unit weight must be greater than zero.",
                  "{soil}: birim hacim ağırlık sıfırdan büyük olmalıdır."),
    "err_phi": ("{soil}: the friction angle must be between 0 and 60°.",
                "{soil}: içsel sürtünme açısı 0 ile 60° arasında olmalıdır."),
    "err_cohesion": ("{soil}: the cohesion cannot be negative.",
                     "{soil}: kohezyon negatif olamaz."),
    "err_gamma_sat": ("{soil}: the saturated unit weight must exceed γw.",
                      "{soil}: doygun birim hacim ağırlık γw'den büyük olmalıdır."),
    "err_backfill_phi": ("The backfill needs a friction angle.",
                         "Geri dolgunun içsel sürtünme açısı olmalıdır."),
    "err_foundation_strength": ("The foundation soil has no strength: enter c' and φ', or cu "
                                "with φ = 0.",
                                "Temel zemininin dayanımı yok: c' ve φ' ya da φ = 0 ile cu "
                                "giriniz."),
    "err_gamma_concrete": ("The unit weight of concrete must be greater than zero.",
                           "Betonun birim hacim ağırlığı sıfırdan büyük olmalıdır."),
    "err_water": ("The water levels must lie between the base and the top of the wall, and the "
                  "water table below the base cannot be negative.",
                  "Su seviyeleri taban ile duvar tepesi arasında olmalı, tabanın altındaki su "
                  "tablası derinliği negatif olamaz."),
    "err_key": ("The shear key needs a depth and a width, and must lie under the footing.",
                "Kayma dişinin derinliği ve genişliği olmalı, diş temelin altında kalmalıdır."),
    "err_ratios": ("δ/φ and the share of the passive resistance must be between 0 and 1.",
                   "δ/φ ve pasif direnç payı 0 ile 1 arasında olmalıdır."),
    "err_base_ratios": ("The base friction ratio must be between 0 and 1, the adhesion ratio "
                        "between 0 and 1.",
                        "Taban sürtünme oranı 0 ile 1, adezyon oranı 0 ile 1 arasında "
                        "olmalıdır."),
    "err_ocr": ("The overconsolidation ratio cannot be below 1.",
                "Aşırı konsolidasyon oranı 1'den küçük olamaz."),
    "err_loads": ("The loads and the allowable pressure cannot be negative.",
                  "Yükler ve zemin emniyet gerilmesi negatif olamaz."),
    "err_seismic": ("The earthquake needs Ss, S1 ≥ 0, a site class ZA–ZE, kh < 1, kv / kh and ψ "
                    "between 0 and 1, and the dynamic increment between 1/3 and 2/3 of the "
                    "height.",
                    "Deprem için Ss, S1 ≥ 0, ZA–ZE yerel zemin sınıfı, kh < 1, 0 ile 1 arasında "
                    "kv / kh ve ψ, ve yüksekliğin 1/3'ü ile 2/3'ü arasında dinamik artış "
                    "noktası gerekir."),
    "err_material": ("Unknown concrete class or steel grade.",
                     "Bilinmeyen beton sınıfı veya donatı çeliği."),
    "err_cover_concrete": ("The clear covers must be positive and leave room for the bars in "
                           "the stem and the footing.",
                           "Net paspayları pozitif olmalı ve gövde ile temelde donatıya yer "
                           "bırakmalıdır."),
    "err_pressure": ("The earth pressure could not be worked out for these angles.",
                     "Bu açılar için toprak basıncı hesaplanamadı."),

    # ------------------------------------------------------------------ warnings
    "warn_mo_limited": ("The seismic angle and the backslope together exceed the friction angle: "
                        "Mononobe–Okabe has no real solution and its limiting value is used — the "
                        "backfill itself is at failure under this acceleration.",
                        "Deprem açısı ile arka şev birlikte içsel sürtünme açısını aşıyor: "
                        "Mononobe–Okabe'nin gerçek çözümü yok, sınır değeri kullanıldı — geri "
                        "dolgu bu ivme altında kendisi göçme durumunda."),
    "warn_water_seismic": ("Water stands behind or in front of the wall: the hydrodynamic "
                           "pressure of the water in an earthquake is not included.",
                           "Duvarın arkasında veya önünde su var: depremde suyun hidrodinamik "
                           "basıncı hesaba katılmadı."),
    "warn_global_none": ("No slip circle passing under the wall could be found; the global "
                         "stability was not checked.",
                         "Duvarın altından geçen bir kayma dairesi bulunamadı; genel duraylılık "
                         "kontrol edilemedi."),
    "warn_design": ("At least one member does not pass: make the section thicker or the "
                    "concrete stronger.",
                    "En az bir eleman sağlamıyor: kesiti kalınlaştırın veya beton sınıfını "
                    "yükseltin."),
    "warn_footing_unstable": ("The resultant leaves the base in {combos}: the footing is "
                              "designed for the other combinations, and the wall must first be "
                              "made stable.",
                              "{combos} birleşiminde bileşke tabanın dışına çıkıyor: temel diğer "
                              "birleşimlere göre tasarlandı; önce duvarın duraylılığı "
                              "sağlanmalıdır."),
    "warn_cohesion_ignored": ("The cohesion of the backfill is left out: only Rankine's "
                              "pressure takes it.",
                              "Geri dolgunun kohezyonu dikkate alınmadı: yalnızca Rankine "
                              "basıncı hesaba katar."),
    "warn_cohesion_backfill": ("The cohesion of the backfill lowers the earth pressure; a "
                               "backfill is usually taken as cohesionless, since its cohesion "
                               "is lost when it is wetted or disturbed.",
                               "Geri dolgunun kohezyonu toprak basıncını azaltıyor; dolgu "
                               "genellikle kohezyonsuz alınır, çünkü kohezyon ıslanma veya "
                               "örselenmeyle kaybolur."),
    "warn_passive_slope": ("The ground in front slopes away, but Rankine's passive coefficient "
                           "is for level ground: the passive resistance is overestimated; "
                           "Coulomb's takes the slope.",
                           "Önündeki zemin eğimli, ancak Rankine pasif katsayısı yatay zemin "
                           "içindir: pasif direnç fazla bulunur; Coulomb eğimi hesaba katar."),
    "warn_key_passive": ("A shear key works through the passive resistance in front of it, so "
                         "that resistance is counted (with the share given) although the "
                         "passive option is off.",
                         "Kayma dişi önündeki pasif dirençle çalışır; bu nedenle pasif seçeneği "
                         "kapalı olsa da bu direnç (verilen payla) hesaba katıldı."),
    "warn_uplift_base": ("The resultant lies outside the middle third: part of the base lifts "
                         "off the ground.",
                         "Bileşke orta üçte birin dışında: tabanın bir kısmı zeminden "
                         "ayrılıyor."),
    "warn_water": ("The water table is {dw:.2f} m below the base, within the foundation's "
                   "failure zone; the self-weight term uses a reduced unit weight.",
                   "Su tablası tabanın {dw:.2f} m altında, temelin göçme bölgesi içinde; zati "
                   "ağırlık terimi azaltılmış birim hacim ağırlıkla hesaplandı."),
    "warn_undrained": ("The foundation soil is analysed undrained (φ = 0): sliding and bearing "
                       "rest on cu alone.",
                       "Temel zemini drenajsız (φ = 0) çözüldü: kayma ve taşıma gücü yalnızca "
                       "cu'ya dayanıyor."),
    "warn_thin_stem": ("The stem is thinner than 0.20 m at the top: hard to cast and to "
                       "reinforce on two faces.",
                       "Gövde tepede 0.20 m'den ince: dökülmesi ve iki yüzden donatılması "
                       "güç."),
    "warn_narrow_base": ("The base is only {ratio:.2f}·H wide; a cantilever wall usually needs "
                         "0.5–0.7·H.",
                         "Taban yalnızca {ratio:.2f}·H genişliğinde; konsol duvar genellikle "
                         "0.5–0.7·H ister."),
    "warn_live_on_slope": ("A live surcharge is applied on a sloping backfill; check that "
                           "traffic can in fact reach it.",
                           "Eğimli geri dolguya hareketli sürşarj uygulandı; trafiğin gerçekten "
                           "oraya erişip erişmediğini kontrol ediniz."),
    "warn_at_rest_mo": ("The pressure at rest is for a wall that cannot yield; Wood's dynamic "
                        "thrust suits it better than Mononobe–Okabe's.",
                        "Sükûnetteki basınç yer değiştiremeyen duvar içindir; onunla Wood "
                        "dinamik itkisi Mononobe–Okabe'den daha uyumludur."),

    # ------------------------------------------------------------------ names
    "soil_backfill": ("Backfill", "Geri dolgu"),
    "soil_foundation": ("Foundation soil", "Temel zemini"),
    "pm_rankine": ("Rankine", "Rankine"),
    "pm_coulomb": ("Coulomb", "Coulomb"),
    "pm_at_rest": ("At rest (K0)", "Sükûnette (K0)"),
    "pm_trial_wedge": ("Trial wedge", "Deneme kaması"),
    "pm_mononobe_okabe": ("Mononobe–Okabe (KAE)", "Mononobe–Okabe (KAE)"),
    "pm_mo_increment": ("Mononobe–Okabe: KAE, P = ΔPAE", "Mononobe–Okabe: KAE, P = ΔPAE"),
    "pp_rankine": ("Rankine passive (Kp)", "Rankine pasif (Kp)"),
    "pp_coulomb": ("Coulomb passive (Kp)", "Coulomb pasif (Kp)"),
    "method_vesic": ("Vesić (1973)", "Vesić (1973)"),
    "method_meyerhof": ("Meyerhof (1963)", "Meyerhof (1963)"),
    "method_hansen": ("Brinch Hansen (1970)", "Brinch Hansen (1970)"),
    "method_terzaghi": ("Terzaghi (1943)", "Terzaghi (1943)"),
    "method_ec7": ("EN 1997-1 Annex D", "EN 1997-1 Ek D"),
    "sm_mononobe_okabe": ("Mononobe–Okabe", "Mononobe–Okabe"),
    "sm_seed_whitman": ("Seed–Whitman (ΔKAE = ¾·kh)", "Seed–Whitman (ΔKAE = ¾·kh)"),
    "sm_wood": ("Wood (unyielding wall)", "Wood (yer değiştiremeyen duvar)"),
    "taper_back": ("back face (earth side)", "arka yüz (toprak tarafı)"),
    "taper_front": ("front face", "ön yüz"),
    "site_ZA": ("ZA — hard rock", "ZA — sağlam, sert kaya"),
    "site_ZB": ("ZB — rock", "ZB — az ayrışmış, orta sağlam kaya"),
    "site_ZC": ("ZC — very dense soil, soft rock", "ZC — çok sıkı kum, çakıl, sert kil, "
                                                   "ayrışmış kaya"),
    "site_ZD": ("ZD — medium dense soil, stiff clay", "ZD — orta sıkı kum, çakıl, çok katı "
                                                      "kil"),
    "site_ZE": ("ZE — loose sand, soft clay", "ZE — gevşek kum, çakıl, yumuşak-katı kil"),
    "mob_rigid": ("cannot move (βr = 1)", "yer değiştiremez (βr = 1)"),
    "mob_free_200": ("may move 200·(0.4·SDS) mm (βr = 0.67)",
                     "200·(0.4·SDS) mm yer değiştirebilir (βr = 0.67)"),
    "mob_free_300": ("may move 300·(0.4·SDS) mm (βr = 0.5)",
                     "300·(0.4·SDS) mm yer değiştirebilir (βr = 0.5)"),
    "kv_up": ("kv upward", "kv yukarı"),
    "kv_down": ("kv downward", "kv aşağı"),
    "factor_depth": ("depth d", "derinlik d"),
    "factor_inclination": ("inclination i", "eğim i"),
    "factor_ground": ("ground slope g", "zemin eğimi g"),
    "bar_auto": ("chosen by the program", "program seçsin"),

    # ------------------------------------------------------------------ members and bars
    "member_stem": ("Stem, base (back face)", "Gövde, taban (arka yüz)"),
    "member_toe": ("Footing, bottom (toe)", "Temel, alt (ön ampatman)"),
    "member_heel": ("Footing, top (heel)", "Temel, üst (arka ampatman)"),
    "member_key": ("Shear key", "Kayma dişi"),
    "member_stem_front": ("Stem, front face (minimum)", "Gövde, ön yüz (minimum)"),
    "member_stem_horizontal": ("Stem, horizontal (each face)", "Gövde, yatay (her yüz)"),
    "member_footing_long": ("Footing, along the wall (each face)",
                            "Temel, duvar boyunca (her yüz)"),
    "bar_stem_back_full": ("Stem, back face, full height", "Gövde arka yüz, tam boy"),
    "bar_stem_back_cut": ("Stem, back face, curtailed", "Gövde arka yüz, kesilen"),
    "bar_stem_front": ("Stem, front face", "Gövde ön yüz"),
    "bar_stem_horizontal": ("Stem, horizontal", "Gövde yatay"),
    "bar_footing_bottom": ("Footing, bottom", "Temel alt"),
    "bar_footing_top": ("Footing, top", "Temel üst"),
    "bar_footing_long": ("Footing, along the wall", "Temel boyuna"),
    "bar_key": ("Shear key, U-bars", "Kayma dişi, U etriye"),
    "bar_key_long": ("Shear key, along the wall", "Kayma dişi boyuna"),

    # ------------------------------------------------------------------ forces
    "force_W_stem": ("Weight of the stem", "Gövde ağırlığı"),
    "force_W_footing": ("Weight of the footing", "Temel ağırlığı"),
    "force_W_key": ("Weight of the key", "Diş ağırlığı"),
    "force_W_heel_soil": ("Soil on the heel", "Topuk üzerindeki zemin"),
    "force_W_toe_soil": ("Soil on the toe", "Ön ampatman üzerindeki zemin"),
    "force_Q_dead": ("Permanent surcharge on the heel", "Topukta kalıcı sürşarj"),
    "force_Q_live": ("Live surcharge on the heel", "Topukta hareketli sürşarj"),
    "force_P_top": ("Line load on the stem", "Gövdeye çizgisel yük"),
    "force_H_top": ("Horizontal load at the top", "Tepede yatay yük"),
    "force_Pa_h": ("Earth pressure, horizontal", "Toprak itkisi, yatay"),
    "force_Pa_v": ("Earth pressure, vertical", "Toprak itkisi, düşey"),
    "force_Pq_dead_h": ("Permanent surcharge thrust, horizontal",
                        "Kalıcı sürşarj itkisi, yatay"),
    "force_Pq_dead_v": ("Permanent surcharge thrust, vertical", "Kalıcı sürşarj itkisi, düşey"),
    "force_Pq_live_h": ("Live surcharge thrust, horizontal", "Hareketli sürşarj itkisi, yatay"),
    "force_Pq_live_v": ("Live surcharge thrust, vertical", "Hareketli sürşarj itkisi, düşey"),
    "force_Pw_back": ("Water behind the wall", "Duvar arkasındaki su"),
    "force_Pw_front": ("Water in front of the wall", "Duvar önündeki su"),
    "force_U": ("Uplift under the base", "Taban altı su kaldırması"),
    "force_E_inertia": ("Inertia kh·W", "Atalet kh·W"),
    "force_E_vertical": ("Vertical inertia kv·W", "Düşey atalet kv·W"),
    "force_dPAE_h": ("Dynamic increment ΔPAE, horizontal", "Dinamik artış ΔPAE, yatay"),
    "force_dPAE_v": ("Dynamic increment ΔPAE, vertical", "Dinamik artış ΔPAE, düşey"),

    # ------------------------------------------------------------------ form groups
    "group_project": ("Project", "Proje"),
    "title_label": ("Title", "Başlık"),
    "analyst_label": ("Analyst", "Hazırlayan"),
    "group_geometry": ("Wall geometry", "Duvar geometrisi"),
    "H_label": ("Height H (underside of footing to top)", "Yükseklik H (temel altından tepeye)"),
    "t_top_label": ("Stem thickness at the top", "Gövde kalınlığı, tepede"),
    "t_bot_label": ("Stem thickness at the base", "Gövde kalınlığı, tabanda"),
    "taper_label": ("Inclined face of the stem", "Gövdenin eğik yüzü"),
    "toe_label": ("Toe length", "Ön ampatman boyu"),
    "heel_label": ("Heel length", "Arka ampatman (topuk) boyu"),
    "t_f_label": ("Footing thickness", "Temel kalınlığı"),
    "D_label": ("Soil over the toe", "Ön ampatman üzerindeki zemin"),
    "backslope_label": ("Backslope β", "Arka şev açısı β"),
    "toe_slope_label": ("Slope of the ground in front", "Öndeki zeminin eğimi"),
    "geometry_note": ("Per metre run. H runs from the underside of the footing to the top of "
                      "the stem; the base is toe + stem + heel wide. The backfill starts at the "
                      "top of the stem.",
                      "Metre başına. H temel altından gövde tepesine ölçülür; taban ön ampatman "
                      "+ gövde + arka ampatman genişliğindedir. Geri dolgu gövde tepesinden "
                      "başlar."),
    "group_key": ("Shear key", "Kayma dişi"),
    "key_enabled_label": ("A shear key under the footing", "Temel altında kayma dişi"),
    "key_depth_label": ("Depth below the base", "Tabandan derinlik"),
    "key_width_label": ("Width", "Genişlik"),
    "key_offset_label": ("From the front of the footing", "Temelin ön ucundan uzaklık"),
    "key_note": ("The key resists sliding through the passive resistance in front of it, down "
                 "to its bottom.",
                 "Diş, altına kadar önündeki pasif dirençle kaymaya karşı koyar."),
    "group_loads": ("Loads", "Yükler"),
    "q_dead_label": ("Permanent surcharge on the backfill", "Dolguda kalıcı sürşarj"),
    "q_live_label": ("Live surcharge on the backfill", "Dolguda hareketli sürşarj"),
    "P_top_label": ("Vertical line load on the stem", "Gövdeye düşey çizgisel yük"),
    "H_top_label": ("Horizontal load at the top of the stem", "Gövde tepesinde yatay yük"),
    "loads_note": ("The live surcharge (traffic) never helps: it is left out of sliding and "
                   "overturning where it rests on the heel.",
                   "Hareketli sürşarj (trafik) hiçbir zaman yardımcı sayılmaz: topuk üzerindeki "
                   "kısmı kayma ve devrilmede alınmaz."),
    "group_backfill": ("Backfill", "Geri dolgu"),
    "group_foundation": ("Foundation soil (and soil in front)", "Temel zemini (ve öndeki zemin)"),
    "gamma_label": ("Unit weight γ", "Birim hacim ağırlık γ"),
    "gamma_sat_label": ("Saturated unit weight γsat", "Doygun birim hacim ağırlık γdoy"),
    "phi_label": ("Friction angle φ'", "İçsel sürtünme açısı φ'"),
    "c_label": ("Cohesion c' (cu with φ = 0)", "Kohezyon c' (φ = 0 ile cu)"),
    "backfill_note": ("A granular, drained backfill is the rule behind a cantilever wall.",
                      "Konsol duvar arkasında kural olarak granüler ve drene bir dolgu "
                      "kullanılır."),
    "foundation_note": ("For an undrained analysis enter φ = 0 and cu as the cohesion. The soil "
                        "over the toe and in front of the wall is taken with these properties.",
                        "Drenajsız çözüm için φ = 0 ve kohezyon olarak cu giriniz. Ön ampatman "
                        "üzerindeki ve duvar önündeki zemin bu özelliklerle alınır."),
    "group_water": ("Water", "Su"),
    "water_back_label": ("Water behind the wall, above the base", "Duvar arkasında su, tabandan"),
    "water_front_label": ("Water in front, above the base", "Önde su, tabandan"),
    "water_depth_label": ("Water table below the base (no water above)",
                          "Tabandan su tablası derinliği (üstte su yoksa)"),
    "gamma_water_label": ("Unit weight of water γw", "Suyun birim hacim ağırlığı γw"),
    "water_note": ("0 above the base means a drained wall. Water behind pushes and lifts the "
                   "base; below the water the soil counts buoyant.",
                   "Tabanın üstünde 0, drene duvar demektir. Arkadaki su iter ve tabanı "
                   "kaldırır; su altında zemin batık alınır."),
    "group_earth": ("Earth pressure", "Toprak basıncı"),
    "method_label": ("Method on the virtual back", "Sanal arka yüzde yöntem"),
    "delta_ratio_label": ("Wall friction δ/φ", "Duvar sürtünmesi δ/φ"),
    "OCR_label": ("Overconsolidation ratio OCR", "Aşırı konsolidasyon oranı OCR"),
    "passive_label": ("Count the passive resistance in front", "Öndeki pasif direnci hesaba kat"),
    "passive_method_label": ("Passive coefficient", "Pasif katsayı"),
    "passive_ratio_label": ("Share of the passive counted", "Hesaba katılan pasif payı"),
    "earth_note": ("Every method is computed for comparison; the one chosen here is used for "
                   "the checks and the stem. The passive resistance is often left out, or "
                   "halved, since it needs movement to develop.",
                   "Karşılaştırma için bütün yöntemler hesaplanır; burada seçilen kontrollerde "
                   "ve gövdede kullanılır. Pasif direnç, oluşması için yer değiştirme gerektiği "
                   "için çoğu kez dikkate alınmaz veya yarıya indirilir."),
    "group_stability": ("Stability and bearing", "Duraylılık ve taşıma gücü"),
    "base_friction_label": ("Base friction δb/φ", "Taban sürtünmesi δb/φ"),
    "base_adhesion_label": ("Base adhesion ca/c", "Taban adezyonu ca/c"),
    "bearing_method_label": ("Bearing capacity factors", "Taşıma gücü katsayıları"),
    "bearing_embedment_label": ("Count the embedment as a surcharge",
                                "Gömülmeyi sürşarj olarak hesaba kat"),
    "bearing_inclination_label": ("Load inclination factors", "Yük eğim katsayıları"),
    "bearing_depth_label": ("Depth factors", "Derinlik katsayıları"),
    "q_allow_label": ("Allowable soil pressure (0 = none)", "Zemin emniyet gerilmesi (0 = yok)"),
    "global_enabled_label": ("Search the slip circles (global stability)",
                             "Kayma dairelerini ara (genel duraylılık)"),
    "stability_note": ("δb = 2/3·φ is the usual base friction (EN 1997-1 allows δ = φ for "
                       "concrete cast against the soil). An allowable pressure from the "
                       "geotechnical report is checked against the peak of the base pressure.",
                       "Taban sürtünmesi için genellikle δb = 2/3·φ alınır (EN 1997-1 zemine "
                       "karşı dökülen betonda δ = φ'ye izin verir). Zemin etüt raporundaki "
                       "emniyet gerilmesi taban basıncının en büyük değeriyle karşılaştırılır."),
    "group_criteria": ("Required factors of safety (static)", "Gerekli güvenlik sayıları (statik)"),
    "FS_sliding_label": ("Sliding", "Kayma"),
    "FS_overturning_label": ("Overturning", "Devrilme"),
    "ecc_label": ("Eccentricity: e ≤ B / …", "Dışmerkezlik: e ≤ B / …"),
    "FS_bearing_label": ("Bearing capacity", "Taşıma gücü"),
    "FS_global_label": ("Global stability", "Genel duraylılık"),
    "criteria_note": ("Common practice: sliding 1.5, overturning 2.0 (1.5 on rock), e ≤ B/6, "
                      "bearing 3.0, global 1.5.",
                      "Yaygın uygulama: kayma 1.5, devrilme 2.0 (kayada 1.5), e ≤ B/6, taşıma "
                      "gücü 3.0, genel duraylılık 1.5."),
    "group_seismic": ("Earthquake (TBDY 2018)", "Deprem (TBDY 2018)"),
    "seismic_enabled_label": ("Check the wall under an earthquake", "Duvarı depremde kontrol et"),
    "Ss_label": ("Short-period map acceleration Ss", "Kısa periyot harita ivmesi Ss"),
    "S1_label": ("1-second map acceleration S1", "1 saniye harita ivmesi S1"),
    "site_label": ("Local site class", "Yerel zemin sınıfı"),
    "mobility_label": ("Displacement of the wall", "Duvarın yer değiştirmesi"),
    "kh_manual_label": ("kh given directly (0 = from TBDY)", "Doğrudan kh (0 = TBDY'den)"),
    "kv_ratio_label": ("kv / kh", "kv / kh"),
    "seismic_method_label": ("Dynamic thrust", "Dinamik itki"),
    "dyn_height_label": ("Dynamic increment acts at … · h", "Dinamik artışın etkime noktası … · h"),
    "psi_live_label": ("Share of the live load ψ", "Hareketli yük payı ψ"),
    "seismic_note": ("Ss and S1 from the AFAD hazard map (DD-2 unless the project says "
                     "otherwise). kh = βr·0.4·SDS; βr = 1 for a wall that cannot move "
                     "(EN 1998-5 puts flexural RC walls here), 0.67 or 0.5 when the stated "
                     "displacement is acceptable. kv acts up and down; the worse governs.",
                     "Ss ve S1 AFAD tehlike haritasından (proje aksini söylemedikçe DD-2). "
                     "kh = βr·0.4·SDS; βr yer değiştiremeyen duvarda 1 (EN 1998-5 eğilmeye "
                     "çalışan betonarme duvarları buraya koyar), belirtilen yer değiştirme "
                     "kabul edilebiliyorsa 0.67 veya 0.5. kv yukarı ve aşağı alınır; elverişsiz "
                     "olan belirleyicidir."),
    "group_criteria_seis": ("Required factors of safety (earthquake)",
                            "Gerekli güvenlik sayıları (deprem)"),
    "criteria_seis_note": ("TBDY 2018 §16.7: sliding γRh = 1.1, bearing γRv = 1.4 for shallow "
                           "foundations; e ≤ B/3.",
                           "TBDY 2018 §16.7 yüzeysel temeller: kayma γRh = 1.1, taşıma gücü "
                           "γRv = 1.4; e ≤ B/3."),
    "group_concrete": ("Reinforced concrete (TS 500)", "Betonarme (TS 500)"),
    "grade_label": ("Concrete class", "Beton sınıfı"),
    "steel_label": ("Reinforcing steel", "Donatı çeliği"),
    "gamma_concrete_label": ("Unit weight of concrete", "Betonun birim hacim ağırlığı"),
    "cover_stem_label": ("Clear cover of the stem", "Gövde net paspayı"),
    "cover_footing_label": ("Clear cover of the footing", "Temel net paspayı"),
    "bar_stem_label": ("Main bar of the stem", "Gövde ana donatısı"),
    "bar_footing_label": ("Main bar of the footing", "Temel ana donatısı"),
    "rho_min_label": ("Minimum ratio of the main steel ρmin (on b·h)",
                      "Ana donatı en küçük oranı ρmin (b·h üzerinden)"),
    "rho_front_label": ("Minimum ratio, front face of the stem", "Gövde ön yüzü en küçük oranı"),
    "rho_dist_label": ("Minimum distribution ratio (both faces)",
                       "En küçük dağıtma oranı (iki yüz toplam)"),
    "curtail_label": ("Stop half the stem bars where they are not needed",
                      "Gövde donatısının yarısını gerekmediği yerde kes"),
    "concrete_note": ("TS 500: ρmin = 0.002 for one-way slabs of S420/S500; the distribution "
                      "steel at least a fifth of the main steel; the main bars at most "
                      "min(1.5·h, 200 mm) apart.",
                      "TS 500: tek doğrultuda çalışan plakta S420/S500 için ρmin = 0.002; "
                      "dağıtma donatısı ana donatının en az beşte biri; ana donatı aralığı en "
                      "çok min(1.5·h, 200 mm)."),

    # ------------------------------------------------------------------ checks and cards
    "chk_sliding": ("Sliding", "Kayma"),
    "chk_overturning": ("Overturning", "Devrilme"),
    "chk_eccentricity": ("Eccentricity", "Dışmerkezlik"),
    "chk_bearing": ("Bearing capacity", "Taşıma gücü"),
    "chk_allowable": ("Allowable pressure (q_allow / q_max)",
                      "Emniyet gerilmesi (q_em / q_maks)"),
    "chk_global": ("Global stability (Bishop)", "Genel duraylılık (Bishop)"),
    "chk_global_fellenius": ("Global stability (Fellenius)", "Genel duraylılık (Fellenius)"),
    "card_sliding": ("Sliding", "Kayma"),
    "card_overturning": ("Overturning", "Devrilme"),
    "card_eccentricity": ("Eccentricity", "Dışmerkezlik"),
    "card_bearing": ("Bearing capacity", "Taşıma gücü"),
    "card_global": ("Global stability", "Genel duraylılık"),
    "card_global_off": ("not searched", "aranmadı"),
    "card_stem": ("Stem", "Gövde"),
    "card_toe": ("Footing, bottom", "Temel, alt"),
    "card_heel": ("Footing, top", "Temel, üst"),
    "card_heel_length": ("Heel needed", "Gereken topuk"),
    "card_heel_sub": ("the wall has {heel:.2f} m", "duvarda {heel:.2f} m"),
    "card_seismic": ("Earthquake", "Deprem"),
    "card_seismic_sub": ("{n} of {total} checks hold · kh = {kh:.3f}",
                         "{total} kontrolün {n} tanesi sağlanıyor · kh = {kh:.3f}"),
    "card_none": ("none", "yok"),
    "ok_short": ("OK", "UYGUN"),
    "notok_short": ("NOT OK", "UYGUN DEĞİL"),
    "na_short": ("n/a", "—"),
    "info_short": ("for comparison", "karşılaştırma"),
    "value_FS": ("FS", "GS"),

    # ------------------------------------------------------------------ table heads
    "head_method": ("Method", "Yöntem"),
    "head_pmethod": ("Method", "Yöntem"),
    "head_Nc": ("Nc", "Nc"),
    "head_Nq": ("Nq", "Nq"),
    "head_Ng": ("Nγ", "Nγ"),
    "head_qult": ("q_ult kPa", "q_ult kPa"),
    "head_qallow": ("q_ult / FS kPa", "q_ult / GS kPa"),
    "head_P": ("P kN/m", "P kN/m"),
    "head_Ph": ("Ph kN/m", "Ph kN/m"),
    "head_Pv": ("Pv kN/m", "Pv kN/m"),
    "head_force": ("Force", "Kuvvet"),
    "head_V": ("V kN/m", "V kN/m"),
    "head_H": ("H kN/m", "H kN/m"),
    "head_arm": ("Arm m", "Kol m"),
    "head_moment": ("M about the toe kNm/m", "Ön uca göre M kNm/m"),
    "head_member": ("Section", "Kesit"),
    "head_As_req": ("As req. mm²", "As gerekli mm²"),
    "head_As_min": ("As min mm²", "As min mm²"),
    "head_bars": ("Bars", "Donatı"),
    "head_As_prov": ("As prov. mm²", "As mevcut mm²"),
    "head_combo": ("Comb.", "Birl."),
    "head_status": ("Status", "Durum"),
    "head_parameter": ("Parameter", "Parametre"),
    "head_value": ("Value", "Değer"),
    "tb_site": ("Local site class", "Yerel zemin sınıfı"),
    "tb_beta_r": ("Displacement factor βr", "Yer değiştirme katsayısı βr"),
    "tb_method": ("Dynamic thrust", "Dinamik itki"),
    "tb_dP": ("Dynamic increment ΔPAE", "Dinamik artış ΔPAE"),
    "tb_inertia": ("Inertia of wall and soil kh·W", "Duvar ve zemin ataleti kh·W"),
    "tb_governing": ("Governing kv", "Belirleyici kv"),
    "sch_pos": ("Pos.", "Poz"),
    "sch_name": ("Bar", "Donatı"),
    "sch_spacing": ("s mm", "s mm"),
    "sch_shape": ("Shape (lengths in m)", "Şekil (boylar m)"),
    "sch_length": ("Length m", "Boy m"),
    "sch_count": ("Number /m", "Adet /m"),
    "sch_total": ("Total m", "Toplam m"),
    "sch_unit": ("kg/m", "kg/m"),
    "sch_mass": ("Mass kg", "Ağırlık kg"),
    "sch_sum": ("Steel per metre of wall", "Duvarın metresi başına çelik"),
    "sch_along": ("runs along the wall", "duvar boyunca"),
    "sch_per_metre": ("per metre of wall", "duvarın metresi başına"),
    "sch_totals": ("Concrete {v:.3f} m³/m · {r:.0f} kg/m³",
                   "Beton {v:.3f} m³/m · {r:.0f} kg/m³"),

    # ------------------------------------------------------------------ drawing
    "drw_title": ("SECTION — REINFORCEMENT", "KESİT — DONATI"),
    "drw_materials": ("{grade} / {steel} · clear cover: stem {cs:.0f} mm, footing {cf:.0f} mm · "
                      "dimensions in m",
                      "{grade} / {steel} · net paspayı: gövde {cs:.0f} mm, temel {cf:.0f} mm · "
                      "ölçüler m"),
    "drw_quantities": ("Per metre of wall: concrete {v:.3f} m³, steel {s:.1f} kg "
                       "({r:.0f} kg/m³)",
                       "Duvarın metresi başına: beton {v:.3f} m³, çelik {s:.1f} kg "
                       "({r:.0f} kg/m³)"),

    # ------------------------------------------------------------------ results text
    "res_title": ("CANTILEVER RETAINING WALL — RESULTS", "KONSOL İSTİNAT DUVARI — SONUÇLAR"),
    "res_wall": ("Wall: H = {H:.2f} m, B = {B:.2f} m (toe {toe:.2f} m, heel {heel:.2f} m), stem "
                 "{t_top:.2f}–{t_bot:.2f} m, footing {t_f:.2f} m, soil over the toe {D:.2f} m, "
                 "β = {beta:.1f}°",
                 "Duvar: H = {H:.2f} m, B = {B:.2f} m (ön ampatman {toe:.2f} m, topuk "
                 "{heel:.2f} m), gövde {t_top:.2f}–{t_bot:.2f} m, temel {t_f:.2f} m, ön "
                 "ampatman üzerinde zemin {D:.2f} m, β = {beta:.1f}°"),
    "res_method": ("Earth pressure: {method}, K = {K:.4f} at ω = {omega:.1f}° on the virtual "
                   "back, h = {h:.2f} m",
                   "Toprak basıncı: {method}, sanal arka yüzde K = {K:.4f}, ω = {omega:.1f}°, "
                   "h = {h:.2f} m"),
    "res_forces": ("ΣV = {V:.1f} kN/m, ΣH = {Hf:.1f} kN/m, M_R = {MR:.1f} kNm/m, "
                   "M_O = {MO:.1f} kNm/m, e = {e:.3f} m",
                   "ΣV = {V:.1f} kN/m, ΣH = {Hf:.1f} kN/m, M_R = {MR:.1f} kNm/m, "
                   "M_O = {MO:.1f} kNm/m, e = {e:.3f} m"),
    "res_required": ("required", "gerekli"),
    "res_stability_title": ("STABILITY", "DURAYLILIK"),
    "res_sliding": ("Sliding resistance: friction {fr:.1f} + adhesion {ad:.1f} + passive "
                    "{pp:.1f} = {R:.1f} kN/m",
                    "Kayma direnci: sürtünme {fr:.1f} + adezyon {ad:.1f} + pasif {pp:.1f} = "
                    "{R:.1f} kN/m"),
    "res_base": ("Base pressure: toe {qt:.1f} kPa, heel {qh:.1f} kPa, in contact over "
                 "{c:.2f} m",
                 "Taban basıncı: ön uç {qt:.1f} kPa, arka uç {qh:.1f} kPa, temas boyu {c:.2f} m"),
    "res_bearing": ("B' = {B:.3f} m, σv = {s:.1f} kPa, q_ult = {q:.1f} kPa ({method})",
                    "B' = {B:.3f} m, σv = {s:.1f} kPa, q_ult = {q:.1f} kPa ({method})"),
    "res_bearing_title": ("BEARING CAPACITY BY METHOD", "YÖNTEME GÖRE TAŞIMA GÜCÜ"),
    "res_methods_title": ("EARTH PRESSURE BY METHOD (virtual back)",
                          "YÖNTEME GÖRE TOPRAK BASINCI (sanal arka yüz)"),
    "res_seismic_title": ("EARTHQUAKE (TBDY 2018)", "DEPREM (TBDY 2018)"),
    "res_design_title": ("REINFORCED CONCRETE DESIGN (TS 500)", "BETONARME TASARIM (TS 500)"),
    "res_material": ("{grade} / {steel}: fcd = {fcd:.2f} MPa, fctd = {fctd:.3f} MPa, "
                     "fyd = {fyd:.1f} MPa, ρmax = {rho_max:.4f}",
                     "{grade} / {steel}: fcd = {fcd:.2f} MPa, fctd = {fctd:.3f} MPa, "
                     "fyd = {fyd:.1f} MPa, ρmax = {rho_max:.4f}"),
    "res_sections_title": ("SECTIONS", "KESİTLER"),
    "res_cut": ("Half the stem bars stop {y:.2f} m above the footing.",
                "Gövde donatısının yarısı temelin {y:.2f} m üstünde kesilir."),
    "res_no_cut": ("The stem bars run the full height.",
                   "Gövde donatısı tam boy devam eder."),
    "res_schedule_title": ("BAR BENDING SCHEDULE (per metre of wall)",
                           "DONATI AÇILIMI (duvarın metresi başına)"),
    "res_quantities": ("Concrete {v:.3f} m³/m, steel {s:.1f} kg/m ({r:.0f} kg/m³)",
                       "Beton {v:.3f} m³/m, çelik {s:.1f} kg/m ({r:.0f} kg/m³)"),
    "res_heel": ("The stability checks need a heel of {heel:.2f} m; the wall has {cur:.2f} m.",
                 "Duraylılık kontrolleri {heel:.2f} m topuk gerektiriyor; duvarda {cur:.2f} m."),
    "res_no_heel": ("No heel up to 3·H satisfies the stability checks.",
                    "3·H'ye kadar hiçbir topuk boyu duraylılık kontrollerini sağlamıyor."),

    # ------------------------------------------------------------------ figures
    "fig_section": ("Section, forces and base pressure", "Kesit, kuvvetler ve taban basıncı"),
    "fig_pressure": ("Pressures on the virtual back", "Sanal arka yüzdeki basınçlar"),
    "fig_methods": ("Earth pressure by method", "Yönteme göre toprak basıncı"),
    "fig_stability": ("Stability checks", "Duraylılık kontrolleri"),
    "fig_bearing": ("Bearing capacity by method", "Yönteme göre taşıma gücü"),
    "fig_global": ("Global stability: the critical slip circle",
                   "Genel duraylılık: kritik kayma dairesi"),
    "fig_stem": ("Stem: moment and shear", "Gövde: moment ve kesme"),
    "fig_footing": ("Footing: base pressure and moments", "Temel: taban basıncı ve momentler"),
    "fig_reinforcement": ("Reinforcement drawing", "Donatı çizimi"),
    "fig_schedule": ("Bar bending schedule", "Donatı açılımı"),
    "fig_spectrum": ("TBDY 2018 design spectrum", "TBDY 2018 tasarım spektrumu"),
    "plot_x": ("x from the toe [m]", "ön uçtan x [m]"),
    "plot_y": ("height above the base [m]", "tabandan yükseklik [m]"),
    "plot_water": ("water", "su"),
    "plot_virtual_back": ("virtual back", "sanal arka yüz"),
    "plot_static": ("static", "statik"),
    "plot_seismic": ("seismic", "deprem"),
    "plot_p_soil": ("soil", "zemin"),
    "plot_p_dead": ("permanent surcharge", "kalıcı sürşarj"),
    "plot_p_live": ("live surcharge", "hareketli sürşarj"),
    "plot_p_water": ("water", "su"),
    "plot_p_dynamic": ("with the dynamic increment", "dinamik artışla"),
    "plot_p_passive": ("passive in front (share counted)", "öndeki pasif (hesaba katılan pay)"),
    "plot_p_axis": ("horizontal pressure [kPa]", "yatay basınç [kPa]"),
    "plot_p_info": ("{method}: K = {K:.4f}, ω = {omega:.1f}°\nΣH = {H:.1f} kN/m",
                    "{method}: K = {K:.4f}, ω = {omega:.1f}°\nΣH = {H:.1f} kN/m"),
    "plot_Kh": ("horizontal coefficient Kh", "yatay katsayı Kh"),
    "plot_Ph": ("horizontal thrust Ph [kN/m]", "yatay itki Ph [kN/m]"),
    "plot_margin": ("value / required (1 = at the limit)", "değer / gerekli (1 = sınırda)"),
    "plot_no_bearing": ("The resultant leaves the base.", "Bileşke tabanın dışında."),
    "plot_allow": ("q_ult / {FS:.1f}", "q_ult / {FS:.1f}"),
    "plot_applied": ("σv = ΣV / B'", "σv = ΣV / B'"),
    "plot_qmax": ("peak base pressure q_max", "en büyük taban basıncı q_maks"),
    "plot_q_allow_given": ("allowable pressure given", "verilen emniyet gerilmesi"),
    "plot_q_axis": ("pressure [kPa]", "basınç [kPa]"),
    "plot_global_info": ("{case}: Bishop F = {bishop:.3f}, Fellenius F = {fellenius:.3f}",
                         "{case}: Bishop F = {bishop:.3f}, Fellenius F = {fellenius:.3f}"),
    "plot_envelope": ("envelope", "zarf"),
    "plot_Mr": ("capacity Mr of the bars", "donatının taşıdığı Mr"),
    "plot_cut": ("half the bars stop at {y:.2f} m", "donatının yarısı {y:.2f} m'de kesilir"),
    "plot_M_axis": ("moment [kNm/m]", "moment [kNm/m]"),
    "plot_V_axis": ("shear [kN/m]", "kesme [kN/m]"),
    "plot_service": ("service (unfactored)", "işletme (katsayısız)"),
    "plot_M_toe": ("toe (bottom tension +)", "ön ampatman (alt çekme +)"),
    "plot_M_heel": ("heel (top tension +)", "topuk (üst çekme +)"),
    "plot_T": ("period T [s]", "periyot T [s]"),
    "plot_Sae": ("Sae(T) [g]", "Sae(T) [g]"),
    "plot_spectrum_info": ("site {site}: Ss = {Ss:.3f}, S1 = {S1:.3f}\nFs = {Fs:.2f}, "
                           "F1 = {F1:.2f}\nSDS = {SDS:.3f}, SD1 = {SD1:.3f}\nβr = {br:.2f}: "
                           "kh = {kh:.3f}, kv = {kv:.3f}",
                           "zemin {site}: Ss = {Ss:.3f}, S1 = {S1:.3f}\nFs = {Fs:.2f}, "
                           "F1 = {F1:.2f}\nSDS = {SDS:.3f}, SD1 = {SD1:.3f}\nβr = {br:.2f}: "
                           "kh = {kh:.3f}, kv = {kv:.3f}"),

    # ------------------------------------------------------------------ shell texts shared
    "run_analysis_button": ("Analyse and design", "Çözümle ve tasarla"),
    "running_analysis": ("Analysing…", "Çözümleniyor…"),
    "analysis_complete": ("Analysis complete.", "Çözümleme tamamlandı."),
    "report_action": ("Export report…", "Raporu dışa aktar…"),
    "report_running": ("Writing the report…", "Rapor yazılıyor…"),
    "warnings_title": ("Warnings", "Uyarılar"),
}

TRANSLATIONS = {
    "en": {key: pair[0] for key, pair in ENTRIES.items()},
    "tr": {key: pair[1] for key, pair in ENTRIES.items()},
}


def t(lang: str, key: str, **params) -> str:
    """One text in one language, formatted; the key itself if it is unknown.

    A parameter that is itself a key of the translations (a soil's name) is
    translated before it is put in.
    """
    table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = table.get(key, key)
    if not params:
        return text
    params = {k: (table.get(v, v) if isinstance(v, str) else v) for k, v in params.items()}
    return text.format(**params)


def warning_text(lang: str, warning) -> str:
    """An engine warning, (key, params), as a sentence."""
    key, params = warning
    return t(lang, key, **params)
