# Pre-concept structural: „Turn” (inspirat de Burj Khalifa, 828 m)

Scris înainte de a desena în ETABS. Scop: o structură extrem de înaltă, realistă ca sistem, care să arate ce funcții îi mai lipsesc motorului
(secțiuni pe zone de înălțime, înălțimi de nivel variabile, seturi de încărcări pe ocupare, vânt pe înălțime, material oțel pentru spire, niveluri tehnice).
Nu e o copie dimensională exactă: e un model structural cu aceleași idei (miez hexagonal contravântuit de aripi, retrageri în spirală, beton de clase mari,
niveluri tehnice cu centuri, spire din oțel).

## 1. Faptele de pornire (ordine de mărime)
- 163 de niveluri, 828 m; beton armat până la nivelul 156 (≈ 600 m), spire din oțel deasupra (≈ 227 m).
- Plan în Y: miez hexagonal central + 3 aripi la 120°; pereții de coridor ai aripilor (contraforții) leagă miezul de stâlpii de la perimetru.
- Retrageri în spirală (câte o aripă se scurtează pe rând): reduc suprafața expusă vântului și „încurcă” vârtejurile.
- Niveluri tehnice (mecanice) cu pereți/centuri de legătură (outriggers) la câteva cote (≈ 17, 40, 73, 109, 136, 156).
- Beton C80 la bază → C60 sus; pereții de la 1,3 m la 0,5 m grosime. Vântul și efectele de ordinul II domină, nu seismul.
- Programe pe înălțime: comerț/lobby la bază, hotel, apartamente, birouri, punte de observație (nivelul 124), spații tehnice.

## 2. Sistemul structural
| Parte | Rol | Model în ETABS |
|---|---|---|
| Miez hexagonal | rigiditate la torsiune și forfecare, axul turnului | 6 pereți (apotema 5,2 m), din care fețele spre aripi au golul coridorului; etichete Pier |
| Pereți de coridor („contraforți”) | duc forța laterală spre perimetru, scurtează stâlpii în flambaj | 2 pereți pe aripă (v = ±1,8 m) de la miez până la vârful aripii |
| Stâlpi de perimetru | gravitație + reazem pentru centurile tehnice | stâlpi la fiecare 4,5 m pe laturile aripilor (v = ±12 m) și la vârf |
| Grinzi și planșee | diafragmă rigidă pe nivel | grinzi pe liniile stâlpilor și la capătul coridoarelor; plăci cvadrilatere pe fâșii |
| Niveluri tehnice | centuri la perimetru (outrigger) | grinzi 1,2 × 3,0 m pe laturile aripilor la nivelurile tehnice, înălțime de etaj 6 m |
| Subsol | 2 niveluri de parcare, pereți perimetrali, miezul continuă | pereți pe conturul Y, împingerea pământului |
| Spire | catarg de oțel | stâlpi-țeavă centrați, 7 niveluri, secțiune descrescătoare; reazem pe „spițe” din oțel de la colțurile miezului |

## 3. Geometria planului (m)
Miez: hexagon cu raza circumscrisă 6,0 (apotema 5,196), fețele cu normalele la 0°, 60°, … Aripile pe axele 0°, 120°, 240°, lățime 24 (v = ±12), pereții de coridor la v = ±1,8.
Punctul de crestătură N = (6,928; 12) e pe raza de 60° care pornește din mijlocul feței miezului (2,598; 4,5) și e comun aripilor vecine. Traveile: 4,5 m, 7 pe aripă la bază (vârf la 38,4 m de centru).
Planșeul = pe fiecare aripă 3 fâșii × travei (v: −12…−1,8…1,8…12) + 3 poligoane de legătură cu miezul; în interiorul miezului nu e planșeu (puțuri).

**Retrageri în spirală:** începând de la nivelul 26, la fiecare 6 niveluri se scurtează cu o travee aripa următoare (0 → 1 → 2 → 0 …), 21 de retrageri până la nivelul ≈ 152;
sus rămâne doar miezul cu zona de legătură (nivelurile 153–156).

## 4. Niveluri
Subsol S2, S1 (4,5 m); nivelul 1 = 8 m (lobby); niveluri tehnice (6 m) la 17, 40, 73, 109, 136, 156; restul = înălțime tipică calculată ca vârful nivelului 156 să fie la ≈ 601 m (≈ 3,74 m);
7 niveluri de spire (≈ 32 m fiecare). Denumiri ETABS: S2, S1, P (= nivelul 1), E1 … (= nivelul 2 …), până la E162. Total: 2 + 163 = 165 niveluri.

## 5. Secțiuni pe zone (grad de beton, grosimea pereților, stâlpi, planșeu)
| Zona | Niveluri | Beton | Perete | Stâlp | Planșeu |
|---|---|---|---|---|---|
| 1 | 1–40 | C80/95 | 1,30 | 1,4 × 1,4 | 0,30 |
| 2 | 41–73 | C70/85 | 1,10 | 1,2 × 1,2 | 0,28 |
| 3 | 74–109 | C60/75 | 0,90 | 1,0 × 1,0 | 0,25 |
| 4 | 110–136 | C50/60 | 0,70 | 0,9 × 0,9 | 0,25 |
| 5 | 137–156 | C50/60 | 0,50 | 0,8 × 0,8 | 0,25 |
Grinzile de cadru 0,6 × 0,9 m peste tot. Fiecare zonă are propriile secțiuni și material (funcție nouă a motorului: secțiuni pe zone).

## 6. Încărcări
- Greutate proprie; **seturi uniforme de încărcare pe ocupare** (Shell Uniform Load Sets) atribuite fiecărei plăci după nivel:
  | Set | Permanent suplimentar | Utilă | Niveluri |
  |---|---|---|---|
  | MALL | 2,5 | 5,0 | 1–3 (comerț) |
  | HOTEL | 2,0 | 2,0 | 4–16 |
  | REZID | 2,2 | 2,0 | 18–39, 41–72, 74–108 |
  | BIROU | 2,0 | 3,0 | 110–122, 125–135, 137–155 |
  | OBSERV | 2,0 | 5,0 | 123–124 |
  | TEHNIC | 3,0 | 7,5 | niveluri tehnice |
  | PARCARE | 1,0 | 2,5 | subsol |
- Fațadă: sarcină liniară permanentă pe grinzile de perimetru = 1,2 kN/m² × înălțimea nivelului (aceeași `Permanenta`).
- **Vânt pe înălțime** (tiparele `Vant_X`, `Vant_Y`): forță pe nivel = q(z) · Cf · B(z) · h, cu q(z) = q₁₀ · (z/10)^(2α) (q₁₀ = 0,8 kN/m², α = 0,16), Cf = 1,2,
  B(z) = lățimea proiectată a planului la nivelul respectiv (scade pe măsură ce aripile se retrag). Forțele se aplică într-un punct al diafragmei (centrul miezului); combinații cu ± și cu permanent favorabil.
- Seism P100-1 (parametrii orientativi ai motorului), cu forțe statice calibrate după T1.
- Împingerea pământului pe pereții de subsol.

## 7. Analiză
Diafragmă rigidă; caz modal Ritz (vectori din UX, UY), 120 de vectori (cerința „3 moduri pe etaj” nu are sens la 165 de niveluri: modelul scrie în setările verificatorului
cerința proprie de moduri pe etaj); mesh 3 m; fisurare ca în restul motorului.

## 8. Ce vrem să aflăm despre motor/verificator
Timp de construire la ~25 000 de obiecte și 165 de niveluri; recuperarea ETABS; ce reguli ale verificatorului nu sunt gândite pentru clădiri înalte
(construcție etapizată la ≥ 15 niveluri, moduri pe etaj, mase pe etaj cu retrageri, torsiune, centuri, continuitate la retrageri); ce funcții lipsesc motorului.

## 9. Simplificări asumate
Nu se modelează: fațada ca elemente, lifturile și puțurile, rotunjirea vârfurilor aripilor, centurile din beton de legătură între stâlpi și miez cu pereți (doar grinzi adânci),
fundația pe piloți, interacțiunea cu terenul, vântul real (tunel aerodinamic), efectele de timp (curgere lentă, contracție), construcția etapizată (vezi rezultate).

## 10. Cum a ieșit (model construit, analizat și verificat în ETABS 22)
Imagine: `docs/burj_etabs.png`. Rulare: `python scripts/burj.py --analyze` (construire ≈ 11 min cu etapizarea, calibrare + analiză ≈ 5 min fiecare, verificările ≈ 10 min).
**Obiecte:** 4038 stâlpi, 11 403 grinzi, 6903 plăci, 6498 + 102 pereți, 6600 centuri dummy, 326 forțe de vânt, 14 etape de construcție cu 35 557 de obiecte în grupuri; 165 niveluri, 828 m. **T1 ≈ 10,7 s** (ordinul de mărime al turnului real, ≈ 11 s).
**Ce a trebuit adăugat motorului** (funcții generale, nu doar pentru turn): secțiuni și materiale pe zone de înălțime (clase C50/60 … C80/95, oțel S355, secțiuni țeavă); niveluri cu înălțimi variabile pe grila de 1 mm; seturi de încărcări uniforme pe ocupare
(*Shell Uniform Load Sets*, o singură scriere de tabel pentru toate plăcile); fațadă ca sarcină liniară; vânt pe înălțime ca forțe pe diafragmă (API-ul `AutoWind` din ETABS 22.1 răspunde −99, deci forțele se aplică direct, cu momentul care le readuce în centru);
temperatură; număr total de moduri/vectori Ritz în loc de „pe etaj”; amplificarea spectrului ca forța tăietoare dinamică să fie ≥ 0,85 din cea statică (P100-1); construcție etapizată (grupuri + caz `CONSTR`, operațiile „Add Structure” și „Load Objects if Added”);
scrierea în setările verificatorului a standardelor proprii ale modelului (mesh, moduri pe etaj) și a constatărilor așteptate (waivers).
**Constatări rămase (legitime, explicate):** torsiune 2,5 la nivelul parter sub forța statică cu excentricitate accidentală (spirala de retrageri și excentricitatea de 5 % din 78 m dau un cuplu mare la bază); etaje „moi” la lobby (8 m) și la nivelurile tehnice (6 m) față de etajele tipice;
salturi de masă la nivelurile tehnice (centuri adânci, 7,5 kN/m² utilă); diafragma rigidă cu raport de deplasări > 1,2 (consecința torsiunii); cazul `CONSTR` (neliniar) nu se rulează implicit.
**Corecții de verificator descoperite:** spire/catarg fără plăci nu intră în comparația de mase; torsiunea se judecă în direcția forței (în direcția perpendiculară deriva medie e neglijabilă); cazurile neliniare ne-rulate nu mai sunt „neterminate”;
secțiunile țeavă se citesc (diametru); amplificarea voită a spectrului e informație (cu limită la ×3), nu eroare; calitatea mesh-ului: plăcile neortogonale cer mesh „General”.
