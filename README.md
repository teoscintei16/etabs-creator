# ETABS Creator

Generează modele ETABS (v22) conforme regulilor, pentru a testa verificatorul [etabs-check](https://github.com/teoscintei16/etabs-check):
cadre, pereți izolați, pereți cuplați, nuclee de pereți (L, C, I, H, T), structuri duale, forme neregulate (L, retragere, goluri),
subsol sub un plan mai mare decât turnul, mai multe turnuri și **planuri libere**: cerc, elipsă, semicerc, poligon, trapez, formă cu lobi,
spline închis prin puncte de control, piramide (reducere netedă sau în trepte), răsucire, înclinare, atriu central, pereți trapezoidali.

Pornește o instanță ETABS **nouă**; nu înlocuiește niciodată modelul unui utilizator deschis în altă instanță.

## Pornire

```
pip install -r requirements.txt
python -m etabs_creator          # http://127.0.0.1:8766
```

Modelele se salvează în `generated_models/`, iar parametrii seismici și centurile se scriu în setările verificatorului
(`<model>.EDB.checks.json`).

## Structura codului (fișiere mici, pe subiect)

| Folder | Rol |
|---|---|
| `spec/` | specificația modelului, în părți mici (grilă, secțiuni, încărcări, rigiditate, seism, pereți, subsol, formă, turnuri) |
| `plan/` | planul construcției ortogonale, calcule pure (niveluri, turnuri, celule, pereți, nuclee, subsol) |
| `free/` | planul liber, calcule pure: contur (cerc, spline…), rețea radială de inele, transformări pe nivel (piramidă, răsucire) |
| `seismic/` | spectrul P100-1, coeficientul seismic, combinațiile (pure) |
| `build/` | crearea obiectelor în ETABS, nivel cu nivel (stâlpi/grinzi, pereți, subsol, planșee, rezemare) |
| `rules/` | regulile aplicate după geometrie: fisurare, zone rigide, mesh, masă, moduri, spectru, forțe statice, combinații, calibrare |
| `defects/` | defecte intenționate (`defects=nume1,nume2`) pentru a testa reparațiile verificatorului: moduri puține, Ritz fără accelerații, DOF oprite, mesh nestandard etc. |
| `shells/` | coji sferice cu coaste (Opera din Sydney): centrul sferei din 3 varfuri, reteaua petecului, amplasarea salilor si a cojilor pe grila podiumului (calcule pure; vezi `docs/OPERA_CONCEPT.md`) |
| `server/` | API FastAPI (`recovery.py`: ETABS repornit la fiecare 8 modele și reîncercare la „Invalid pointer”) și pagina simplă (`static/`) |

Mesh-ul plăcilor: `mesh_floor=auto` → „General” la planuri libere (Rectangular lasă elemente-ciobuc), altfel „Rectangular”.
Opera: `structure=opera` (podium + 2 sali + 14 coji sferice cu coaste, 4 niveluri de coji, vant si temperatura); presetarea completa si rularea de la cap la cap: `scripts/opera.py` din proiectul etabs-check.
Testarea cu verificatorul (matrice de structuri, reparații de la cap la cap): `scripts/` din proiectul etabs-check.

Testele nu au nevoie de ETABS (obiecte false): `python -m unittest discover -s tests -t .`

## Descoperiri despre API-ul ETABS

- `ApplyEditedTables` **înlocuiește tabelul întreg**: înregistrările netrimise se șterg din model. Fiecare scriere citește tabelul complet.
- Pe un model blocat (analizat), editarea tabelelor este ignorată în tăcere.
- `FrameObj.SetEndLengthOffset` ignoră factorul de zonă rigidă la decalaj automat: se scrie tabelul „End Length Offsets”.
- Pereții cu „Default” la mesh rămân un singur element pe panou: se folosește „Auto Rectangular”.
- Tiparul seismic se creează întâi prin API, apoi se completează tabelul „User Coefficient”.

## Limitări cunoscute

- **Mai multe turnuri:** turnurile fizice (dreptunghiuri din grila totală, fiecare cu etajele lui) se desenează într-un singur „tower” ETABS. API-ul ETABS
  alocă obiectele nivelurilor primului tower indiferent de `Tower.SetActiveTower`, deci turnurile ETABS definite (`T1-…`, `T2-…`) nu se pot desena din API.
  Verificatorul semnalează corect „corpuri independente ≠ turnuri definite”.
- Împingerea pământului e uniformă (simplificare); sensul se verifică vizual.
- Parametrii seismici impliciți sunt orientativi (fără oraș): introdu valorile amplasamentului.
- **Plan liber:** rețeaua e radială (inele de la centru la contur); conturul trebuie să fie stelat față de centroid. Coordonatele se rotunjesc la 1 mm.
  ETABS acceptă etichete Pier doar pe pereți verticali: panourile înclinate (piramida cu reducere netedă) sunt „rampe” cu proprietate Wall, fără Pier.
  Piramida în trepte are elemente verticale pe fiecare etaj, deci reazemă pe placă la fiecare treaptă (verificatorul semnalează corect lipsa continuității).
  Stâlpii înclinați peste ~15° sunt clasificați de ETABS drept contravântuiri.
