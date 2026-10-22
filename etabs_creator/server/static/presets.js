// Presetari pe tipul de structura: valorile se pun in formular si pot fi modificate dupa aceea.
const NO_WALLS = { walls: false, core_shape: "", coupling_bays_x: "", coupling_bays_y: "", shape: "rect", void_cells: "", towers: "" };
const WALLS_OFF = { wall_lines_x: "none", wall_bays_x: "none", wall_lines_y: "none", wall_bays_y: "none" };

const PRESETS = {
  cadre: { ...NO_WALLS },
  pereti_izolati: { ...NO_WALLS, walls: true, wall_lines_x: "first,last", wall_bays_x: "middle", wall_lines_y: "first,last", wall_bays_y: "middle" },
  pereti_cuplati: { ...NO_WALLS, walls: true, wall_lines_x: "first,last", wall_bays_x: "first,last", wall_lines_y: "none", wall_bays_y: "none", coupling_bays_x: "all" },
  dual: { ...NO_WALLS, walls: true, wall_lines_x: "first,last", wall_bays_x: "middle", wall_lines_y: "none", wall_bays_y: "none" },
  nucleu: { ...NO_WALLS, ...WALLS_OFF, walls: true, core_shape: "C", core_cells: "" },
  neregulat: { ...NO_WALLS, shape: "L", cut_bays: 1, cut_travei: 1, void_cells: "1,1" },
  turnuri: { ...NO_WALLS, bays: 7, travei: 3, towers: "0,0,3,3,6;4,0,3,3,9", basement: 2 },
};

function applyPreset(name) {
  for (const [k, v] of Object.entries(PRESETS[name] || {})) {
    const el = document.getElementById("f_" + k);
    if (!el) continue;
    if (el.type === "checkbox") el.checked = !!v; else el.value = v;
  }
}
