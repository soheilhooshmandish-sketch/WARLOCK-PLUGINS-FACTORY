#include "DistrhoPlugin.hpp"

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
