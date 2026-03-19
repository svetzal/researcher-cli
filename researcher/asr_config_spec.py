from unittest.mock import patch

from researcher.asr_config import (
    ASR_MODEL_MAP,
    ASR_MODEL_MAP_MLX,
    DEFAULT_VLM_PRESET,
    resolve_asr_spec_name,
    resolve_vlm_preset,
)


class DescribeResolveAsrSpecName:
    def should_map_each_known_model_to_its_whisper_constant_on_non_apple(self):
        with patch("researcher.asr_config.is_apple_silicon", return_value=False):
            for model_name, expected in ASR_MODEL_MAP.items():
                assert resolve_asr_spec_name(model_name) == expected

    def should_default_to_whisper_turbo_for_unknown_model_on_non_apple(self):
        with patch("researcher.asr_config.is_apple_silicon", return_value=False):
            assert resolve_asr_spec_name("nonexistent") == "WHISPER_TURBO"

    def should_default_to_whisper_turbo_for_empty_string_on_non_apple(self):
        with patch("researcher.asr_config.is_apple_silicon", return_value=False):
            assert resolve_asr_spec_name("") == "WHISPER_TURBO"

    def should_map_each_known_model_to_mlx_variant_on_apple_silicon(self):
        with patch("researcher.asr_config.is_apple_silicon", return_value=True):
            for model_name, expected in ASR_MODEL_MAP_MLX.items():
                assert resolve_asr_spec_name(model_name) == expected

    def should_default_to_whisper_turbo_mlx_for_unknown_model_on_apple_silicon(self):
        with patch("researcher.asr_config.is_apple_silicon", return_value=True):
            assert resolve_asr_spec_name("nonexistent") == "WHISPER_TURBO_MLX"

    def should_return_turbo_mlx_for_turbo_on_apple_silicon(self):
        with patch("researcher.asr_config.is_apple_silicon", return_value=True):
            assert resolve_asr_spec_name("turbo") == "WHISPER_TURBO_MLX"


class DescribeResolveVlmPreset:
    def should_return_default_preset_when_none(self):
        assert resolve_vlm_preset(None) == DEFAULT_VLM_PRESET

    def should_return_specified_model_when_provided(self):
        assert resolve_vlm_preset("smoldocling") == "smoldocling"

    def should_return_specified_model_over_default(self):
        assert resolve_vlm_preset("granite_docling") == "granite_docling"
