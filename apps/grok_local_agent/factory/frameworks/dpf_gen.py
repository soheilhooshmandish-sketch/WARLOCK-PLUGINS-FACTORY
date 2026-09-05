"""Generate DPF plugin sources from PluginSpec. Does not clone DPF."""
from __future__ import annotations

from pathlib import Path

from ...config import PROJECT_ROOT
from ..spec import PluginSpec

PROBE = PROJECT_ROOT / "apps" / "grok_local_agent" / "factory" / "probe"


def generate(spec: PluginSpec, dest: Path | None = None) -> dict:
    root = dest or PROBE
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "DistrhoPluginInfo.h": _info(spec),
        "ProbeDSP.cpp": _dsp(spec),
        "CMakeLists.txt": _cmake(spec),
        "Makefile": _make(),
        "README": f"{spec.plugin}\nframework={spec.framework}\nNot THALL. Factory proof plugin.\n",
    }
    written = []
    for name, body in files.items():
        path = root / name
        path.write_text(body, encoding="utf-8")
        written.append(str(path.relative_to(PROJECT_ROOT)))
    return {"ok": True, "framework": "DPF", "dir": str(root), "files": written}


def _info(spec: PluginSpec) -> str:
    return f"""#pragma once
#define DISTRHO_PLUGIN_NAME "{spec.plugin}"
#define DISTRHO_PLUGIN_URI "{spec.uri}"
#define DISTRHO_PLUGIN_HAS_UI 0
#define DISTRHO_PLUGIN_IS_RT_SAFE 1
#define DISTRHO_PLUGIN_NUM_INPUTS {spec.inputs}
#define DISTRHO_PLUGIN_NUM_OUTPUTS {spec.outputs}
#define DISTRHO_PLUGIN_WANT_MIDI_INPUT 0
#define DISTRHO_PLUGIN_WANT_MIDI_OUTPUT 0
#define DISTRHO_PLUGIN_WANT_STATE 1
#define DISTRHO_PLUGIN_IS_SYNTH 0
#define DISTRHO_PLUGIN_BRAND "{spec.brand}"
"""


def _dsp(spec: PluginSpec) -> str:
    return r'''#include "DistrhoPlugin.hpp"

START_NAMESPACE_DISTRHO

class ProbePlugin : public Plugin {
public:
    ProbePlugin() : Plugin(1, 0, 0), fGain(1.0f) {}

protected:
    const char* getLabel() const override { return "WARLOCKProbe"; }
    const char* getDescription() const override { return "WARLOCK factory proof. Not THALL."; }
    const char* getMaker() const override { return "WARLOCK"; }
    const char* getLicense() const override { return "ISC"; }
    uint32_t getVersion() const override { return d_version(0, 1, 0); }
    int64_t getUniqueId() const override { return d_cconst('W', 'P', 'R', 'B'); }

    void initParameter(uint32_t index, Parameter& parameter) override {
        if (index != 0) return;
        parameter.hints = kParameterIsAutomatable;
        parameter.name = "Gain";
        parameter.symbol = "GAIN";
        parameter.ranges.min = 0.0f;
        parameter.ranges.max = 2.0f;
        parameter.ranges.def = 1.0f;
    }

    float getParameterValue(uint32_t index) const override {
        return index == 0 ? fGain : 0.0f;
    }

    void setParameterValue(uint32_t index, float value) override {
        if (index == 0) fGain = value;
    }

    void run(const float** inputs, float** outputs, uint32_t frames) override {
        const float* inL = inputs[0];
        const float* inR = inputs[1];
        float* outL = outputs[0];
        float* outR = outputs[1];
        const float g = fGain;
        for (uint32_t i = 0; i < frames; ++i) {
            outL[i] = inL[i] * g;
            outR[i] = inR[i] * g;
        }
    }

private:
    float fGain;
    DISTRHO_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ProbePlugin)
};

Plugin* createPlugin() { return new ProbePlugin(); }

END_NAMESPACE_DISTRHO
'''


def _cmake(spec: PluginSpec) -> str:
    return """cmake_minimum_required(VERSION 3.15)
project(WARLOCKProbe LANGUAGES CXX)
if(NOT DEFINED ENV{DPF_DIR} AND NOT DEFINED DPF_DIR)
  message(FATAL_ERROR "DPF is missing. Set DPF_DIR. Farnaz will not download it.")
endif()
if(DEFINED ENV{DPF_DIR} AND NOT DEFINED DPF_DIR)
  set(DPF_DIR $ENV{DPF_DIR})
endif()
add_subdirectory(${DPF_DIR} ${CMAKE_BINARY_DIR}/dpf)
# DPF plugins typically use Makefile. This CMake is a gate: fail loud if DPF is absent.
"""


def _make() -> str:
    return """#!/usr/bin/make -f
# Requires DPF next to this folder or DPF_DIR.
NAME = WARLOCKProbe
FILES_DSP = ProbeDSP.cpp
include $(DPF_DIR)/Makefile.plugins.mk
TARGETS += vst3
all: $(TARGETS)
"""
