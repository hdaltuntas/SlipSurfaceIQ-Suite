"""
Every text of SlipSurface IQ Rock, in English and Turkish.

Each entry is written once as ``key: (English, Turkish)`` so the two languages
cannot drift apart: a key without its translation is a syntax error, not a
blank on the screen. `TRANSLATIONS[lang][key]` is how the rest of the program
reads them. The names in the typical-value tables (rock types, strength
grades, excavation cases, GSI classes) live with their values in
`slipsurface.rock.tables`.
"""

from __future__ import annotations

ENTRIES = {
    # ------------------------------------------------------------------ input errors
    "err_sigma_ci": ("The uniaxial compressive strength of the intact rock σci must be "
                     "greater than zero.",
                     "Sağlam kayanın tek eksenli basınç dayanımı σci sıfırdan büyük olmalıdır."),
    "err_mi": ("The Hoek–Brown constant mi must be greater than zero.",
               "Hoek–Brown sabiti mi sıfırdan büyük olmalıdır."),
    "err_ei": ("The intact modulus Ei (or the modulus ratio MR) must be greater than zero.",
               "Sağlam kaya modülü Ei (ya da modül oranı MR) sıfırdan büyük olmalıdır."),
    "err_gsi_input": ("GSI cannot be worked out: check '{name}'.",
                      "GSI hesaplanamıyor: '{name}' değerini kontrol ediniz."),
    "err_gsi": ("GSI = {gsi:.1f} is outside the range the criterion is written for "
                "({lo:.0f}–{hi:.0f}).",
                "GSI = {gsi:.1f}, ölçütün tanımlı olduğu aralığın ({lo:.0f}–{hi:.0f}) "
                "dışında."),
    "err_D": ("The disturbance factor D must be between 0 and 1.",
              "Örselenme faktörü D 0 ile 1 arasında olmalıdır."),
    "err_depth": ("A tunnel or a slope needs a positive unit weight and depth (height).",
                  "Tünel ya da şev için pozitif birim hacim ağırlık ve derinlik (yükseklik) "
                  "gerekir."),
    "err_sigma3max": ("The upper limit of confinement σ3max must be greater than zero.",
                      "Çevre basıncının üst sınırı σ3max sıfırdan büyük olmalıdır."),
    "err_lab_few": ("Fitting σci and mi needs at least two tests at different σ3.",
                    "σci ve mi uydurmak için farklı σ3 değerlerinde en az iki deney gerekir."),
    "err_lab_fit": ("The tests do not describe a Hoek–Brown envelope: the fitted line gives "
                    "no real σci or mi. Check the tests.",
                    "Deneyler bir Hoek–Brown zarfı tanımlamıyor: uydurulan doğru gerçek bir "
                    "σci ya da mi vermiyor. Deneyleri kontrol ediniz."),

    # ------------------------------------------------------------------ warnings
    "warn_lab_r2": ("The Hoek–Brown envelope fits the tests poorly (r² = {r2:.3f}); check "
                    "them for outliers or for failure along a discontinuity.",
                    "Hoek–Brown zarfı deneylere zayıf uyuyor (r² = {r2:.3f}); aykırı "
                    "değerleri ya da süreksizlik boyunca kırılmayı kontrol ediniz."),
    "warn_lab_narrow": ("The tests reach σ3 = {s3:.2f} MPa only; Hoek recommends tests up to "
                        "about σci/2 = {limit:.1f} MPa, and a narrow range makes mi uncertain.",
                        "Deneyler yalnızca σ3 = {s3:.2f} MPa'ya ulaşıyor; Hoek yaklaşık "
                        "σci/2 = {limit:.1f} MPa'ya kadar deney önerir, dar aralık mi'yi "
                        "belirsizleştirir."),
    "warn_lab_wide": ("The tests reach σ3 = {s3:.2f} MPa, beyond σci/2 = {limit:.1f} MPa, "
                      "where the rock may have turned ductile and the fit no longer applies.",
                      "Deneyler σ3 = {s3:.2f} MPa'ya, σci/2 = {limit:.1f} MPa'nın ötesine "
                      "ulaşıyor; burada kaya sünek davranmış olabilir ve uydurma geçerli "
                      "olmayabilir."),
    "warn_mi_range": ("mi = {mi:.1f} lies outside the typical range for {rock} "
                      "({lo:.0f}–{hi:.0f}).",
                      "mi = {mi:.1f}, {rock} için tipik aralığın ({lo:.0f}–{hi:.0f}) "
                      "dışında."),
    "warn_mr_range": ("MR = {MR:.0f} lies outside the typical range for {rock} "
                      "({lo:.0f}–{hi:.0f}).",
                      "MR = {MR:.0f}, {rock} için tipik aralığın ({lo:.0f}–{hi:.0f}) "
                      "dışında."),
    "warn_rmr_low": ("RMR89 = {rmr:.0f} is below {limit:.0f}, where GSI = RMR89 − 5 is not "
                     "reliable; estimate GSI from the chart or from Q' instead.",
                     "RMR89 = {rmr:.0f}, GSI = RMR89 − 5 bağıntısının güvenilir olmadığı "
                     "{limit:.0f} değerinin altında; GSI'yı abaktan ya da Q'dan kestiriniz."),
    "warn_gsi_high": ("GSI = {gsi:.0f}: a rock mass this little jointed may not behave "
                      "isotropically; check whether single discontinuities govern.",
                      "GSI = {gsi:.0f}: bu kadar az eklemli bir kaya kütlesi izotrop "
                      "davranmayabilir; tek tek süreksizliklerin davranışı yönetip "
                      "yönetmediğini kontrol ediniz."),
    "warn_tunnel_D": ("D = {D:.2f} in a tunnel: the disturbance applies to the damaged zone "
                      "around the opening only; the rock beyond it has D = 0.",
                      "Tünelde D = {D:.2f}: örselenme yalnızca açıklığın çevresindeki hasarlı "
                      "bölge için geçerlidir; ötesindeki kayada D = 0'dır."),
    "warn_erm_above_ei": ("The rock mass modulus Erm = {Erm:,.0f} MPa exceeds the intact "
                          "modulus Ei = {Ei:,.0f} MPa; check Ei, or use the generalised "
                          "estimate, which cannot.",
                          "Kaya kütlesi modülü Erm = {Erm:,.0f} MPa, sağlam kaya modülü "
                          "Ei = {Ei:,.0f} MPa'yı aşıyor; Ei'yi kontrol ediniz ya da bunu "
                          "yapamayan genelleştirilmiş tahmini kullanınız."),
    "warn_query_tension": ("σ3 = {s3:.3g} MPa lies below the tensile strength σt = {st:.3g} "
                           "MPa; the instantaneous strength is given at σt.",
                           "σ3 = {s3:.3g} MPa, çekme dayanımı σt = {st:.3g} MPa'nın altında; "
                           "anlık dayanım σt'de verilmiştir."),

    # ------------------------------------------------------------------ input groups
    "group_project": ("Project", "Proje"),
    "title_label": ("Title", "Başlık"),
    "analyst_label": ("Analyst", "Hazırlayan"),

    "group_intact": ("Intact rock", "Sağlam kaya"),
    "source_label": ("σci and mi from", "σci ve mi kaynağı"),
    "source_manual": ("values entered", "girilen değerler"),
    "source_lab": ("fit to triaxial tests", "üç eksenli deneylere uydurma"),
    "rock_type_label": ("Rock type (typical mi, MR)", "Kaya türü (tipik mi, MR)"),
    "picker_custom": ("— custom —", "— özel —"),
    "class_sedimentary": ("Sedimentary", "Tortul"),
    "class_metamorphic": ("Metamorphic", "Metamorfik"),
    "class_igneous": ("Igneous", "Magmatik"),
    "grade_label": ("Field strength grade", "Arazi dayanım sınıfı"),
    "sigma_ci_label": ("Uniaxial strength σci", "Tek eksenli dayanım σci"),
    "mi_label": ("Hoek–Brown constant mi", "Hoek–Brown sabiti mi"),
    "intact_note": ("A rock type fills in typical mi and MR, a field strength grade a typical "
                    "σci; every value stays editable. With 'fit to triaxial tests', σci and mi "
                    "come from the test table.",
                    "Kaya türü tipik mi ve MR, arazi dayanım sınıfı tipik σci değerini "
                    "doldurur; her değer düzenlenebilir kalır. 'Üç eksenli deneylere "
                    "uydurma' seçiliyken σci ve mi deney tablosundan gelir."),

    "group_gsi": ("Geological Strength Index", "Jeolojik Dayanım İndeksi"),
    "gsi_source_label": ("GSI from", "GSI kaynağı"),
    "gsi_source_direct": ("value entered", "girilen değer"),
    "gsi_source_chart": ("chart: structure and surface", "abak: yapı ve yüzey"),
    "gsi_source_jcond": ("JCond89 and RQD", "JCond89 ve RQD"),
    "gsi_source_rmr": ("RMR89", "RMR89"),
    "gsi_source_q": ("Q' (Barton)", "Q' (Barton)"),
    "gsi_source_cai": ("block volume and joint condition", "blok hacmi ve süreksizlik durumu"),
    "GSI_label": ("GSI", "GSI"),
    "structure_label": ("Structure", "Yapı"),
    "surface_label": ("Surface condition", "Yüzey durumu"),
    "JCond89_label": ("Joint condition JCond89 (0–30)", "Süreksizlik durumu JCond89 (0–30)"),
    "RQD_label": ("RQD", "RQD"),
    "RMR89_label": ("RMR89 (dry, unadjusted)", "RMR89 (kuru, düzeltmesiz)"),
    "Q_prime_label": ("Q' = RQD/Jn · Jr/Ja", "Q' = RQD/Jn · Jr/Ja"),
    "Vb_label": ("Block volume Vb", "Blok hacmi Vb"),
    "Jc_label": ("Joint condition factor Jc", "Süreksizlik durum faktörü Jc"),
    "gsi_note": ("The chart's classes are placed on the quantified chart, "
                 "GSI = 1.5·JCond89 + RQD/2 (Hoek, Carter & Diederichs 2013). "
                 "RMR89: GSI = RMR89 − 5; Q': GSI = 9·ln Q' + 44; Vb, Jc: Cai et al. (2004).",
                 "Abak sınıfları sayısallaştırılmış abağa yerleştirilir: "
                 "GSI = 1.5·JCond89 + RQD/2 (Hoek, Carter & Diederichs 2013). "
                 "RMR89: GSI = RMR89 − 5; Q': GSI = 9·ln Q' + 44; Vb, Jc: Cai vd. (2004)."),

    "group_disturbance": ("Disturbance", "Örselenme"),
    "disturbance_case_label": ("Excavation (typical D)", "Kazı (tipik D)"),
    "D_label": ("Disturbance factor D", "Örselenme faktörü D"),
    "disturbance_note": ("D is 0 for undisturbed rock and 1 for rock heavily damaged by "
                         "blasting or stress relief (Hoek et al. 2002).",
                         "D, örselenmemiş kayada 0, patlatma ya da gerilme boşalmasıyla ağır "
                         "hasar görmüş kayada 1'dir (Hoek vd. 2002)."),

    "group_application": ("Application — range of σ3", "Uygulama — σ3 aralığı"),
    "application_label": ("Application", "Uygulama"),
    "application_general": ("General (σ3max = σci/4)", "Genel (σ3max = σci/4)"),
    "application_tunnel": ("Tunnel", "Tünel"),
    "application_slope": ("Slope", "Şev"),
    "application_custom": ("Custom σ3max", "Özel σ3max"),
    "unit_weight_label": ("Unit weight of the rock mass γ", "Kaya kütlesi birim hacim ağırlığı γ"),
    "depth_label": ("Tunnel depth / slope height H", "Tünel derinliği / şev yüksekliği H"),
    "sigma3_max_label": ("Upper limit σ3max", "Üst sınır σ3max"),
    "application_note": ("The equivalent c' and φ' are fitted over σt < σ3 < σ3max; a tunnel "
                         "and a slope set σ3max from σcm and γH (Hoek et al. 2002).",
                         "Eşdeğer c' ve φ', σt < σ3 < σ3max aralığında uydurulur; tünel ve "
                         "şevde σ3max, σcm ve γH'den bulunur (Hoek vd. 2002)."),

    "group_modulus": ("Deformation modulus", "Deformasyon modülü"),
    "modulus_method_label": ("Estimate", "Tahmin"),
    "modulus_generalized": ("Hoek & Diederichs 2006, generalised",
                            "Hoek & Diederichs 2006, genelleştirilmiş"),
    "modulus_simplified": ("Hoek & Diederichs 2006, simplified",
                           "Hoek & Diederichs 2006, basitleştirilmiş"),
    "modulus_hctc2002": ("Hoek, Carranza-Torres & Corkum 2002",
                         "Hoek, Carranza-Torres & Corkum 2002"),
    "Ei_source_label": ("Intact modulus Ei from", "Sağlam kaya modülü Ei"),
    "Ei_source_mr": ("MR · σci", "MR · σci"),
    "Ei_source_direct": ("value entered", "girilen değer"),
    "MR_label": ("Modulus ratio MR = Ei/σci", "Modül oranı MR = Ei/σci"),
    "Ei_label": ("Intact modulus Ei", "Sağlam kaya modülü Ei"),
    "modulus_note": ("The generalised estimate uses Ei; the simplified one and the 2002 one "
                     "need only GSI, D (and σci).",
                     "Genelleştirilmiş tahmin Ei'yi kullanır; basitleştirilmiş ve 2002 "
                     "tahminleri yalnızca GSI, D (ve σci) ister."),

    "group_query": ("Instantaneous strength", "Anlık dayanım"),
    "query_sigma3_label": ("at σ3", "σ3 değerinde"),
    "query_note": ("The tangent to the envelope at this σ3: σ1, σn, τ, φi and ci "
                   "(Balmer 1952).",
                   "Zarfa bu σ3'teki teğet: σ1, σn, τ, φi ve ci (Balmer 1952)."),

    "group_study": ("Study options", "Çalışma seçenekleri"),
    "study_method": ("Sampling", "Örnekleme"),
    "sampling_oat": ("One at a time", "Tek tek"),
    "sampling_lhs": ("Latin hypercube", "Latin hiperküp"),
    "sampling_mc": ("Monte Carlo", "Monte Carlo"),
    "study_n": ("Samples", "Örnek sayısı"),
    "study_seed": ("Random seed (0: random)", "Rastgele tohum (0: rastgele)"),
    "study_note": ("A range is swept (one at a time) or sampled uniformly; a distribution is "
                   "sampled. The 5 % fractile of each strength is its characteristic value.",
                   "Aralık tek tek taranır ya da düzgün örneklenir; dağılım örneklenir. "
                   "Her dayanımın %5 alt değeri karakteristik değeridir."),

    # ------------------------------------------------------------------ tables
    "col_test": ("Test", "Deney"),
    "col_sigma3": ("σ3 [MPa]", "σ3 [MPa]"),
    "col_sigma1": ("σ1 [MPa]", "σ1 [MPa]"),
    "lab_note": ("σ3 = 0 is a uniaxial test; a tensile test enters as σ3 = −σt, σ1 = 0. "
                 "Hoek recommends tests over 0 ≤ σ3 ≤ σci/2.",
                 "σ3 = 0 tek eksenli deneydir; çekme deneyi σ3 = −σt, σ1 = 0 olarak girilir. "
                 "Hoek, 0 ≤ σ3 ≤ σci/2 aralığında deney önerir."),
    "col_param": ("Input", "Girdi"),
    "col_mode": ("Mode", "Tür"),
    "mode_range": ("range", "aralık"),
    "mode_dist": ("distribution", "dağılım"),
    "col_min": ("Min", "En az"),
    "col_max": ("Max", "En çok"),
    "col_dist": ("Distribution", "Dağılım"),
    "dist_normal": ("normal", "normal"),
    "dist_lognormal": ("lognormal", "lognormal"),
    "dist_uniform": ("uniform", "düzgün"),
    "col_mean": ("Mean", "Ortalama"),
    "col_cov": ("CoV", "DK"),
    "col_points": ("Points", "Nokta"),

    # ------------------------------------------------------------------ study variables
    "grp_intact": ("Intact rock", "Sağlam kaya"),
    "grp_rock_mass": ("Rock mass", "Kaya kütlesi"),
    "grp_modulus": ("Modulus", "Modül"),
    "grp_application": ("Application", "Uygulama"),
    "grp_query": ("Instantaneous", "Anlık"),
    "var_sigma_ci": ("σci", "σci"),
    "var_mi": ("mi", "mi"),
    "var_GSI": ("GSI", "GSI"),
    "var_JCond89": ("JCond89", "JCond89"),
    "var_RQD": ("RQD", "RQD"),
    "var_RMR89": ("RMR89", "RMR89"),
    "var_Q_prime": ("Q'", "Q'"),
    "var_Vb": ("Vb", "Vb"),
    "var_Jc": ("Jc", "Jc"),
    "var_D": ("D", "D"),
    "var_Ei": ("Ei", "Ei"),
    "var_MR": ("MR", "MR"),
    "var_unit_weight": ("γ", "γ"),
    "var_depth": ("H", "H"),
    "var_sigma3_max": ("σ3max", "σ3max"),
    "var_sigma3": ("σ3", "σ3"),

    # ------------------------------------------------------------------ study outputs
    "out_c": ("c' [MPa]", "c' [MPa]"),
    "out_phi": ("φ' [°]", "φ' [°]"),
    "out_Erm": ("Erm [MPa]", "Erm [MPa]"),
    "out_sigma_cm": ("σcm [MPa]", "σcm [MPa]"),
    "out_sigma_c": ("σc [MPa]", "σc [MPa]"),
    "out_sigma_t": ("σt [MPa]", "σt [MPa]"),
    "out_sigma3_max": ("σ3max [MPa]", "σ3max [MPa]"),
    "out_mb": ("mb", "mb"),
    "out_s": ("s", "s"),
    "out_a": ("a", "a"),
    "out_c_i": ("ci [MPa]", "ci [MPa]"),
    "out_phi_i": ("φi [°]", "φi [°]"),
    "out_error": ("error", "hata"),

    # ------------------------------------------------------------------ study text
    "study_run": ("Run study", "Çalışmayı başlat"),
    "study_cancel": ("Cancel", "İptal"),
    "study_export_csv": ("Export CSV", "CSV dışa aktar"),
    "study_export_xlsx": ("Export XLSX", "XLSX dışa aktar"),
    "study_vars_group": ("Study variables", "Çalışma değişkenleri"),
    "study_no_vars": ("Add at least one study variable.", "En az bir çalışma değişkeni ekleyin."),
    "study_progress": ("Sample {done} of {total}…", "Örnek {done} / {total}…"),
    "study_done": ("Study finished: {n} samples.", "Çalışma tamamlandı: {n} örnek."),
    "study_cancelled": ("(cancelled)", "(iptal edildi)"),
    "study_failed": ("The study could not start: {e}", "Çalışma başlatılamadı: {e}"),
    "study_no_data": ("No study results yet.", "Henüz çalışma sonucu yok."),
    "study_table_note": ("Only the first 500 samples are shown; export the table for all.",
                         "Yalnızca ilk 500 örnek gösteriliyor; tümü için tabloyu dışa aktarın."),
    "study_fig_oat": ("One-at-a-time sweep", "Tek tek tarama"),
    "study_fig_hist": ("Distribution of the output", "Çıktının dağılımı"),
    "study_fig_scatter": ("Output against the inputs", "Çıktı ve girdiler"),
    "study_fig_tornado": ("Sensitivity", "Duyarlılık"),
    "st_title": ("PARAMETRIC / PROBABILISTIC STUDY", "PARAMETRİK / OLASILIKSAL ÇALIŞMA"),
    "st_info": ("Sampling: {method} · samples: {n} · analysed: {ok}",
                "Örnekleme: {method} · örnek: {n} · çözülen: {ok}"),
    "st_stats_title": ("Statistics of the outputs", "Çıktıların istatistikleri"),
    "st_mean": ("mean", "ortalama"),
    "st_std": ("std", "std"),
    "st_char_title": ("Characteristic values (lower 5 % fractile)",
                      "Karakteristik değerler (%5 alt değer)"),
    "st_char_line": ("{name:<16} P5 = {p5:10.4g}   (mean {mean:.4g})",
                     "{name:<16} P5 = {p5:10.4g}   (ortalama {mean:.4g})"),
    "st_sens_title": ("Sensitivities — Spearman ρ", "Duyarlılıklar — Spearman ρ"),
    "st_no_sens": ("Sensitivities need a sampled (LHS or Monte Carlo) study.",
                   "Duyarlılık için örneklemeli (LHS ya da Monte Carlo) çalışma gerekir."),

    # ------------------------------------------------------------------ actions
    "run_analysis_button": ("Analyse", "Hesapla"),
    "running_analysis": ("Analysing…", "Hesaplanıyor…"),
    "analysis_complete": ("Done.", "Tamamlandı."),
    "report_action": ("Export report…", "Rapor oluştur…"),
    "report_running": ("Writing the report…", "Rapor yazılıyor…"),
    "warnings_title": ("Warnings", "Uyarılar"),

    # ------------------------------------------------------------------ cards
    "card_GSI": ("GSI", "GSI"),
    "card_hb": ("Hoek–Brown constants", "Hoek–Brown sabitleri"),
    "card_c": ("Cohesion c'", "Kohezyon c'"),
    "card_phi": ("Friction angle φ'", "İçsel sürtünme açısı φ'"),
    "card_sigma_t": ("Tensile strength σt", "Çekme dayanımı σt"),
    "card_sigma_c": ("Uniaxial strength σc", "Tek eksenli dayanım σc"),
    "card_sigma_cm": ("Global strength σcm", "Global dayanım σcm"),
    "card_Erm": ("Deformation modulus Erm", "Deformasyon modülü Erm"),
    "card_sigma3_max": ("σ3max", "σ3max"),
    "card_query": ("Instantaneous", "Anlık"),
    "card_fitted": ("fitted up to σ3 = {s3} MPa", "σ3 = {s3} MPa'ya kadar uydurma"),
    "card_query_sub": ("at σ3 = {s3} MPa · ci = {c} MPa", "σ3 = {s3} MPa'da · ci = {c} MPa"),

    # ------------------------------------------------------------------ GSI source lines
    "gsi_from_direct": ("entered", "girildi"),
    "gsi_from_chart": ("chart: {structure}; {surface}", "abak: {structure}; {surface}"),
    "gsi_from_jcond": ("1.5·JCond89 + RQD/2, JCond89 = {J:g}, RQD = {RQD:g} %",
                       "1.5·JCond89 + RQD/2, JCond89 = {J:g}, RQD = %{RQD:g}"),
    "gsi_from_rmr": ("RMR89 − 5, RMR89 = {RMR:g}", "RMR89 − 5, RMR89 = {RMR:g}"),
    "gsi_from_q": ("9·ln Q' + 44, Q' = {Q:g}", "9·ln Q' + 44, Q' = {Q:g}"),
    "gsi_from_cai": ("Cai et al. 2004, Vb = {Vb:g} cm³, Jc = {Jc:g}",
                     "Cai vd. 2004, Vb = {Vb:g} cm³, Jc = {Jc:g}"),

    # ------------------------------------------------------------------ summary tables
    "table_applications": ("Equivalent Mohr–Coulomb strength by application",
                           "Uygulamaya göre eşdeğer Mohr–Coulomb dayanımı"),
    "head_application": ("Application", "Uygulama"),
    "table_moduli": ("Deformation modulus by estimate", "Tahmine göre deformasyon modülü"),
    "head_method": ("Estimate", "Tahmin"),
    "table_residual": ("Peak and residual strength (Cai et al. 2007)",
                       "Pik ve kalıcı dayanım (Cai vd. 2007)"),
    "head_parameter": ("Parameter", "Parametre"),
    "head_peak": ("Peak", "Pik"),
    "head_residual": ("Residual", "Kalıcı"),

    # ------------------------------------------------------------------ results text
    "res_title": ("ROCK MASS STRENGTH — GENERALISED HOEK–BROWN",
                  "KAYA KÜTLESİ DAYANIMI — GENELLEŞTİRİLMİŞ HOEK–BROWN"),
    "res_intact": ("Intact rock", "Sağlam kaya"),
    "res_rock_type": ("rock type", "kaya türü"),
    "res_source": ("σci and mi from", "σci ve mi kaynağı"),
    "res_fit": ("laboratory fit", "laboratuvar uydurması"),
    "res_fit_line": ("{n} tests, r² = {r2:.4f}, σ3 = {lo:g} … {hi:g} MPa",
                     "{n} deney, r² = {r2:.4f}, σ3 = {lo:g} … {hi:g} MPa"),
    "res_mass": ("Rock mass", "Kaya kütlesi"),
    "res_hb": ("Hoek–Brown constants", "Hoek–Brown sabitleri"),
    "res_strength": ("Rock mass strength", "Kaya kütlesi dayanımı"),
    "res_sigma_t": ("tensile strength σt", "çekme dayanımı σt"),
    "res_sigma_c": ("uniaxial compressive strength σc", "tek eksenli basınç dayanımı σc"),
    "res_sigma_cm": ("global strength σcm", "global dayanım σcm"),
    "res_mc": ("Equivalent Mohr–Coulomb strength", "Eşdeğer Mohr–Coulomb dayanımı"),
    "res_application": ("application", "uygulama"),
    "res_c": ("cohesion c'", "kohezyon c'"),
    "res_phi": ("friction angle φ'", "içsel sürtünme açısı φ'"),
    "res_mc_ucs": ("uniaxial strength of the line", "doğrunun tek eksenli dayanımı"),
    "res_mc_tension": ("tensile strength of the line", "doğrunun çekme dayanımı"),
    "res_modulus": ("Deformation modulus Erm", "Deformasyon modülü Erm"),
    "res_query": ("Instantaneous strength at σ3 = {s3} MPa",
                  "σ3 = {s3} MPa'da anlık dayanım"),
    "res_phi_i": ("instantaneous friction angle φi", "anlık sürtünme açısı φi"),
    "res_c_i": ("instantaneous cohesion ci", "anlık kohezyon ci"),
    "res_residual": ("Residual strength (Cai et al. 2007)", "Kalıcı dayanım (Cai vd. 2007)"),

    # ------------------------------------------------------------------ figures
    "fig_envelopes": ("Failure envelopes", "Göçme zarfları"),
    "fig_principal": ("Principal stresses σ1–σ3", "Asal gerilmeler σ1–σ3"),
    "fig_shear": ("Shear–normal stress τ–σn", "Kayma–normal gerilme τ–σn"),
    "fig_gsi_chart": ("Quantified GSI chart", "Sayısallaştırılmış GSI abağı"),
    "fig_constants": ("Hoek–Brown constants against GSI", "GSI'ya göre Hoek–Brown sabitleri"),
    "fig_strength_gsi": ("c' and φ' against GSI", "GSI'ya göre c' ve φ'"),
    "fig_modulus": ("Deformation modulus against GSI", "GSI'ya göre deformasyon modülü"),
    "fig_disturbance": ("Effect of the disturbance factor D", "Örselenme faktörü D'nin etkisi"),
    "fig_labfit": ("Laboratory tests and the intact envelope",
                   "Laboratuvar deneyleri ve sağlam kaya zarfı"),
    "leg_hb": ("Hoek–Brown", "Hoek–Brown"),
    "leg_mc": ("Mohr–Coulomb  c' = {c:.3g} MPa, φ' = {phi:.1f}°",
               "Mohr–Coulomb  c' = {c:.3g} MPa, φ' = {phi:.1f}°"),
    "leg_residual": ("Residual (Cai et al.)", "Kalıcı (Cai vd.)"),
    "leg_tangent": ("Tangent  ci = {c:.3g} MPa, φi = {phi:.1f}°",
                    "Teğet  ci = {c:.3g} MPa, φi = {phi:.1f}°"),
    "leg_c": ("c'", "c'"),
    "leg_phi": ("φ'", "φ'"),
    "leg_intact": ("Intact rock  σci = {sci:.1f} MPa, mi = {mi:.1f}",
                   "Sağlam kaya  σci = {sci:.1f} MPa, mi = {mi:.1f}"),
    "leg_tests": ("Tests (n = {n})", "Deneyler (n = {n})"),
    "ax_sigma3": ("Minor principal stress σ3 [MPa]", "Küçük asal gerilme σ3 [MPa]"),
    "ax_sigma1": ("Major principal stress σ1 [MPa]", "Büyük asal gerilme σ1 [MPa]"),
    "ax_sigma_n": ("Normal stress σn [MPa]", "Normal gerilme σn [MPa]"),
    "ax_tau": ("Shear stress τ [MPa]", "Kayma gerilmesi τ [MPa]"),
    "ax_jcond": ("Surface condition — 1.5·JCond89", "Yüzey durumu — 1.5·JCond89"),
    "ax_rqd": ("Structure — RQD/2", "Yapı — RQD/2"),
    "ax_constants": ("mb/mi, s", "mb/mi, s"),
    "ax_c": ("Cohesion c' [MPa]", "Kohezyon c' [MPa]"),
    "ax_phi": ("Friction angle φ' [°]", "Sürtünme açısı φ' [°]"),
    "ax_Erm": ("Erm [GPa]", "Erm [GPa]"),
    "ax_regression": ("(σ1 − σ3)² [MPa²]", "(σ1 − σ3)² [MPa²]"),
    "no_lab_fit": ("No laboratory fit: choose 'fit to triaxial tests'.",
                   "Laboratuvar uydurması yok: 'üç eksenli deneylere uydurma'yı seçiniz."),
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
    """An engine warning, (key, params), as a sentence; a rock type by its name."""
    key, params = warning
    if "rock" in params:
        from .tables import ROCK_TYPES, name
        params = dict(params, rock=name(ROCK_TYPES, params["rock"], lang).lower()
                      if lang == "en" else name(ROCK_TYPES, params["rock"], lang))
    return t(lang, key, **params)
