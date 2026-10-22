// Presetari pe tipul de structura: valorile se pun in formular si pot fi modificate dupa aceea.
const FREE_OFF = { free_shape: "", free_wall_edges: "none", taper: 0, step_every: 0, twist_deg: 0, lean_x: 0, lean_y: 0, atrium: 0, free_columns: "all" };
const NO_WALLS = { walls: false, core_shape: "", coupling_bays_x: "", coupling_bays_y: "", shape: "rect", void_cells: "", towers: "", ...FREE_OFF };
const FREE_WALLS = { ...NO_WALLS, walls: true, free_wall_edges: "all", free_columns: "all" };
const WALLS_OFF = { wall_lines_x: "none", wall_bays_x: "none", wall_lines_y: "none", wall_bays_y: "none" };

const PRESETS = {
  cadre: { ...NO_WALLS },
  pereti_izolati: { ...NO_WALLS, walls: true, wall_lines_x: "first,last", wall_bays_x: "middle", wall_lines_y: "first,last", wall_bays_y: "middle" },
  pereti_cuplati: { ...NO_WALLS, walls: true, wall_lines_x: "first,last", wall_bays_x: "first,last", wall_lines_y: "none", wall_bays_y: "none", coupling_bays_x: "all" },
  dual: { ...NO_WALLS, walls: true, wall_lines_x: "first,last", wall_bays_x: "middle", wall_lines_y: "none", wall_bays_y: "none" },
  nucleu: { ...NO_WALLS, ...WALLS_OFF, walls: true, core_shape: "C", core_cells: "" },
  neregulat: { ...NO_WALLS, shape: "L", cut_bays: 1, cut_travei: 1, void_cells: "1,1" },
  cerc: { ...NO_WALLS, free_shape: "circle", free_radius: 12 },
  semicerc: { ...NO_WALLS, free_shape: "semicircle", free_radius: 14 },
  elipsa: { ...NO_WALLS, free_shape: "ellipse", free_radius: 14, free_radius_y: 8 },
  spline: { ...NO_WALLS, free_shape: "spline" },
  trapez: { ...FREE_WALLS, free_shape: "trapezoid" },
  piramida: { ...FREE_WALLS, free_shape: "polygon", free_sides: 4, free_radius: 14, taper: 0.7, stories: 8 },
  piramida_trepte: { ...NO_WALLS, free_shape: "polygon", free_sides: 4, free_radius: 14, step_every: 2, step_scale: 0.8, stories: 8 },
  turnuri: { ...NO_WALLS, bays: 7, travei: 3, towers: "0,0,3,3,6;4,0,3,3,9", basement: 2 },
};

function applyPreset(name) {
  for (const [k, v] of Object.entries(PRESETS[name] || {})) {
    const el = document.getElementById("f_" + k);
    if (!el) continue;
    if (el.type === "checkbox") el.checked = !!v; else el.value = v;
  }
}
