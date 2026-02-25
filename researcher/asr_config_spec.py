from researcher.asr_config import ASR_MODEL_MAP, DEFAULT_VLM_PRESET, resolve_asr_spec_name, resolve_vlm_preset


class DescribeResolveAsrSpecName:
    def should_map_each_known_model_to_its_whisper_constant(self):
        for model_name, expected in ASR_MODEL_MAP.items():
            assert resolve_asr_spec_name(model_name) == expected

    def should_default_to_whisper_turbo_for_unknown_model(self):
        assert resolve_asr_spec_name("nonexistent") == "WHISPER_TURBO"

    def should_default_to_whisper_turbo_for_empty_string(self):
        assert resolve_asr_spec_name("") == "WHISPER_TURBO"


class DescribeResolveVlmPreset:
    def should_return_default_preset_when_none(self):
        assert resolve_vlm_preset(None) == DEFAULT_VLM_PRESET

    def should_return_specified_model_when_provided(self):
        assert resolve_vlm_preset("smoldocling") == "smoldocling"

    def should_return_specified_model_over_default(self):
        assert resolve_vlm_preset("granite_docling") == "granite_docling"
