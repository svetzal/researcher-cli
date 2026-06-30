import pytest

from researcher.enums import AudioAsrModel, EmbeddingProvider, ImagePipeline, SearchMode


class DescribeEmbeddingProvider:
    def should_have_chromadb_ollama_openai_members(self):
        assert set(EmbeddingProvider) == {
            EmbeddingProvider.CHROMADB,
            EmbeddingProvider.OLLAMA,
            EmbeddingProvider.OPENAI,
        }

    def should_compare_equal_to_string_values(self):
        assert EmbeddingProvider.CHROMADB == "chromadb"
        assert EmbeddingProvider.OLLAMA == "ollama"
        assert EmbeddingProvider.OPENAI == "openai"

    def should_construct_from_valid_string(self):
        assert EmbeddingProvider("ollama") is EmbeddingProvider.OLLAMA

    def should_raise_for_unknown_value(self):
        with pytest.raises(ValueError):
            EmbeddingProvider("bogus")


class DescribeImagePipeline:
    def should_have_standard_and_vlm_members(self):
        assert set(ImagePipeline) == {ImagePipeline.STANDARD, ImagePipeline.VLM}

    def should_compare_equal_to_string_values(self):
        assert ImagePipeline.STANDARD == "standard"
        assert ImagePipeline.VLM == "vlm"

    def should_raise_for_unknown_value(self):
        with pytest.raises(ValueError):
            ImagePipeline("ocr")


class DescribeAudioAsrModel:
    def should_have_six_members(self):
        assert set(AudioAsrModel) == {
            AudioAsrModel.TINY,
            AudioAsrModel.BASE,
            AudioAsrModel.SMALL,
            AudioAsrModel.MEDIUM,
            AudioAsrModel.LARGE,
            AudioAsrModel.TURBO,
        }

    def should_construct_from_valid_string(self):
        assert AudioAsrModel("turbo") is AudioAsrModel.TURBO

    def should_raise_for_unknown_value(self):
        with pytest.raises(ValueError):
            AudioAsrModel("bogus")


class DescribeSearchMode:
    def should_have_fragments_and_documents_members(self):
        assert set(SearchMode) == {SearchMode.FRAGMENTS, SearchMode.DOCUMENTS}

    def should_compare_equal_to_string_values(self):
        assert SearchMode.FRAGMENTS == "fragments"
        assert SearchMode.DOCUMENTS == "documents"

    def should_raise_for_unknown_value(self):
        with pytest.raises(ValueError):
            SearchMode("bogus")
