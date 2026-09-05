"""Generate DPF plugin sources from PluginSpec. Does not clone DPF."""
from __future__ import annotations

import json
from pathlib import Path

from ...config import PROJECT_ROOT
from ..spec import PluginSpec

PROBE = PROJECT_ROOT / "apps" / "grok_local_agent" / "factory" / "probe"


def generate(spec: PluginSpec, dest: Path | None = None) -> dict:
    check = spec.validate()
    if not check["ok"]:
        return {"ok": False, "error": check["errors"]}
    root = dest or PROBE
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "DistrhoPluginInfo.h": _info(spec),
        "ProbeDSP.cpp": _dsp(spec),
        "CMakeLists.txt": _cmake(),
        "Makefile": _make(),
        "warlock-plugin.json": json.dumps(spec.manifest(), indent=2) + "\n",
        "README": (
            f"{spec.plugin}\nframework={spec.framework}\n"
            "Factory proof. Not THALL. Finished binary must not need Farnaz or any AI.\n"
        ),
    }
    written = []
    for name, body in files.items():
        path = root / name
        path.write_text(body, encoding="utf-8")
        written.append(str(path.relative_to(PROJECT_ROOT)))
    return {"ok": True, "framework": "DPF", "dir": str(root), "files": written, "spec": spec.to_dict()}


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
    n = len(spec.parameters)
    return r'''#include "DistrhoPlugin.hpp"
#include <cmath>

START_NAMESPACE_DISTRHO

class ProbePlugin : public Plugin {
public:
    ProbePlugin()
        : Plugin(''' + str(n) + r''', 0, 0),
          fGain(1.0f), fOut(1.0f), fBypass(0.0f),
          sGain(1.0f), sOut(1.0f) {}

protected:
    const char* getLabel() const override { return "WARLOCKFactoryTest"; }
    const char* getDescription() const override {
        return "WARLOCK factory proof. GAIN -> tanh clip -> OUTPUT. Not THALL.";
    }
    const char* getMaker() const override { return "WARLOCK"; }
    const char* getHomePage() const override { return "https://warlock.audio"; }
    const char* getLicense() const override { return "ISC"; }
    uint32_t getVersion() const override { return d_version(0, 1, 0); }
    int64_t getUniqueId() const override { return d_cconst('W', 'P', 'R', 'B'); }

    void initParameter(uint32_t index, Parameter& parameter) override {
        parameter.hints = kParameterIsAutomatable;
        if (index == 0) {
            parameter.name = "Gain"; parameter.symbol = "GAIN";
            parameter.ranges.min = 0.0f; parameter.ranges.max = 4.0f; parameter.ranges.def = 1.0f;
        } else if (index == 1) {
            parameter.name = "Output"; parameter.symbol = "OUTPUT";
            parameter.ranges.min = 0.0f; parameter.ranges.max = 2.0f; parameter.ranges.def = 1.0f;
        } else if (index == 2) {
            parameter.hints |= kParameterIsBoolean | kParameterIsAutomatable;
            parameter.name = "Bypass"; parameter.symbol = "BYPASS";
            parameter.ranges.min = 0.0f; parameter.ranges.max = 1.0f; parameter.ranges.def = 0.0f;
        }
    }

    float getParameterValue(uint32_t index) const override {
        if (index == 0) return fGain;
        if (index == 1) return fOut;
        if (index == 2) return fBypass;
        return 0.0f;
    }

    void setParameterValue(uint32_t index, float value) override {
        if (index == 0) fGain = value;
        else if (index == 1) fOut = value;
        else if (index == 2) fBypass = value;
    }

    void run(const float** inputs, float** outputs, uint32_t frames) override {
        const float* inL = inputs[0];
        const float* inR = inputs[1];
        float* outL = outputs[0];
        float* outR = outputs[1];
        const float a = 0.05f;
        const bool bypass = fBypass >= 0.5f;
        for (uint32_t i = 0; i < frames; ++i) {
            sGain += a * (fGain - sGain);
            sOut  += a * (fOut  - sOut);
            float l = inL[i];
            float r = inR[i];
            if (!bypass) {
                l = std::tanh(l * sGain) * sOut;
                r = std::tanh(r * sGain) * sOut;
            }
            if (!std::isfinite(l)) l = 0.0f;
            if (!std::isfinite(r)) r = 0.0f;
            outL[i] = l;
            outR[i] = r;
        }
    }

private:
    float fGain, fOut, fBypass, sGain, sOut;
    DISTRHO_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ProbePlugin)
};

Plugin* createPlugin() { return new ProbePlugin(); }

END_NAMESPACE_DISTRHO
'''


def _cmake() -> str:
    return """cmake_minimum_required(VERSION 3.15)
project(WARLOCKFactoryTest LANGUAGES CXX)
if(NOT DEFINED ENV{DPF_DIR} AND NOT DEFINED DPF_DIR)
  message(FATAL_ERROR "DPF is missing. Set DPF_DIR. Farnaz will not download it.")
endif()
if(DEFINED ENV{DPF_DIR} AND NOT DEFINED DPF_DIR)
  set(DPF_DIR $ENV{DPF_DIR})
endif()
add_subdirectory(${DPF_DIR} ${CMAKE_BINARY_DIR}/dpf)
"""


def _make() -> str:
    return """#!/usr/bin/make -f
NAME = WARLOCKFactoryTest
FILES_DSP = ProbeDSP.cpp
include $(DPF_DIR)/Makefile.plugins.mk
TARGETS += vst3
all: $(TARGETS)
"""
