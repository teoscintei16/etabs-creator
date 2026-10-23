# Pre-concept structural: „Opera” (inspirat de Opera din Sydney)

Document scris **înainte** de a desena în ETABS: stabilește sistemul structural, geometria, încărcările, reazemele, simplificările și ce așteptăm de la
verificator. Modelul generat este o abstractizare realistă, nu o copie a clădirii: scopul e un model mare, cu forme curbe complexe, care să pună la
încercare motorul de creare și verificatorul.

## 1. Ce e Opera din Sydney (faptele de pornire)
- Un **podium** masiv din beton (platformă), cu sălile și spațiile tehnice în interior.
- Deasupra, **cojile** („pânzele”): aranjate în **perechi** care se apleacă una spre alta, în trei grupuri — sala mare de concerte, sala de operă și restaurantul.
- Soluția geometrică a lui Utzon („soluția sferică”): **toate cojile sunt petice ale aceleiași sfere** (rază ≈ 75,2 m). Coastele sunt arce de cerc mare care
  pornesc evantai dintr-un **piedestal** de la bază și se desfac spre muchia frontală. Coastele sunt prefabricate din beton precomprimat; între ele, panouri.
- Înălțimea maximă ≈ 65 m deasupra apei; podiumul ≈ 120 × 180 m în plan.

## 2. Sistemul structural ales pentru model
| Parte | Rol structural | Cum se modelează în ETABS |
|---|---|---|
| Fundație / subsol S1 | încastrare la bază, hol tehnic, pardoseala sălilor la ±0,00 | cadre + planșeu + pereți perimetrali de subsol (motorul existent) |
| Podium (P, E1) | platformă rigidă, contravântuire, reazem pentru coji | stâlpi 1,2 × 1,2 m, grinzi 0,6 × 1,2 m, planșee 0,25 m (motorul ortogonal) |
| Pereți de rigidizare ai podiumului | 60 m pe fațada de nord (y = 180), de la podium la baza modelului: aduc centrul de rigiditate spre masa din nord (fără ei torsiunea e 1,6) | motorul de pereți existent, etichete Pier |
| Cutiile sălilor | pereți de beton 0,5 m în jurul fiecărei săli, din fundație până la nivelul podiumului: sunt **reazemul cojilor** și stabilitatea laterală | panouri de perete cu etichete Pier, segmentate la pasul rețelei cojii |
| Cojile | membrană + placă curbă, grosime 0,25 m, beton | arii (shell-thin) pe rețea de patrulatere de pe sferă |
| Coastele | grinzi curbe pe cojile, o coastă la fiecare 2 coloane de rețea | cadre 0,5 × 1,0 m pe muchiile rețelei |
| Grinda de picior | preia reacțiunea cojii pe toată baza | cadru 1,0 × 2,0 m pe coasta de bază |
| Grinda frontală (rim) | rigidizează muchia liberă BC | cadru 0,8 × 1,4 m |
| Legăturile de coamă | leagă coaja de contra-coajă (perechea) peste golul dintre creste | cadre 0,8 × 1,2 m la fiecare 3 noduri ale muchiei frontale |

Fluxul forțelor: coajă → coaste + grindă frontală → grinda de picior → perete al cutiei sălii (sau stâlpii podiumului la restaurant) → subsol → fundație.
Perechea de coji se sprijină una pe alta prin legăturile de coamă (împotriva ruperii laterale).

## 3. Geometria
**Podiumul:** 12 deschideri × 10 m (X, vest–est, 120 m) și 15 travei × 12 m (Y, sud–nord, 180 m); subsol S1 (−6…0), P (0…6), E1 (6…12 = nivelul podiumului).
**Sălile:** Sala de concerte (vest, axa x = 30) și Sala de operă (est, axa x = 90), fiecare 40 × 96 m (y = 24…120), cu pereții lungi pe liniile x = 10, 50 și 70, 110.
Golurile din planșeele P și E1 corespund sălilor (parter-sală cu planșeul de la ±0,00).
**Cojile:** pe fiecare latură lungă a fiecărei săli, 3 coji în șir (sud→nord), cu baza pe peretele lung:
| rând | lungime bază | înălțime peste podium | aplecare spre axă |
|---|---|---|---|
| 1 | 36 m | 52 m | 14 m |
| 2 | 36 m | 42 m | 12 m |
| 3 | 24 m | 30 m | 10 m |
Sala de operă are înălțimile ×0,85. Restaurantul: o pereche la y = 132…168 pe liniile x = 40 și 80, înălțime 20 m, aplecare 10 m (reazem pe stâlpii podiumului).
Total: 12 + 2 = **14 coji**. Cota maximă ≈ 12 + 52 = 64 m (Sala de concerte).

**Construcția unei coji:** se dau trei puncte: A (vârful evantaiului, virtual, la 12 m sud de baza fizică), B (capătul bazei) și C (creasta). Centrul sferei de rază 75,2 m
care trece prin ele se calculează exact (cercul circumscris + înălțimea pe normala planului). Punctul (s, t) al cojii e `normalizare((1−s)·A + s·((1−t)·B + t·C))` pe sferă;
t = const dă o coastă (cerc mare din A). Rețeaua: rândurile se aleg astfel încât **nodurile bazei să cadă din 2 în 2 m în y**, adică pe liniile grilei podiumului
(12 m = 6 pași); 10 coloane peste coaste. Raportul de aspect maxim al elementelor ≈ 2,8.
Verificat în cod: bazele (A, B) sunt la cota podiumului, pe liniile grilei; creasta sub cota de 67 m; nicio coajă nu depășește intervalul y al rândului ei
(deci cojile unui șir nu se intersectează).

## 4. Niveluri ETABS
S1, P, E1 (podium) + 4 niveluri de coji T1…T4 (câte 13 m, până la 64 m): ele dau forțelor seismice statice și deplasărilor o distribuție pe înălțime.
Obiectele (coji, coaste) trec prin niveluri; ETABS le tratează ca pe niște obiecte între niveluri.

## 5. Încărcări
- Greutate proprie (beton 25 kN/m³): coaja 0,25 m = 6,25 kN/m².
- Permanent suplimentar pe coji (plăci ceramice de acoperire): 1,5 kN/m² (tipar `Permanenta`).
- Utilă: planșee podium 5,0 kN/m² (săli, foaiere); coji 0,5 kN/m² (întreținere).
- Vânt (simplificat, tipare `Vant_X`, `Vant_Y`): presiune 1,2 kN/m² pe proiecția cojilor — în realitate vântul și efectele termice sunt determinante (necesită tunel aerodinamic).
- Seism: parametrii P100-1 din motor (orientativi, fără oraș); forțe statice calibrate după T1 prin ciclul de calibrare al motorului.
- Împingerea pământului pe pereții de subsol (existentă).

## 6. Reazeme
Încastrare la baza S1 (capete de stâlpi și colțuri de perete). Coastele de bază sunt legate de nodurile de sus ale pereților cutiei sălii;
la restaurant, grinda de picior reazemă pe stâlpii podiumului din 12 în 12 m (nodurile grilei).

## 7. Reguli ale verificatorului pe care modelul trebuie să le respecte
Continuitate verticală (cojile pe pereți, pereții până la bază), diafragme pe planșee, tipare cu tipul corect, mesh standard, zone rigide pe bare, număr de moduri suficient
(ridicat pentru că cojile au multe moduri locale), masă participantă ≥ 90 %, etichete Pier, normale de plăci coerente. Constatările **legitime** pe care le așteptăm:
- cojile sunt „obiecte între niveluri”: planșee înclinate, nu diafragme (info);
- raport mare între rigiditățile podiumului și ale cojilor (etaj moale/neregularitate) — corect structural;
- perioade lungi și moduri locale ale cojilor la masa participantă.

## 8. Simplificări asumate (ce NU e modelat)
Coaste prefabricate cu rosturi, precomprimare, sticlă și lamele de pe fețele deschise, scene și scări interioare, fundația pe piloți/chesoane, efecte termice și de vânt reale,
interacțiunea cu sala (acustică). Sălile sunt cutii goale cu planșeul la ±0,00.

## 9. Plan de verificare
1. Teste unitare ale geometriei (puncte pe sferă, colțuri la cote corecte, aspect, aliniere cu grila) și ale constructorului (obiecte false).
2. Construire în ETABS cu motorul; verificatorul „pre”; analiză; verificatorul „post”.
3. Fiecare constatare e clasificată: defect al creatorului (se repară în motor) sau constatare legitimă (se documentează).

## 10. Cum a ieșit (model construit și verificat în ETABS 22)
Imagine: `docs/opera_etabs.png`. Rulare: `python scripts/opera.py --analyze` (construire ≈ 2,5 min cu calibrarea forțelor statice, analiză ≈ 95 s).
**Obiecte:** 486 stâlpi, ≈ 750 grinzi, 412 plăci, ≈ 360 pereți, 2280 elemente de coajă, 1140 coaste, 228 grinzi de picior, 140 frontale, 10 legături de coamă; 14 coji, vârf la 64 m.
**Decizii luate la construcție (față de conceptul inițial):**
- Baza unei coji nu cade pe un plan vertical (arcul de bază al sferei are săgeată ≈ 4 m în plan): baza e „îndreptată” — fiecare rând de noduri se mută pe orizontală pe linia peretelui; muchia frontală rămâne exact pe sferă.
- Vârful evantaiului e tăiat (12 m): altfel elementele de lângă piedestal degenerează (aspect 9 → 2,8).
- Diafragmă rigidă pe podium și caz modal **Ritz** (vectori din UX, UY): cu 120 de moduri Eigen masa participantă rămânea la 75 %, iar cu Ritz (150 vectori) trece de 90 % la modul 125 (X) / 136 (Y). Vectorul pe Z lipsește pentru că sursa de masă nu include masa verticală.
- Pereți de rigidizare de 60 m pe fațada de nord: fără ei raportul de torsiune era 1,63 (eroare), cu ei 1,27 (avertisment).
- Mesh de 2 m (standard verificator 0,5 m; modelul își scrie standardul în setările verificatorului).
**Constatări rămase (legitime):** salt de masă P → S1 (subsolul e mai greu: planșeu complet, pereți și împingerea pământului); torsiune 1,27 la E1 (planul nu e simetric pe Y: sălile încep la 24 m de sud); diafragma rigidă cu goluri mari (4 rezultate cu raport 1,27).
**Corecții de verificator descoperite de acest model:** plăcile înclinate > 15° nu sunt planșee (fără diafragmă); coastele cojilor nu sunt grinzi de cadru (zone rigide, contravântuiri, pantă, punct de inserție); nodurile peretelui pe care reazemă o coajă nu cer centură; nivelurile cu numai coji nu intră în evaluarea masei pe etaj; vectorul Ritz pe Z se cere doar cu masă verticală; mesajul ETABS „zero Ritz starting vectors” e informativ.
