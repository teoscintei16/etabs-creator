"""Opera: podium cu sali si coji sferice cu coaste (inspirat de Opera din Sydney). Vezi docs/OPERA_CONCEPT.md."""
from __future__ import annotations

from dataclasses import dataclass

from ..connect import GenError


def floats(text: str, what: str) -> list[float]:
    try:
        return [float(t) for t in str(text).replace(";", ",").split(",") if t.strip()]
    except ValueError as e:
        raise GenError(f"„{what}”: listă de numere separate prin virgulă (ex. 52,42,30).") from e


@dataclass
class OperaSpec:
    opera: bool = False                     # podium cu sali si coji sferice (cere grila podiumului: vezi presetarea „opera”)
    opera_radius: float = 75.2              # m, raza sferei comune a cojilor (solutia sferica a lui Utzon)
    shell_t: float = 0.25                   # m, grosimea cojii
    shell_dy: float = 2.0                   # m, pasul retelei pe coasta de baza (divide pasul grilei)
    shell_across: int = 10                  # coloane peste coaste
    shell_tip: float = 12.0                 # m, varful evantaiului taiat (piedestalul): distanta de la A la baza fizica
    shell_rib_every: int = 2                # o coasta (grinda) la fiecare atatea coloane
    shell_heights: str = "52,42,30"         # m peste podium, pe randuri (sud -> nord)
    shell_lengths: str = "36,36,24"         # m, lungimea bazei fiecarui rand (multiplu al pasului grilei pe Y)
    shell_leans: str = "14,12,10"           # m, aplecarea crestei spre axa salii
    hall_axes: str = "30,90"                # x al axei fiecarei sali
    hall_half: float = 20.0                 # m, jumatate din latimea salii (peretii lungi la axa ± hall_half)
    hall_y0: float = 24.0                   # m, inceputul salilor pe Y
    hall_scale: str = "1,0.85"              # factor de inaltime pe sala
    restaurant: bool = True                 # perechea de coji a restaurantului, la nord de sali
    restaurant_height: float = 20.0
    restaurant_lean: float = 10.0
    podium_wall_lines: str = "last"         # pereti de rigidizare ai podiumului, paraleli cu X: liniile grilei (first,last / indici); „none” = fara
    podium_wall_bays: str = "3,4,5,6,7,8"   # deschiderile lor (aduc centrul de rigiditate spre masa din partea de nord: fara torsiune excesiva)
    shell_stories: int = 4                  # niveluri deasupra podiumului (distribuie forte seismice pe inaltimea cojilor)
    shell_cladding: float = 1.5             # kN/m2 permanent suplimentar pe coji (placi ceramice)
    shell_live: float = 0.5                 # kN/m2 utila pe coji (intretinere)
    shell_temp: float = 20.0                # °C variatie uniforma de temperatura pe coji (tiparul Temp, cladire de 180 m); 0 = fara
    wind: float = 1.2                       # kN/m2 presiune pe proiectia cojilor (tiparele Vant_X, Vant_Y); 0 = fara

    def validate(self) -> None:
        if not self.opera:
            return
        if self.opera_radius <= 0 or self.shell_t <= 0 or self.shell_dy <= 0 or self.hall_half <= 0:
            raise GenError("Raza sferei, grosimea cojii, pasul rețelei și semi-lățimea sălii trebuie să fie pozitive.")
        if not 4 <= self.shell_across <= 40 or self.shell_rib_every < 1 or not 1 <= self.shell_stories <= 12:
            raise GenError("Coloane peste coaste 4–40, coastă la ≥ 1 coloană, niveluri de coji 1–12.")
        h, n, lean = (floats(getattr(self, k), k) for k in ("shell_heights", "shell_lengths", "shell_leans"))
        if not h or not (len(h) == len(n) == len(lean)):
            raise GenError("Înălțimile, lungimile și aplecările cojilor trebuie să aibă același număr de rânduri (ex. 52,42,30).")
        if not floats(self.hall_axes, "hall_axes") or len(floats(self.hall_scale, "hall_scale")) != len(floats(self.hall_axes, "hall_axes")):
            raise GenError("Axele sălilor și factorii de înălțime trebuie să aibă același număr de valori.")
        if self.shell_cladding < 0 or self.shell_live < 0 or self.wind < 0 or self.shell_temp < 0:
            raise GenError("Încărcările pe coji trebuie să fie nenegative.")
