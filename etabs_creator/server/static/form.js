// Logica paginii: stare ETABS, formular generat din FIELDS, creare model.
const $ = (id) => document.getElementById(id);
let defaults = null;

async function api(url, body) {
  const r = await fetch(url, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || r.statusText);
  return j;
}

function say(text, cls = "") { $("msg").className = cls; $("msg").textContent = text; }

function renderForm(spec) {
  $("form").innerHTML = "";
  for (const [title, fields] of FIELDS) {
    const h = document.createElement("h2"); h.textContent = title; h.className = "grp"; $("form").append(h);
    const g = document.createElement("div"); g.className = "grid"; $("form").append(g);
    for (const [key, label, type] of fields) {
      const l = document.createElement("label"); l.textContent = label;
      let el;
      if (type === "select") {
        el = document.createElement("select");
        for (const o of OPTIONS[key]()) el.add(new Option(o || "(fără)", o));
        if (key === "structure") el.onchange = () => applyPreset(el.value);
      } else { el = document.createElement("input"); el.type = type; if (type === "number") el.step = "any"; }
      el.id = "f_" + key;
      if (type === "checkbox") el.checked = !!spec[key]; else el.value = spec[key] ?? "";
      l.append(el); g.append(l);
    }
  }
}

function readSpec() {
  const s = {};
  for (const [, fields] of FIELDS) for (const [key, , type] of fields) {
    const el = $("f_" + key);
    s[key] = type === "checkbox" ? el.checked : type === "number" ? Number(el.value) : el.value;
  }
  return s;
}

function renderModels(models) {
  $("models").innerHTML = models.length ? "" : '<li class="muted">Niciunul încă.</li>';
  for (const m of models) {
    const li = document.createElement("li");
    const o = m.objects;
    li.textContent = `${m.name} (${m.structure}): ${o.stalpi} stâlpi, ${o.grinzi} grinzi, ${o.placi} plăci — ${m.file}`;
    $("models").append(li);
  }
}

function summary(r) {
  const o = r.objects;
  const extra = [o.pereti ? `${o.pereti} panouri de perete (${r.piers.join(", ")}), ${o.centuri || 0} centuri` : "",
    o.grinzi_cuplare ? `${o.grinzi_cuplare} grinzi de cuplare` : "", o.pereti_subsol ? `${o.pereti_subsol} pereți de subsol` : "",
    r.towers > 1 ? `${r.towers} turnuri` : ""].filter(Boolean);
  return `Gata în ${r.seconds} s: ${o.stalpi} stâlpi, ${o.grinzi} grinzi, ${o.placi} plăci` + (extra.length ? ", " + extra.join(", ") : "") + ".\n"
    + r.notes.map((n) => "• " + n).join("\n") + `\nSalvat: ${r.file}`
    + (r.sidecar ? "\nParametrii seismici" + (r.belts ? " și centurile" : "") + " au fost scriși în setările verificatorului." : "");
}

async function refresh() {
  const s = await api("/api/status");
  $("dot").className = "dot" + (s.open ? " on" : "");
  $("state").textContent = s.open ? `ETABS pornit (v${s.version})${s.file ? " · " + s.file : ""}` : "ETABS nu este pornit";
  $("build").disabled = !s.open; $("close").disabled = !s.open; $("open").disabled = s.open;
  $("hint").textContent = s.open ? "Modelul se salvează în folderul generated_models." : "Pornește mai întâi ETABS.";
}

$("open").onclick = async () => {
  $("open").disabled = true; say("Se pornește ETABS (poate dura ~1 minut)…");
  try { const r = await api("/api/open", {}); say(r.already ? "ETABS era deja pornit." : `ETABS pornit în ${r.seconds} s.`, "okc"); }
  catch (e) { say(e.message, "err"); }
  await refresh();
};
$("close").onclick = async () => { try { await api("/api/close", {}); say("ETABS închis."); } catch (e) { say(e.message, "err"); } await refresh(); };
$("build").onclick = async () => {
  $("build").disabled = true; say("Se creează modelul…");
  try {
    say(summary(await api("/api/build", { spec: readSpec() })), "okc");
    renderModels((await api("/api/defaults")).models);
  } catch (e) { say(e.message, "err"); }
  await refresh();
};

(async () => { defaults = await api("/api/defaults"); renderForm(defaults.spec); renderModels(defaults.models); await refresh(); })();
