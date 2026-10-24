"""
Every text of SlipSurface IQ Bearing, in English and Turkish.

Each entry is written once as ``key: (English, Turkish)`` so the two languages
cannot drift apart: a key without its translation is a syntax error, not a
blank on the screen. `TRANSLATIONS[lang][key]` is how the rest of the program
reads them.
"""

from __future__ import annotations

ENTRIES = {
    # ------------------------------------------------------------------ input errors
    "err_dimensions": ("The foundation width and length must be greater than zero.",
                       "Temel genişliği ve boyu sıfırdan büyük olmalıdır."),
    "err_depth": ("The foundation depth cannot be negative.",
                  "Temel derinliği negatif olamaz."),
    "err_tilt": ("The base tilt and the ground slope must be positive angles whose sum "
                 "is below 90°.",
                 "Taban eğimi ile arazi eğimi pozitif ve toplamları 90°'den küçük olmalıdır."),
    "err_load": ("The vertical load must be greater than zero.",
                 "Düşey yük sıfırdan büyük olmalıdır."),
    "err_gamma": ("Layer '{name}': γ must be positive and γsat greater than γw.",
                  "'{name}' tabakası: γ pozitif, γdoy ise γw'den büyük olmalıdır."),
    "err_phi": ("Layer '{name}': the friction angle must be between 0 and 60°.",
                "'{name}' tabakası: içsel sürtünme açısı 0 ile 60° arasında olmalıdır."),
    "err_nu": ("Layer '{name}': Poisson's ratio must be between 0 and 0.5.",
               "'{name}' tabakası: Poisson oranı 0 ile 0.5 arasında olmalıdır."),
    "err_no_layers": ("The soil profile has no layer with a thickness.",
                      "Zemin profilinde kalınlığı girilmiş tabaka yok."),
    "err_base_below": ("The foundation base must lie within the soil profile "
                       "(Df < {depth:.2f} m).",
                       "Temel tabanı zemin profilinin içinde olmalıdır (Df < {depth:.2f} m)."),
    "err_no_strength": ("Layer '{name}' has no strength at all: enter c' and φ', or cu.",
                        "'{name}' tabakasının hiç dayanımı yok: c' ve φ' ya da cu giriniz."),
    "err_eccentricity": ("The eccentricity leaves no effective area: the resultant falls "
                         "outside the base.",
                         "Dışmerkezlik etkin alan bırakmıyor: bileşke yük tabanın dışına "
                         "düşüyor."),
    "err_no_method": ("No method can be run on these inputs: a drained analysis needs c' "
                      "or φ', an undrained one needs cu.",
                      "Bu girdilerle hiçbir yöntem çalıştırılamıyor: drenajlı analiz c' ya "
                      "da φ', drenajsız analiz cu ister."),

    # ------------------------------------------------------------------ warnings
    "warn_swapped": ("The length was shorter than the width; B and L were swapped so that B ≤ L.",
                     "Boy genişlikten kısaydı; B ≤ L olacak şekilde B ve L yer değiştirdi."),
    "warn_kern": ("The resultant falls outside the middle third (e = {e:.3f} m > B/6 = "
                  "{limit:.3f} m): part of the base lifts off.",
                  "Bileşke yük orta üçte birin dışına düşüyor (e = {e:.3f} m > B/6 = "
                  "{limit:.3f} m): tabanın bir kısmı zeminden ayrılıyor."),
    "warn_zone_below": ("The failure zone reaches below the soil profile ({depth:.2f} m); "
                        "the last layer is taken as continuing.",
                        "Göçme bölgesi zemin profilinin altına ({depth:.2f} m) iniyor; son "
                        "tabakanın devam ettiği kabul edildi."),
    "warn_local_shear": ("Local shear: the strength was reduced to c* = 2c/3 and "
                         "φ* = arctan(2·tan φ/3).",
                         "Yerel kayma: dayanım c* = 2c/3 ve φ* = arctan(2·tan φ/3) olarak "
                         "azaltıldı."),
    "warn_seismic_limit": ("The horizontal seismic coefficient kh = {kh:.3f} reaches "
                           "tan φ = {limit:.3f}: the soil mass alone is at failure and the "
                           "surcharge and self-weight terms are taken as zero.",
                           "Yatay deprem katsayısı kh = {kh:.3f}, tan φ = {limit:.3f} "
                           "değerine ulaşıyor: zemin kütlesi tek başına göçme durumunda, "
                           "sürşarj ve zati ağırlık terimleri sıfır alındı."),
    "warn_method_unavailable": ("The chosen method ({method}) cannot be run on these inputs; "
                                "another was used for the checks.",
                                "Seçilen yöntem ({method}) bu girdilerle çalıştırılamadı; "
                                "kontroller için başka bir yöntem kullanıldı."),
    "warn_no_inclination": ("{method} defines no load inclination factors: the horizontal "
                            "load does not reduce its capacity. Compare it with Hansen's or "
                            "Vesić's.",
                            "{method} yöntemi yük eğim katsayısı tanımlamaz: yatay yük "
                            "taşıma gücünü azaltmaz. Hansen ya da Vesić ile karşılaştırınız."),
    "warn_ec7_depth": ("EN 1997-1 Annex D gives no depth factors; Hansen's were used because "
                       "depth factors are switched on.",
                       "EN 1997-1 Ek D derinlik katsayısı vermez; derinlik katsayıları açık "
                       "olduğu için Hansen'inkiler kullanıldı."),
    "warn_two_layer_single": ("The two-layer check needs a second layer below the one the "
                              "foundation sits on; the strength was averaged instead.",
                              "İki tabakalı kontrol, temelin oturduğu tabakanın altında ikinci "
                              "bir tabaka ister; onun yerine dayanım ortalandı."),
    "warn_two_layer_strength": ("The two-layer check needs both layers to have a strength in "
                                "the analysis that was run.",
                                "İki tabakalı kontrol, çalıştırılan analizde her iki tabakanın "
                                "da dayanımı olmasını ister."),
    "warn_ksp_range": ("The Ksp method is written for a discontinuity spacing above 0.3 m and "
                       "an aperture below 5 mm; the inputs fall outside that range.",
                       "Ksp yöntemi 0.3 m'den geniş süreksizlik aralığı ve 5 mm'den küçük "
                       "açıklık için yazılmıştır; girdiler bu aralığın dışında."),

    # ------------------------------------------------------------------ choice labels
    "shape_rectangle": ("Rectangle", "Dikdörtgen"),
    "shape_square": ("Square", "Kare"),
    "shape_strip": ("Strip", "Şerit"),
    "shape_circle": ("Circle", "Daire"),
    "method_terzaghi": ("Terzaghi (1943)", "Terzaghi (1943)"),
    "method_meyerhof": ("Meyerhof (1963)", "Meyerhof (1963)"),
    "method_hansen": ("Brinch Hansen (1970)", "Brinch Hansen (1970)"),
    "method_vesic": ("Vesić (1973)", "Vesić (1973)"),
    "method_ec7": ("EN 1997-1 Annex D", "EN 1997-1 Ek D"),
    "method_skempton": ("Skempton (1951), undrained", "Skempton (1951), drenajsız"),
    "method_punching": ("Punching (Meyerhof & Hanna)", "Zımbalama (Meyerhof & Hanna)"),
    "method_spread": ("Load spread onto the weak layer", "Zayıf tabakaya yük yayılması"),
    "method_spt": ("SPT (Meyerhof), settlement rule", "SPT (Meyerhof), oturma kuralı"),
    "method_cpt": ("CPT (Meyerhof), settlement rule", "CPT (Meyerhof), oturma kuralı"),
    "method_pmt": ("Pressuremeter (Ménard)", "Presiyometre (Ménard)"),
    "method_hoek_brown": ("Rock: Hoek–Brown", "Kaya: Hoek–Brown"),
    "method_ksp": ("Rock: CFEM Ksp", "Kaya: CFEM Ksp"),
    "analysis_both": ("Whichever governs", "Hangisi belirleyiciyse"),
    "analysis_drained": ("Drained (c', φ')", "Drenajlı (c', φ')"),
    "analysis_undrained": ("Undrained (cu, φ = 0)", "Drenajsız (cu, φ = 0)"),
    "shear_general": ("General shear", "Genel kayma"),
    "shear_local": ("Local shear (Terzaghi's reduction)", "Yerel kayma (Terzaghi azaltması)"),
    "behaviour_granular": ("Granular", "Granüler"),
    "behaviour_cohesive": ("Cohesive", "Kohezyonlu"),
    "layer_model_average": ("Average over the failure zone", "Göçme bölgesinde ortalama"),
    "layer_model_two_layer": ("Two layers (strong over weak)", "İki tabaka (sağlam / zayıf)"),
    "two_layer_punching": ("Punching (Meyerhof & Hanna)", "Zımbalama (Meyerhof & Hanna)"),
    "two_layer_spread": ("Load spread", "Yük yayılması"),
    "approach_fs": ("Factor of safety", "Güvenlik sayısı"),
    "approach_da1": ("EN 1997-1, Design Approach 1", "EN 1997-1, Tasarım Yaklaşımı 1"),
    "approach_da2": ("EN 1997-1, Design Approach 2", "EN 1997-1, Tasarım Yaklaşımı 2"),
    "approach_da3": ("EN 1997-1, Design Approach 3", "EN 1997-1, Tasarım Yaklaşımı 3"),
    "test_spt": ("SPT", "SPT"),
    "test_cpt": ("CPT (cone)", "CPT (koni)"),
    "test_pmt": ("Pressuremeter", "Presiyometre"),
    "category_clay_a": ("Clay / silt A", "Kil / silt A"),
    "category_clay_b": ("Clay / silt B", "Kil / silt B"),
    "category_sand_a": ("Sand A", "Kum A"),
    "category_sand_b": ("Sand and gravel B", "Kum ve çakıl B"),
    "category_rock": ("Weathered rock", "Ayrışmış kaya"),
    "rock_method_hoek_brown": ("Hoek–Brown → equivalent c', φ'",
                               "Hoek–Brown → eşdeğer c', φ'"),
    "rock_method_ksp": ("CFEM discontinuity spacing (Ksp)",
                        "CFEM süreksizlik aralığı (Ksp)"),
    "analysis_label_short_drained": ("drained", "drenajlı"),
    "analysis_label_short_undrained": ("undrained", "drenajsız"),

    # ------------------------------------------------------------------ input groups
    "group_project": ("Project", "Proje"),
    "title_label": ("Title", "Başlık"),
    "analyst_label": ("Analyst", "Hazırlayan"),
    "group_foundation": ("Foundation", "Temel"),
    "shape_label": ("Shape", "Şekil"),
    "B_label": ("Width B (diameter of a circle)", "Genişlik B (dairede çap)"),
    "L_label": ("Length L", "Boy L"),
    "Df_label": ("Foundation depth Df", "Temel derinliği Df"),
    "tilt_label": ("Base tilt η", "Taban eğimi η"),
    "slope_label": ("Ground slope β", "Arazi eğimi β"),
    "foundation_note": ("A square and a circle take their length from B; a strip is analysed "
                        "per metre of length.",
                        "Kare ve dairede boy B'den alınır; şerit temel bir metre boy için "
                        "çözülür."),
    "group_loading": ("Actions at the base", "Taban yükleri"),
    "V_label": ("Vertical load V", "Düşey yük V"),
    "Hb_label": ("Horizontal load along B", "B yönünde yatay yük"),
    "Hl_label": ("Horizontal load along L", "L yönünde yatay yük"),
    "Mb_label": ("Moment giving an eccentricity along B",
                 "B yönünde dışmerkezlik veren moment"),
    "Ml_label": ("Moment giving an eccentricity along L",
                 "L yönünde dışmerkezlik veren moment"),
    "varfrac_label": ("Variable share of the actions", "Yüklerin hareketli payı"),
    "loading_note": ("Characteristic actions at the centre of the base. A moment becomes an "
                     "eccentricity e = M/V, a horizontal load an inclination. The variable "
                     "share is what the Eurocode's partial factors need; a strip takes its "
                     "actions per metre.",
                     "Taban merkezindeki karakteristik yükler. Moment e = M/V dışmerkezliğine, "
                     "yatay yük eğime dönüşür. Hareketli pay, Eurocode kısmi katsayıları için "
                     "gereklidir; şerit temelde yükler bir metre içindir."),
    "group_water": ("Groundwater", "Yeraltı suyu"),
    "water_depth_label": ("Water table depth", "Su tablası derinliği"),
    "gamma_w_label": ("Unit weight of water γw", "Suyun birim hacim ağırlığı γw"),
    "group_options": ("Method", "Yöntem"),
    "method_label": ("Bearing capacity method", "Taşıma gücü yöntemi"),
    "analysis_label": ("Analysis", "Analiz"),
    "shear_label": ("Failure mode", "Göçme biçimi"),
    "shape_factors_label": ("Shape factors", "Şekil katsayıları"),
    "depth_factors_label": ("Depth factors", "Derinlik katsayıları"),
    "inclination_factors_label": ("Load inclination factors", "Yük eğim katsayıları"),
    "base_factors_label": ("Base tilt factors", "Taban eğim katsayıları"),
    "ground_factors_label": ("Ground slope factors", "Arazi eğim katsayıları"),
    "compressibility_label": ("Compressibility factors (Vesić)",
                              "Sıkışabilirlik katsayıları (Vesić)"),
    "effective_area_label": ("Effective area for the eccentricity (Meyerhof)",
                             "Dışmerkezlik için etkin alan (Meyerhof)"),
    "options_note": ("A factor a method does not define stays 1 and is reported as such. "
                     "Terzaghi's method has shape factors only.",
                     "Bir yöntemin tanımlamadığı katsayı 1 kalır ve raporda öyle görünür. "
                     "Terzaghi yönteminde yalnızca şekil katsayıları vardır."),
    "group_layers": ("Layered ground", "Tabakalı zemin"),
    "layer_model_label": ("Layer model", "Tabaka modeli"),
    "zone_factor_label": ("Failure zone depth, × the Prandtl depth",
                          "Göçme bölgesi derinliği, × Prandtl derinliği"),
    "two_layer_model_label": ("Two-layer check", "İki tabakalı kontrol"),
    "Ks_label": ("Punching shear coefficient Ks (0: 1 − sin φ₁)",
                 "Zımbalama kayma katsayısı Ks (0: 1 − sin φ₁)"),
    "adhesion_label": ("Adhesion ratio ca/c₁", "Adezyon oranı ca/c₁"),
    "spread_angle_label": ("Load spread angle from the vertical",
                           "Düşeyden ölçülen yük yayılma açısı"),
    "layers_note": ("The strength is averaged over the failure zone, whose depth is the "
                    "Prandtl depth (0.707·B at φ = 0, about 1.6·B at φ = 30°). The two-layer "
                    "check applies where the foundation sits on a layer thinner than that "
                    "zone.",
                    "Dayanım, derinliği Prandtl derinliği olan göçme bölgesinde ortalanır "
                    "(φ = 0'da 0.707·B, φ = 30°'de yaklaşık 1.6·B). İki tabakalı kontrol, "
                    "temelin bu bölgeden ince bir tabakaya oturduğu durumda geçerlidir."),
    "group_seismic": ("Earthquake", "Deprem"),
    "seismic_enabled_label": ("Pseudo-static analysis", "Psödo-statik analiz"),
    "kh_label": ("Horizontal coefficient kh", "Yatay katsayı kh"),
    "kv_label": ("Vertical coefficient kv (positive upwards)",
                 "Düşey katsayı kv (yukarı yönde pozitif)"),
    "soil_inertia_label": ("Soil inertia (Paolucci & Pecker)",
                           "Zemin ataleti (Paolucci & Pecker)"),
    "seismic_note": ("The structure's inertia kh·V is added to the horizontal load and the "
                     "vertical load becomes V·(1 − kv); the soil's own inertia reduces the "
                     "capacity terms by (1 − kh/tan φ)^0.35 and (1 − 0.32·kh).",
                     "Yapının ataleti kh·V yatay yüke eklenir, düşey yük V·(1 − kv) olur; "
                     "zeminin kendi ataleti taşıma gücü terimlerini (1 − kh/tan φ)^0.35 ve "
                     "(1 − 0.32·kh) ile azaltır."),
    "group_insitu": ("In-situ test", "Arazi deneyi"),
    "insitu_enabled_label": ("Add the in-situ capacity", "Arazi deneyi taşıma gücünü ekle"),
    "test_label": ("Test", "Deney"),
    "N60_label": ("SPT N60", "SPT N60"),
    "qc_label": ("Cone resistance qc", "Koni direnci qc"),
    "pl_label": ("Limit pressure pl", "Limit basınç pl"),
    "p0_label": ("At-rest pressure p0", "Sükûnetteki basınç p0"),
    "category_label": ("Soil category (Ménard)", "Zemin sınıfı (Ménard)"),
    "settlement_label": ("Tolerable settlement", "İzin verilen oturma"),
    "insitu_note": ("The SPT and CPT rules give the pressure that keeps the settlement within "
                    "the tolerable value — they are settlement rules, not a rupture capacity. "
                    "Ménard's rule gives an ultimate capacity.",
                    "SPT ve CPT kuralları, oturmayı izin verilen değerin altında tutan basıncı "
                    "verir — bunlar oturma kurallarıdır, göçme taşıma gücü değil. Ménard kuralı "
                    "nihai taşıma gücü verir."),
    "group_rock": ("Rock", "Kaya"),
    "rock_enabled_label": ("The founding stratum is rock", "Temel kayaya oturuyor"),
    "rock_method_label": ("Rock method", "Kaya yöntemi"),
    "sigma_ci_label": ("Intact rock strength σci", "Sağlam kaya dayanımı σci"),
    "GSI_label": ("Geological Strength Index", "Jeolojik Dayanım İndeksi"),
    "mi_label": ("Hoek–Brown constant mi", "Hoek–Brown sabiti mi"),
    "rock_D_label": ("Disturbance factor D", "Örselenme katsayısı D"),
    "gamma_rock_label": ("Unit weight of the rock mass", "Kaya kütlesinin birim hacim ağırlığı"),
    "spacing_label": ("Discontinuity spacing", "Süreksizlik aralığı"),
    "aperture_label": ("Discontinuity aperture", "Süreksizlik açıklığı"),
    "rock_note": ("Hoek–Brown turns the rock mass into an equivalent c' and φ' up to "
                  "σ3 = σci/4 and runs the same bearing capacity equation. The CFEM Ksp "
                  "method already carries a factor of safety of 3.",
                  "Hoek–Brown, kaya kütlesini σ3 = σci/4'e kadar eşdeğer c' ve φ'ye çevirir ve "
                  "aynı taşıma gücü denklemini çalıştırır. CFEM Ksp yöntemi zaten 3 güvenlik "
                  "sayısı içerir."),
    "group_criteria": ("Verification", "Kontrol"),
    "approach_label": ("Verification", "Kontrol biçimi"),
    "FS_label": ("Required factor of safety", "Gerekli güvenlik sayısı"),
    "FS_sliding_label": ("Required factor of safety against sliding",
                         "Kaymaya karşı gerekli güvenlik sayısı"),
    "ecc_limit_label": ("Allowable eccentricity, B / x", "İzin verilen dışmerkezlik, B / x"),
    "delta_ratio_label": ("Base friction δ / φ'", "Taban sürtünmesi δ / φ'"),
    "criteria_note": ("The factor of safety is taken on the net capacity, q_net,ult / q_net. "
                      "A Design Approach instead factors the actions, the strength and the "
                      "resistance as EN 1997-1 Annex A does. B/6 is the middle third.",
                      "Güvenlik sayısı net taşıma gücü üzerinden alınır: q_net,ult / q_net. "
                      "Tasarım Yaklaşımı ise yükleri, dayanımı ve direnci EN 1997-1 Ek A'daki "
                      "gibi katsayılarla çarpar. B/6 orta üçte birdir."),
    "group_study": ("Study", "Çalışma"),
    "study_method": ("Sampling", "Örnekleme"),
    "study_n": ("Samples", "Örnek sayısı"),
    "study_seed": ("Seed (0: random)", "Tohum (0: rastgele)"),
    "study_note": ("A range sweeps the input one at a time; a distribution samples it. "
                   "Latin hypercube needs fewer samples than plain Monte Carlo for the same "
                   "precision.",
                   "Aralık girdiyi teker teker tarar; dağılım ise örnekler. Latin hiperküp, "
                   "aynı hassasiyet için düz Monte Carlo'dan daha az örnek ister."),
    "sampling_oat": ("One at a time", "Teker teker"),
    "sampling_lhs": ("Latin hypercube", "Latin hiperküp"),
    "sampling_mc": ("Monte Carlo", "Monte Carlo"),
    "dist_normal": ("Normal", "Normal"),
    "dist_lognormal": ("Lognormal", "Lognormal"),
    "dist_uniform": ("Uniform", "Düzgün"),
    "mode_range": ("Range", "Aralık"),
    "mode_dist": ("Distribution", "Dağılım"),

    # ------------------------------------------------------------------ table columns
    "col_name": ("Layer", "Tabaka"),
    "col_thickness": ("t (m)", "t (m)"),
    "col_behaviour": ("Type", "Tür"),
    "col_gamma": ("γ (kN/m³)", "γ (kN/m³)"),
    "col_gamma_sat": ("γsat (kN/m³)", "γdoy (kN/m³)"),
    "col_c": ("c' (kPa)", "c' (kPa)"),
    "col_phi": ("φ' (°)", "φ' (°)"),
    "col_cu": ("cu (kPa)", "cu (kPa)"),
    "col_E": ("E (MPa)", "E (MPa)"),
    "col_nu": ("ν", "ν"),
    "soil_note": ("c' and φ' are the effective strength, cu the undrained shear strength; "
                  "a granular layer needs no cu and a cohesive one is checked both ways. "
                  "E and ν are only used by the compressibility factors.",
                  "c' ve φ' efektif dayanım, cu ise drenajsız kayma dayanımıdır; granüler "
                  "tabakada cu gerekmez, kohezyonlu tabaka her iki durumda da kontrol edilir. "
                  "E ve ν yalnızca sıkışabilirlik katsayılarında kullanılır."),
    "col_param": ("Input", "Girdi"),
    "col_mode": ("Mode", "Mod"),
    "col_min": ("Min", "Min"),
    "col_max": ("Max", "Maks"),
    "col_dist": ("Distribution", "Dağılım"),
    "col_mean": ("Mean", "Ortalama"),
    "col_cov": ("CoV", "CoV"),
    "col_points": ("Points", "Nokta"),

    # ------------------------------------------------------------------ cards
    "card_q_ult": ("Ultimate capacity q_ult", "Nihai taşıma gücü q_ult"),
    "card_q_net": ("Net ultimate q_net,ult", "Net nihai q_net,ult"),
    "card_q_all": ("Allowable q_all", "İzin verilebilir q_all"),
    "card_applied": ("Applied pressure", "Uygulanan basınç"),
    "card_FS": ("Factor of safety", "Güvenlik sayısı"),
    "card_check_bearing": ("Bearing check", "Taşıma gücü kontrolü"),
    "card_check_sliding": ("Sliding check", "Kayma kontrolü"),
    "card_check_ecc": ("Eccentricity check", "Dışmerkezlik kontrolü"),
    "card_width": ("Required width", "Gerekli genişlik"),
    "card_ec7": ("EN 1997-1", "EN 1997-1"),
    "card_governing": ("governing: {name}", "belirleyici: {name}"),
    "card_on_area": ("on A' = {area:.2f} m²", "A' = {area:.2f} m² üzerinde"),
    "card_none": ("—", "—"),
    "ok_short": ("OK", "UYGUN"),
    "notok_short": ("NOT OK", "UYGUN DEĞİL"),
    "na_short": ("n/a", "—"),

    # ------------------------------------------------------------------ results text
    "res_title": ("BEARING CAPACITY RESULTS", "TAŞIMA GÜCÜ SONUÇLARI"),
    "res_foundation": ("Foundation: {shape}, B = {B:.2f} m{L}, Df = {Df:.2f} m",
                       "Temel: {shape}, B = {B:.2f} m{L}, Df = {Df:.2f} m"),
    "res_tilt": ("Base tilt η = {eta:.1f}°, ground slope β = {beta:.1f}°",
                 "Taban eğimi η = {eta:.1f}°, arazi eğimi β = {beta:.1f}°"),
    "res_loading": ("Actions: V = {V:.1f} kN, H = {H:.1f} kN ({angle:.1f}° from vertical)",
                    "Yükler: V = {V:.1f} kN, H = {H:.1f} kN (düşeyden {angle:.1f}°)"),
    "res_eccentricity": ("Eccentricity: e_B = {eB:.3f} m, e_L = {eL:.3f} m → "
                         "B' = {Be:.3f} m, L' = {Le:.3f} m, A' = {A:.2f} m²",
                         "Dışmerkezlik: e_B = {eB:.3f} m, e_L = {eL:.3f} m → "
                         "B' = {Be:.3f} m, L' = {Le:.3f} m, A' = {A:.2f} m²"),
    "res_pressure": ("Contact pressure: q_max = {qmax:.1f} kPa, q_min = {qmin:.1f} kPa "
                     "({kern})",
                     "Taban basıncı: q_maks = {qmax:.1f} kPa, q_min = {qmin:.1f} kPa ({kern})"),
    "res_in_kern": ("within the middle third", "orta üçte bir içinde"),
    "res_out_kern": ("outside the middle third, contact over {c:.2f} m",
                     "orta üçte birin dışında, {c:.2f} m boyunca temas"),
    "res_surcharge": ("Surcharge at the base: σv0 = {total:.1f} kPa, u = {u:.1f} kPa, "
                      "σ'v0 = {eff:.1f} kPa",
                      "Taban sürşarjı: σv0 = {total:.1f} kPa, u = {u:.1f} kPa, "
                      "σ'v0 = {eff:.1f} kPa"),
    "res_zone": ("Failure zone: {depth:.2f} m below the base ({layers})",
                 "Göçme bölgesi: tabanın {depth:.2f} m altına kadar ({layers})"),
    "res_params": ("Design strength: c' = {c:.1f} kPa, φ' = {phi:.1f}°, cu = {cu:.1f} kPa, "
                   "γ = {gamma:.2f} kN/m³",
                   "Hesap dayanımı: c' = {c:.1f} kPa, φ' = {phi:.1f}°, cu = {cu:.1f} kPa, "
                   "γ = {gamma:.2f} kN/m³"),
    "res_methods_title": ("Bearing capacity by method", "Yönteme göre taşıma gücü"),
    "head_method": ("Method", "Yöntem"),
    "head_analysis": ("Analysis", "Analiz"),
    "head_qult": ("q_ult", "q_ult"),
    "head_qnet": ("q_net,ult", "q_net,ult"),
    "head_qall": ("q_all", "q_all"),
    "head_FS": ("FS", "GS"),
    "head_Nc": ("Nc", "Nc"),
    "head_Nq": ("Nq", "Nq"),
    "head_Ng": ("Nγ", "Nγ"),
    "res_factors_title": ("Factors of the governing method ({name})",
                          "Belirleyici yöntemin katsayıları ({name})"),
    "head_factor": ("Factor", "Katsayı"),
    "head_c_term": ("cohesion", "kohezyon"),
    "head_q_term": ("surcharge", "sürşarj"),
    "head_g_term": ("self weight", "zati ağırlık"),
    "factor_shape": ("shape s", "şekil s"),
    "factor_depth": ("depth d", "derinlik d"),
    "factor_inclination": ("inclination i", "eğim i"),
    "factor_base": ("base tilt b", "taban eğimi b"),
    "factor_ground": ("ground slope g", "arazi eğimi g"),
    "factor_compressibility": ("compressibility F", "sıkışabilirlik F"),
    "res_terms_title": ("The three terms of the governing method", "Belirleyici yöntemin "
                        "üç terimi"),
    "res_term_line": ("{name}: {value:.1f} kPa ({share:.0f} %)",
                      "{name}: {value:.1f} kPa (%{share:.0f})"),
    "res_others_title": ("Other methods", "Diğer yöntemler"),
    "res_two_layer": ("Two layers: q_top = {top:.1f} kPa, q_bottom = {bottom:.1f} kPa, "
                      "H = {H:.2f} m, Ks = {Ks:.3f}",
                      "İki tabaka: q_üst = {top:.1f} kPa, q_alt = {bottom:.1f} kPa, "
                      "H = {H:.2f} m, Ks = {Ks:.3f}"),
    "res_rock": ("Rock mass: mb = {mb:.3f}, s = {s:.5f}, a = {a:.3f} → c' = {c:.0f} kPa, "
                 "φ' = {phi:.1f}°",
                 "Kaya kütlesi: mb = {mb:.3f}, s = {s:.5f}, a = {a:.3f} → c' = {c:.0f} kPa, "
                 "φ' = {phi:.1f}°"),
    "res_seismic": ("Earthquake: kh = {kh:.3f}, kv = {kv:.3f}; the resultant is tilted by "
                    "{psi:.1f}°",
                    "Deprem: kh = {kh:.3f}, kv = {kv:.3f}; bileşke {psi:.1f}° eğiliyor"),
    "res_checks_title": ("Checks", "Kontroller"),
    "res_check_bearing": ("Bearing: FS = {actual:.2f} ≥ {allowable:.2f} — {status}",
                          "Taşıma gücü: GS = {actual:.2f} ≥ {allowable:.2f} — {status}"),
    "res_check_sliding": ("Sliding: FS = {actual:.2f} ≥ {allowable:.2f} — {status}",
                          "Kayma: GS = {actual:.2f} ≥ {allowable:.2f} — {status}"),
    "res_check_ecc": ("Eccentricity: e/B = {actual:.3f} ≤ {allowable:.3f} — {status}",
                      "Dışmerkezlik: e/B = {actual:.3f} ≤ {allowable:.3f} — {status}"),
    "res_ec7_title": ("EN 1997-1 verification ({approach})", "EN 1997-1 kontrolü ({approach})"),
    "res_ec7_line": ("{name} ({sets}): Ed = {Ed:.0f} kN ≤ Rd = {Rd:.0f} kN, "
                     "Λ = {util:.2f} — {status}",
                     "{name} ({sets}): Ed = {Ed:.0f} kN ≤ Rd = {Rd:.0f} kN, "
                     "Λ = {util:.2f} — {status}"),
    "res_ec7_slide": ("    sliding: Hd = {Hd:.0f} kN ≤ Rd = {Rd:.0f} kN — {status}",
                      "    kayma: Hd = {Hd:.0f} kN ≤ Rd = {Rd:.0f} kN — {status}"),
    "res_required_width": ("The bearing check is satisfied from B = {B:.2f} m",
                           "Taşıma gücü kontrolü B = {B:.2f} m'den itibaren sağlanıyor"),
    "res_no_width": ("No width within {hi:.0f} m satisfies the bearing check.",
                     "{hi:.0f} m'ye kadar hiçbir genişlik taşıma gücü kontrolünü sağlamıyor."),
    "res_layers_title": ("Soil profile", "Zemin profili"),
    "head_layer": ("Layer", "Tabaka"),
    "head_depth": ("Depth", "Derinlik"),
    "head_sigma": ("σ'v0", "σ'v0"),
    "warnings_title": ("Warnings", "Uyarılar"),

    # ------------------------------------------------------------------ figures
    "fig_schematic": ("Section and failure mechanism", "Kesit ve göçme mekanizması"),
    "fig_factors": ("Bearing capacity factors", "Taşıma gücü katsayıları"),
    "fig_comparison": ("Comparison of the methods", "Yöntemlerin karşılaştırması"),
    "fig_components": ("The three terms", "Üç terim"),
    "fig_width": ("Capacity against width", "Genişliğe göre taşıma gücü"),
    "fig_depth": ("Capacity against depth", "Derinliğe göre taşıma gücü"),
    "fig_envelope": ("Failure envelope V–H", "Göçme zarfı V–H"),
    "fig_pressure": ("Contact pressure and effective area", "Taban basıncı ve etkin alan"),
    "plot_ultimate": ("Ultimate", "Nihai"),
    "plot_allowable": ("Allowable", "İzin verilebilir"),
    "plot_applied": ("Applied", "Uygulanan"),
    "plot_design": ("Design resistance", "Tasarım direnci"),
    "plot_width": ("Width B", "Genişlik B"),
    "plot_depth": ("Depth Df", "Derinlik Df"),
    "plot_pressure": ("Pressure", "Basınç"),
    "plot_phi": ("Friction angle φ'", "İçsel sürtünme açısı φ'"),
    "plot_factor": ("Factor", "Katsayı"),
    "plot_required": ("Required B = {B:.2f} m", "Gerekli B = {B:.2f} m"),
    "plot_effective": ("Effective area A'", "Etkin alan A'"),
    "plot_base": ("Base", "Taban"),
    "plot_water": ("Water table", "Su tablası"),
    "plot_wedge": ("Failure zone", "Göçme bölgesi"),
    "plot_resultant": ("Resultant", "Bileşke"),
    "plot_this_case": ("This case", "Bu durum"),
    "plot_no_data": ("Nothing to draw.", "Çizilecek bir şey yok."),

    # ------------------------------------------------------------------ study
    "run_analysis_button": ("Analyse", "Hesapla"),
    "running_analysis": ("Analysing…", "Hesaplanıyor…"),
    "analysis_complete": ("Analysis complete.", "Hesap tamamlandı."),
    "report_action": ("Export report…", "Rapor al…"),
    "report_running": ("Writing the report…", "Rapor yazılıyor…"),
    "study_run": ("Run the study", "Çalışmayı başlat"),
    "study_cancel": ("Cancel", "İptal"),
    "study_export_csv": ("CSV", "CSV"),
    "study_export_xlsx": ("Excel", "Excel"),
    "study_vars_group": ("Study variables", "Çalışma değişkenleri"),
    "study_no_vars": ("Add at least one study variable.",
                      "En az bir çalışma değişkeni ekleyiniz."),
    "study_progress": ("Sample {done} of {total}", "{total} örnekten {done}."),
    "study_done": ("Study finished: {n} samples.", "Çalışma bitti: {n} örnek."),
    "study_cancelled": ("(cancelled)", "(iptal edildi)"),
    "study_failed": ("The study could not be started: {e}", "Çalışma başlatılamadı: {e}"),
    "study_no_data": ("No study has been run.", "Henüz çalışma yapılmadı."),
    "study_table_note": ("Only the first rows are shown; the CSV and Excel exports carry "
                         "them all.",
                         "Yalnızca ilk satırlar gösteriliyor; CSV ve Excel çıktıları hepsini "
                         "içerir."),
    "study_fig_oat": ("One-at-a-time sweep", "Teker teker tarama"),
    "study_fig_hist": ("Distribution of the output", "Çıktının dağılımı"),
    "study_fig_scatter": ("Output against each input", "Çıktı – girdi saçılımı"),
    "study_fig_tornado": ("Sensitivities", "Duyarlılıklar"),
    "out_q_ult": ("Ultimate capacity (kPa)", "Nihai taşıma gücü (kPa)"),
    "out_q_net_ult": ("Net ultimate capacity (kPa)", "Net nihai taşıma gücü (kPa)"),
    "out_q_all": ("Allowable pressure (kPa)", "İzin verilebilir basınç (kPa)"),
    "out_q_applied": ("Applied pressure (kPa)", "Uygulanan basınç (kPa)"),
    "out_FS": ("Factor of safety", "Güvenlik sayısı"),
    "out_utilisation": ("Utilisation", "Kullanım oranı"),
    "out_FS_sliding": ("Factor of safety, sliding", "Kaymaya karşı güvenlik sayısı"),
    "out_ecc": ("Eccentricity e/B", "Dışmerkezlik e/B"),
    "out_error": ("Error", "Hata"),
    "ls_bearing": ("Bearing capacity", "Taşıma gücü"),
    "ls_sliding": ("Sliding", "Kayma"),
    "ls_eccentricity": ("Eccentricity", "Dışmerkezlik"),
    "st_title": ("STUDY RESULTS", "ÇALIŞMA SONUÇLARI"),
    "st_info": ("Method: {method}; samples: {n}; successful: {ok}",
                "Yöntem: {method}; örnek: {n}; başarılı: {ok}"),
    "st_stats_title": ("Statistics of the outputs", "Çıktıların istatistikleri"),
    "st_rel_title": ("Probability of failure", "Göçme olasılığı"),
    "st_rel_line": ("{name}: {k} of {n}, P = {pf:.3g} (95 % CI {lo:.3g} – {hi:.3g}), β = {beta}",
                    "{name}: {n} örnekte {k}, P = {pf:.3g} (%95 GA {lo:.3g} – {hi:.3g}), "
                    "β = {beta}"),
    "st_sens_title": ("Sensitivity of the factor of safety (Spearman ρ)",
                      "Güvenlik sayısının duyarlılığı (Spearman ρ)"),
    "st_no_sens": ("Sensitivities need at least three samples of a sampled variable.",
                   "Duyarlılık için örneklenen değişkenin en az üç örneği gerekir."),
    "st_mean": ("mean", "ort."),
    "st_std": ("std", "std"),

    # ------------------------------------------------------------------ variable names
    "var_V": ("V", "V"),
    "var_Hb": ("H (B)", "H (B)"),
    "var_Hl": ("H (L)", "H (L)"),
    "var_Mb": ("M (B)", "M (B)"),
    "var_Ml": ("M (L)", "M (L)"),
    "var_B": ("B", "B"),
    "var_L": ("L", "L"),
    "var_Df": ("Df", "Df"),
    "var_base_tilt": ("η", "η"),
    "var_ground_slope": ("β", "β"),
    "var_depth": ("water table", "su tablası"),
    "var_thickness": ("t", "t"),
    "var_gamma": ("γ", "γ"),
    "var_gamma_sat": ("γsat", "γdoy"),
    "var_c": ("c'", "c'"),
    "var_phi": ("φ'", "φ'"),
    "var_cu": ("cu", "cu"),
    "var_E": ("E", "E"),
    "var_nu": ("ν", "ν"),
    "var_kh": ("kh", "kh"),
    "var_kv": ("kv", "kv"),
    "grp_foundation": ("Foundation", "Temel"),
    "grp_loading": ("Actions", "Yükler"),
    "grp_water": ("Groundwater", "Yeraltı suyu"),
    "grp_seismic": ("Earthquake", "Deprem"),
}

TRANSLATIONS = {
    "en": {key: pair[0] for key, pair in ENTRIES.items()},
    "tr": {key: pair[1] for key, pair in ENTRIES.items()},
}


def t(lang: str, key: str, **params) -> str:
    """One text in one language, formatted; the key itself if it is unknown."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return text.format(**params) if params else text


def warning_text(lang: str, warning) -> str:
    """An engine warning, (key, params), as a sentence."""
    key, params = warning
    return t(lang, key, **params)
