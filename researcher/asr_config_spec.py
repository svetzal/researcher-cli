from researcher.asr_config import (
    ASR_MODEL_MAP,
    ASR_MODEL_MAP_MLX,
    resolve_asr_spec_name,
)
from researcher.enums import AudioAsrModel


class DescribeResolveAsrSpecName:
    def should_map_each_known_model_to_its_whisper_constant_on_non_apple(self):
        for model_name, expected in ASR_MODEL_MAP.items():
            assert resolve_asr_spec_name(AudioAsrModel(model_name), apple_silicon=False) == expected

    def should_map_each_known_model_to_mlx_variant_on_apple_silicon(self):
        for model_name, expected in ASR_MODEL_MAP_MLX.items():
            assert resolve_asr_spec_name(AudioAsrModel(model_name), apple_silicon=True) == expected

    def should_return_turbo_mlx_for_turbo_on_apple_silicon(self):
        assert resolve_asr_spec_name(AudioAsrModel.TURBO, apple_silicon=True) == "WHISPER_TURBO_MLX"
