from researcher.asr_config import DEFAULT_VLM_PRESET
from researcher.docling_config import AsrFormatConfig, ConverterConfig, VlmFormatConfig, build_converter_config


class DescribeBuildConverterConfig:
    def should_return_no_vlm_config_for_standard_pipeline(self):
        result = build_converter_config("standard", None, "turbo")

        assert result.vlm is None

    def should_return_vlm_config_for_vlm_pipeline(self):
        result = build_converter_config("vlm", None, "turbo")

        assert result.vlm is not None
        assert isinstance(result.vlm, VlmFormatConfig)

    def should_use_default_vlm_preset_when_model_is_none(self):
        result = build_converter_config("vlm", None, "turbo")

        assert result.vlm == VlmFormatConfig(preset=DEFAULT_VLM_PRESET)

    def should_use_custom_vlm_preset_when_specified(self):
        result = build_converter_config("vlm", "smoldocling", "turbo")

        assert result.vlm == VlmFormatConfig(preset="smoldocling")

    def should_return_asr_config_for_turbo_model(self):
        result = build_converter_config("standard", None, "turbo")

        assert result.asr == AsrFormatConfig(spec_name="WHISPER_TURBO")

    def should_return_asr_config_for_tiny_model(self):
        result = build_converter_config("standard", None, "tiny")

        assert result.asr == AsrFormatConfig(spec_name="WHISPER_TINY")

    def should_return_no_asr_config_when_model_is_empty(self):
        result = build_converter_config("standard", None, "")

        assert result.asr is None

    def should_combine_vlm_and_asr_configs(self):
        result = build_converter_config("vlm", "smoldocling", "tiny")

        assert result == ConverterConfig(
            vlm=VlmFormatConfig(preset="smoldocling"),
            asr=AsrFormatConfig(spec_name="WHISPER_TINY"),
        )
