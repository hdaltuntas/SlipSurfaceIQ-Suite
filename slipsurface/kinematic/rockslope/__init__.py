"""
slipsurface.kinematic.rockslope — kaya şevi limit denge çekirdeği (Hoek & Bray, Goodman & Bray)

SlipSurface IQ Kinematic modülünün limit denge hesaplarını yapar; arayüzden bağımsızdır.

Modüller:
  core      : ortak vektör/geometri yardımcıları
  style     : ortak matplotlib stili
  wedge     : tetrahedral kama analizi (Swedge karşılığı) + stereonet
  planar    : düzlemsel kayma (RocPlane karşılığı)
  toppling  : blok devrilmesi, su dahil (RocTopple karşılığı)
  bolts     : bulon karelaj/boy tasarımı ve kapasite kontrolü
  report    : profesyonel PDF rapor
"""
from .bolts import (
                   STANDARD_LENGTHS,
                   BoltCheck,
                   BoltPattern,
                   BoltSpec,
                   bolt_check_planar,
                   bolt_check_wedge,
                   bolt_options_table,
                   bolt_pattern_planar,
                   bolt_pattern_wedge,
)
from .core import (
                   down_dip_vector,
                   intersect_3_planes,
                   plane_normal,
                   polygon_area,
                   trend_plunge_vector,
                   unit,
                   vector_to_trend_plunge,
)
from .planar import PlanarInput, PlanarResult, planar_analyze, planar_required_support, plot_planar
from .report import METHOD, METHOD_TEXT, PROJECT_FIELDS, PROJECT_LABEL, Report
from .toppling import (
                   TopplingInput,
                   TopplingResult,
                   plot_toppling,
                   toppling_analyze,
                   toppling_required_support,
)
from .wedge import (
                   Joint,
                   Plane,
                   Seismic,
                   Support,
                   SupportResult,
                   TensionCrack,
                   Water,
                   WedgeGeometry,
                   WedgeInput,
                   WedgeResult,
                   analyze,
                   build_wedge,
                   hoek_bray_short,
                   optimum_support_direction,
                   plot_stereonet,
                   plot_wedge,
                   required_support,
)

__version__ = "1.0.0"
