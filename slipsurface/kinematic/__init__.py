"""
SlipSurface IQ Kinematic — kaya şevi kinematiği ve stabilitesi (web tabanlı).

İki adımlı bir iş akışı sunar:

    1. Kinematik tarama  — Markland testi, stereonet, kutup yoğunluğu ve
                           Monte Carlo olasılık analizi
    2. Limit denge       — kama / düzlemsel / devrilme analizi, bulon karelaj ve
                           boy tasarımı, PDF rapor

Arayüz, tarayıcıdan sürülen yerel bir web sunucusudur (yalnızca standart
kütüphane); bu sayede uzak oturumda veya kapsayıcı içinde de çalışır.

Paket düzeni
------------
    slipsurface.kinematic.i18n        dil anahtarı; çift dilli metin yardımcısı
    slipsurface.kinematic.stereonet   ortak alt yarımküre stereonet projeksiyonu
    slipsurface.kinematic.kinematics  kinematik tarama çekirdeği (Markland + Monte Carlo)
    slipsurface.kinematic.rockslope   limit denge çekirdeği (Hoek & Bray, Goodman & Bray)
    slipsurface.kinematic.forms       girdi şeması ve okuyucuları (arayüzden bağımsız)
    slipsurface.kinematic.web         yerel web sunucusu ve tarayıcı arayüzü

Çalıştırma:  slipsurface-kinematic        (veya  python -m slipsurface.kinematic)
"""

from .. import __version__ as __version__  # one version for the whole suite

APP_NAME = "SlipSurface IQ Kinematic"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
