"""Public PluginSpec contract. DSP Brain must not import DPF."""
from .spec import ChainStage, Parameter, PluginSpec, probe_spec

__all__ = ["ChainStage", "Parameter", "PluginSpec", "probe_spec"]
