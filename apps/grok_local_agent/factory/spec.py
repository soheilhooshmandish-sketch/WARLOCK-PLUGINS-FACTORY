"""Framework-independent PluginSpec. DSP Brain must not import DPF."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Parameter:
    id: str
    name: str
    min: float = 0.0
    max: float = 1.0
    default: float = 0.5
    unit: str = ""


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
    plugin_type: str = "utility"
    framework: str = "DPF"
    oversampling: int = 1
    latency_policy: str = "zero-unless-os"
    inputs: int = 2
    outputs: int = 2
    has_ui: bool = False
    parameters: list[Parameter] = field(default_factory=list)
    chain: list[ChainStage] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def probe_spec() -> PluginSpec:
    """Tiny proof plugin. Not THALL."""
    return PluginSpec(
        plugin="WARLOCK Probe",
        uri="https://warlock.audio/plugins/probe",
        plugin_type="utility",
        framework="DPF",
        oversampling=1,
        parameters=[
            Parameter("GAIN", "Gain", 0.0, 2.0, 1.0),
        ],
        chain=[
            ChainStage("in", "input"),
            ChainStage("gain", "gain", "y = x * GAIN"),
            ChainStage("out", "output"),
        ],
    )
