"""Obiecte false pentru ETABS (fara COM): inregistreaza apelurile si imita tabelele editabile (ApplyEditedTables inlocuieste tabelul intreg)."""


class Rec:
    """Inregistreaza apelurile; AddByCoord intoarce nume incrementale."""

    def __init__(self, store, prefix=""):
        self._s, self._p = store, prefix

    def __getattr__(self, name):
        def call(*a):
            self._s["calls"].append((self._p + name, a))
            if name == "AddByCoord":
                self._s["n"] += 1
                if self._p.startswith("AreaObj"):
                    return [a[1], a[2], a[3], f"A{self._s['n']}", 0]        # ca in COM real: tablourile ref sunt returnate
                self._s.setdefault("frames", []).append(f"O{self._s['n']}")
                return [f"O{self._s['n']}", 0]
            if name == "GetPoints":
                if self._p.startswith("AreaObj"):
                    return [4, tuple(f"{a[0]}{c}" for c in "abcd"), 0]
                return [f"P{a[0]}a", f"P{a[0]}b", 0]
            return 0
        return call


class FakeTables:
    """DatabaseTables fals: ApplyEditedTables inlocuieste tabelul intreg, ca in ETABS."""

    def __init__(self, frames_ref=lambda: []):
        self.frames_ref = frames_ref
        self.t = {
            "Analysis Options - Automatic Mesh Settings for Floors": (["MeshOpt", "Localized", "MergeJoints", "MaxMeshSize"],
                                                                      [dict(MeshOpt="General", Localized="No", MergeJoints="No", MaxMeshSize="1.25")]),
            "Analysis Options - Automatic Rectangular Mesh Options for Walls": (["MaxMeshSize"], [dict(MaxMeshSize="1.25")]),
            "Area Assignments - Floor Auto Mesh Options": (["UniqueName", "MeshOption", "Restraints"],
                                                           [dict(UniqueName="1", MeshOption="Default", Restraints="No")]),
            "Area Assignments - Wall Auto Mesh Options": (["UniqueName", "MeshOption", "Restraints"],
                                                          [dict(UniqueName="W1", MeshOption="Default", Restraints="No")]),
            "Frame Assignments - End Length Offsets": (["UniqueName", "OffsetOpt", "OffsetI", "OffsetJ", "RigidFact", "SelfWtOpt"], []),
            "Frame Assignments - Insertion Point": (["UniqueName", "CardinalPt"], []),
            "Mass Source Definition": (["Name", "IsDefault", "IncLateral", "IncVertical", "LumpMass", "SourceSelf", "SourceAdded", "SourceLoads",
                                        "MoveMass", "LoadPattern", "Multiplier"], [dict(Name="MsSrc1", SourceLoads="No")]),
            "Functions - Response Spectrum - User Defined": (["Name", "Period", "Value", "DampRatio"], [dict(Name="UnifRS", Period="0", Value="1", DampRatio="0.05")]),
            "Load Pattern Definitions - Auto Seismic - User Coefficient": (["Name", "IsAuto", "XDir", "XDirPlusE", "XDirMinusE", "YDir", "YDirPlusE",
                                                                           "YDirMinusE", "EccRatio", "TopStory", "BotStory", "C", "K"], []),
        }
        self.pending = []
        self.modal = [dict(Mode=1, Period=0.9, UX=0.0, UY=0.7), dict(Mode=2, Period=0.5, UX=0.6, UY=0.0), dict(Mode=3, Period=0.4, UX=0.0, UY=0.01)]

    def seed_frames(self, names, key):
        """Dupa fiecare AddByCoord ETABS adauga cate o linie in tabelele pe bare (decalaje, punct de insertie), o singura data."""
        if self.t[key][1]:
            return
        if key == "Frame Assignments - End Length Offsets":
            self.t[key][1][:] = [dict(UniqueName=n, OffsetOpt="Auto", OffsetI="0.25", OffsetJ="0.25", RigidFact="0", SelfWtOpt="Auto") for n in names]
        else:
            self.t[key][1][:] = [dict(UniqueName=n, CardinalPt="10 (Centroid)") for n in names]

    def GetTableForEditingArray(self, key, g, v, f, n, d):
        if key in ("Frame Assignments - End Length Offsets", "Frame Assignments - Insertion Point"):
            self.seed_frames(self.frames_ref(), key)
        if key not in self.t:
            return [0, (), 0, (), 1]
        fields, rows = self.t[key]
        return [1, tuple(fields), len(rows), tuple(str(r.get(f, "")) for r in rows for f in fields), 0]

    def SetTableForEditingArray(self, key, v, fields, n, data):
        self.pending.append((key, list(fields), n, list(data)))
        return [v, 0]

    def ApplyEditedTables(self, log, a, b, c, d, e):
        for key, fields, n, data in self.pending:
            self.t[key] = (fields, [dict(zip(fields, data[i * len(fields):(i + 1) * len(fields)])) for i in range(n)])
        self.pending = []
        return [0, 0, 0, 0, "", 0]

    def GetTableForDisplayArray(self, key, g, grp, v, f, n, d):
        if key != "Modal Participating Mass Ratios":
            return [(), 0, (), 1]
        rows = self.modal
        fields = ("Mode", "Period", "UX", "UY")
        return [0, 0, fields, len(rows), tuple(str(r[f]) for r in rows for f in fields), 0]

    def CancelTableEditing(self):
        return 0


class FakeSap:
    def __init__(self, filename=""):
        self.s = {"calls": [], "n": 0}
        self.filename = filename
        for n in ("File", "PropMaterial", "PropFrame", "PropArea", "FrameObj", "AreaObj", "PointObj", "Diaphragm", "View", "RespCombo", "PierLabel", "SpandrelLabel", "Analyze"):
            setattr(self, n, Rec(self.s, n + "."))
        self.LoadPatterns = Rec(self.s, "LoadPatterns.")
        self.LoadCases = type("LC", (), {"ModalEigen": Rec(self.s, "ModalEigen."), "ResponseSpectrum": Rec(self.s, "RS.")})()
        self.Story = type("St", (), {"GetNameList": staticmethod(lambda: self.story_names()), "SetStories_2": staticmethod(self.set_stories)})()
        self.DatabaseTables = FakeTables(lambda: self.s.get("frames", []))

    def set_stories(self, base, n, names, heights, *rest):
        self.s["stories"] = (base, list(names), list(heights))
        return 0

    def story_names(self):
        if "stories" in self.s:
            names = tuple(reversed(self.s["stories"][1]))
            return [len(names), names, 0]
        return [3, ("Story3", "Story2", "Story1"), 0]

    def GetModelIsLocked(self):
        return "Analyze.RunAnalysis" in [n for n, _ in self.s["calls"]] and not self.s.get("unlocked")

    def SetModelIsLocked(self, v):
        self.s["unlocked"] = not v
        return 0

    def GetModelFilename(self):
        return self.filename

    def InitializeNewModel(self, u):
        return 0

    def SetPresentUnits(self, u):
        return 0

    def calls(self, name):
        return [a for n, a in self.s["calls"] if n == name]


def build(spec_kwargs=None, out_path=None, **flat):
    """Construieste un model pe un FakeSap si intoarce (sap, rezultat). Calibrarea statica e oprita daca nu se cere explicit."""
    from etabs_creator.build import build_model
    from etabs_creator.spec import ModelSpec
    flat = {**(spec_kwargs or {}), **flat}
    flat.setdefault("calibrate_static", False)
    sap = FakeSap()
    return sap, build_model(sap, ModelSpec.from_flat(flat), out_path)
