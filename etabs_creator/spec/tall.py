"""Turn foarte inalt (inspirat de Burj Khalifa): plan in Y cu miez hexagonal, retrageri in spirala, zone de sectiuni, niveluri tehnice, spire de otel.
Vezi docs/BURJ_CONCEPT.md."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


@dataclass
class TallSpec:
    tall: bool = False                      # turn in Y (cere presetarea „turn_inalt”)
    tall_levels: int = 156                  # niveluri de beton peste teren
    tall_spire_levels: int = 7              # niveluri de spire din otel deasupra
    tall_top_concrete: float = 601.0        # m: cota varfului ultimului nivel de beton
    tall_top: float = 828.0                 # m: cota varfului spirei
    lobby_height: float = 8.0               # m: nivelul 1
    mech_levels: str = "17,40,73,109,136,156"
    mech_height: float = 6.0
    core_radius: float = 6.0                # m: raza circumscrisa a miezului hexagonal
    wing_halfwidth: float = 12.0            # m: jumatate din latimea unei aripi (v = ±)
    corridor_half: float = 1.8              # m: peretii de coridor sunt la v = ±
    wing_bay: float = 4.5                   # m: travee de-a lungul aripii
    wing_bays: int = 7                      # travei pe aripa la baza
    setback_start: int = 26                 # nivelul de la care incep retragerile in spirala
    setback_every: int = 6                  # un nivel de retragere (o travee mai scurta la o aripa) la fiecare atatea niveluri
    zones: str = ("1-40:C80/95:1.30:1.4:0.30;41-73:C70/85:1.10:1.2:0.28;74-109:C60/75:0.90:1.0:0.25;"
                  "110-136:C50/60:0.70:0.9:0.25;137-156:C50/60:0.50:0.8:0.25")      # „de-la-pana:beton:perete:stalp:placa”
    occupancy: str = ("1-3:MALL;4-16:HOTEL;18-39:REZID;41-72:REZID;74-108:REZID;110-122:BIROU;123-124:OBSERV;125-135:BIROU;137-155:BIROU")
    load_sets: str = "MALL:2.5:5.0;HOTEL:2.0:2.0;REZID:2.2:2.0;BIROU:2.0:3.0;OBSERV:2.0:5.0;TEHNIC:3.0:7.5;PARCARE:1.0:2.5"   # „nume:permanent:utila” (kN/m2)
    facade_load: float = 1.2                # kN/m2 de fatada (× inaltimea nivelului) ca sarcina liniara pe grinzile de perimetru
    tall_wind_q10: float = 0.8              # kN/m2: presiunea dinamica de referinta la 10 m
    tall_wind_alpha: float = 0.16           # exponentul profilului de vant: q(z) = q10 · (z/10)^(2α)
    tall_stage_every: int = 12              # niveluri pe etapa de executie (caz etapizat CONSTR); 0 = fara constructie etapizata
    tall_temp: float = 20.0                 # °C: variatie uniforma de temperatura pe grinzile de perimetru (tiparul Temp); 0 = fara
    tall_wind_cf: float = 1.2               # coeficient de forta (vant pe fata expusa + sucțiune)

    def validate(self) -> None:
        if not self.tall:
            return
        if not 4 <= self.tall_levels <= 300 or not 1 <= self.tall_spire_levels <= 30:
            raise GenError("Niveluri de beton 4–300, niveluri de spire 1–30.")
        if self.tall_top_concrete <= self.lobby_height or self.tall_top <= self.tall_top_concrete:
            raise GenError("Cotele trebuie să crească: lobby < vârful betonului < vârful spirei.")
        for f in ("lobby_height", "mech_height", "core_radius", "wing_halfwidth", "corridor_half", "wing_bay", "tall_wind_q10", "tall_wind_cf"):
            if getattr(self, f) <= 0:
                raise GenError(f"„{f}” trebuie să fie pozitiv.")
        if not 1 <= self.wing_bays <= 20 or self.setback_every < 1 or self.setback_start < 2:
            raise GenError("Travei pe aripă 1–20, retragere la ≥ 1 nivel, începutul retragerilor ≥ nivelul 2.")
        if not self.corridor_half < self.core_radius / 2 < self.wing_halfwidth:
            raise GenError("Trebuie: semi-coridor < jumătate din fața miezului < semi-lățimea aripii.")
        if self.facade_load < 0 or self.tall_wind_alpha < 0:
            raise GenError("Încărcarea de fațadă și exponentul vântului trebuie să fie nenegative.")
