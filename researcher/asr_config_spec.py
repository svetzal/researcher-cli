import itertools

import pytest

from researcher.asr_config import ASR_MODELS, resolve_asr_spec_name
from researcher.enums import AudioAsrModel


class DescribeResolveAsrSpecName:
    def should_map_each_known_model_to_its_whisper_constant_on_non_apple(self):
        for model_name, spec in ASR_MODELS.items():
            assert resolve_asr_spec_name(model_name, apple_silicon=False) == spec.spec_name

    def should_map_each_known_model_to_mlx_variant_on_apple_silicon(self):
        for model_name, spec in ASR_MODELS.items():
            assert resolve_asr_spec_name(model_name, apple_silicon=True) == spec.mlx_spec_name

    def should_return_turbo_mlx_for_turbo_on_apple_silicon(self):
        assert resolve_asr_spec_name(AudioAsrModel.TURBO, apple_silicon=True) == "WHISPER_TURBO_MLX"


class DescribeAsrSpecNameValidity:
    @pytest.mark.parametrize(
        "model,apple_silicon",
        list(itertools.product(list(AudioAsrModel), [True, False])),
    )
    def should_resolve_to_existing_docling_asr_spec(self, model, apple_silicon):
        pytest.importorskip("docling")
        import docling.datamodel.asr_model_specs as asr_specs

        spec_name = resolve_asr_spec_name(model, apple_silicon=apple_silicon)
        assert hasattr(asr_specs, spec_name), f"docling.datamodel.asr_model_specs has no attribute {spec_name!r}"


class DescribeAsrModelCoverage:
    """Structural guard: every AudioAsrModel member must have a complete ASR_MODELS entry.

    Adding a new ASR model requires exactly one new entry in ASR_MODELS — this test
    fails loudly if that entry is missing or incomplete, instead of failing obscurely
    at runtime in whichever consumer (docling resolution, cache packing, CLI help)
    happens to hit the gap first.
    """

    def should_have_an_entry_for_every_audio_asr_model(self):
        assert set(ASR_MODELS) == set(AudioAsrModel)

    @pytest.mark.parametrize("model", list(AudioAsrModel))
    def should_have_all_fields_populated_for_each_model(self, model):
        spec = ASR_MODELS[model]

        assert spec.spec_name
        assert spec.mlx_spec_name
        assert spec.mlx_repo_id
        assert spec.whisper_cache_file
