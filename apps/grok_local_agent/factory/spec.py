"""Framework-independent PluginSpec. DSP Brain must not import DPF."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Parameter:
    id: str
    name: str
    type: str = "float"
    min: float = 0.0
    max: float = 1.0
    default: float = 0.5
    unit: str = ""
    curve: str = "linear"
    smoothing: bool = True
    automatable: bool = True
    version_introduced: str = "0.1.0"

    def contract(self) -> dict:
        return asdict(self)


@dataclass
class ChainStage:
    id: str
    kind: str
    notes: str = ""


@dataclass
class PluginSpec:
    plugin: str
    uri: str
    brand: str = "WARLOCK"
    vendor: str = "WARLOCK Plugins"
    plugin_type: str = "utility"
    category: str = "Utility"
    version: str = "0.1.0"
    framework: str = "DPF"
    formats: list[str] = field(default_factory=lambda: ["VST3"])
    oversampling: int = 1
    oversampling_profile: str = "ECO"
    latency_policy: str = "report-actual"
    inputs: int = 2
    outputs: int = 2
    has_ui: bool = False
    unique_id: str = "WPRB"
    parameters: list[Parameter] = field(default_factory=list)
    chain: list[ChainStage] = field(default_factory=list)
    template: str = "utility"
    template_version: str = "1"

    def to_dict(self) -> dict:
        return asdict(self)

    def manifest(self) -> dict:
        return {
            "name": self.plugin,
            "vendor": self.vendor,
            "framework": self.framework,
            "formats": list(self.formats),
            "version": self.version,
            "category": self.category,
            "oversampling": self.oversampling,
            "presets": True,
            "installer": "NSIS",
            "unique_id": self.unique_id,
            "parameter_ids": [p.id for p in self.parameters],
        }

    def validate(self) -> dict:
        errors = []
        ids = [p.id for p in self.parameters]
        if len(ids) != len(set(ids)):
            errors.append("duplicate parameter id")
        if not self.plugin.strip():
            errors.append("empty name")
        if self.framework != "DPF" and self.template != "legacy":
            errors.append("new factory plugins must default DPF")
        if "VST3" not in self.formats:
            errors.append("first production target is VST3")
        return {"ok": not errors, "errors": errors}


def probe_spec() -> PluginSpec:
    """Tiny factory proof. Not THALL."""
    return PluginSpec(
        plugin="WARLOCK Factory Test",
        uri="https://warlock.audio/plugins/factory-test",
        plugin_type="utility",
        category="Utility",
        unique_id="WPRB",
        template="utility",
        parameters=[
            Parameter("GAIN", "Gain", min=0.0, max=4.0, default=1.0, smoothing=True),
            Parameter("OUTPUT", "Output", min=0.0, max=2.0, default=1.0, smoothing=True),
            Parameter("BYPASS", "Bypass", type="bool", min=0.0, max=1.0, default=0.0, smoothing=False),
        ],
        chain=[
            ChainStage("in", "input"),
            ChainStage("gain", "gain", "x * GAIN"),
            ChainStage("clip", "softclip", "tanh"),
            ChainStage("output", "gain", "x * OUTPUT"),
            ChainStage("bypass", "bypass"),
        ],
    )
