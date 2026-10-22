# ETABS Creator

Generează modele ETABS (v22) conforme regulilor, pentru a testa verificatorul [etabs-check](https://github.com/teoscintei16/etabs-check):
cadre, pereți izolați, pereți cuplați, nuclee de pereți (L, C, I, H, T), structuri duale, forme neregulate (L, retragere, goluri),
subsol sub un plan mai mare decât turnul și mai multe turnuri.

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
| `plan/` | planul construcției, calcule pure (niveluri, turnuri, celule, pereți, nuclee, subsol) |
| `seismic/` | spectrul P100-1, coeficientul seismic, combinațiile (pure) |
| `build/` | crearea obiectelor în ETABS, nivel cu nivel (stâlpi/grinzi, pereți, subsol, planșee, rezemare) |
| `rules/` | regulile aplicate după geometrie: fisurare, zone rigide, mesh, masă, moduri, spectru, forțe statice, combinații, calibrare |
| `server/` | API FastAPI și pagina simplă (`static/`) |

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
