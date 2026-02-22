from unittest.mock import MagicMock, patch

import docling.datamodel.asr_model_specs as _real_asr_model_specs


def _make_patch_dict(
    mock_document_converter_cls,
    mock_image_format_option_cls,
    mock_audio_format_option_cls,
    mock_input_format,
    mock_asr_pipeline_cls,
    mock_asr_pipeline_options_cls,
    extra=None,
):
    """Return the sys.modules patch dict common to all tests.

    - The real `docling.datamodel.asr_model_specs` is included so that the
      gateway can do `import docling.datamodel.asr_model_specs as asr_specs`
      and retrieve the real spec constants (e.g. WHISPER_TURBO with repo_id='turbo').
    - `docling.document_converter` and `docling.pipeline.asr_pipeline` are patched
      so that we can assert on how the gateway calls DocumentConverter and
      AsrPipelineOptions without actually loading any ML models.
    - Tests assert on the `repo_id` attribute of the spec that was passed to
      AsrPipelineOptions, which maps cleanly to the user-facing model name strings.
    """
    patches = {
        "docling.document_converter": MagicMock(
            DocumentConverter=mock_document_converter_cls,
            ImageFormatOption=mock_image_format_option_cls,
            AudioFormatOption=mock_audio_format_option_cls,
        ),
        "docling.datamodel.base_models": MagicMock(InputFormat=mock_input_format),
        "docling.datamodel.asr_model_specs": _real_asr_model_specs,
        "docling.pipeline.asr_pipeline": MagicMock(
            AsrPipeline=mock_asr_pipeline_cls,
            AsrPipelineOptions=mock_asr_pipeline_options_cls,
        ),
    }
    if extra:
        patches.update(extra)
    return patches


def _run_get_converter(gateway_kwargs, patch_dict):
    """Remove the cached gateway module, import it fresh inside the patched context."""
    import sys

    saved = sys.modules.pop("researcher.gateways.docling_gateway", None)

    with patch.dict("sys.modules", patch_dict):
        from researcher.gateways.docling_gateway import DoclingGateway

        gateway = DoclingGateway(**gateway_kwargs)
        gateway._get_converter()

    if saved is not None:
        sys.modules["researcher.gateways.docling_gateway"] = saved
    else:
        sys.modules.pop("researcher.gateways.docling_gateway", None)


class DescribeDoclingGateway:
    class DescribeGetConverter:
        def should_configure_asr_pipeline_by_default(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_audio_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_asr_pipeline_cls = MagicMock()
            mock_asr_pipeline_options_cls = MagicMock()

            _run_get_converter(
                {},
                _make_patch_dict(
                    mock_document_converter_cls,
                    mock_image_format_option_cls,
                    mock_audio_format_option_cls,
                    mock_input_format,
                    mock_asr_pipeline_cls,
                    mock_asr_pipeline_options_cls,
                ),
            )

            mock_document_converter_cls.assert_called_once()
            call_kwargs = mock_document_converter_cls.call_args.kwargs
            assert call_kwargs["format_options"] is not None

        def should_use_turbo_asr_model_by_default(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_audio_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_asr_pipeline_cls = MagicMock()
            mock_asr_pipeline_options_cls = MagicMock()

            _run_get_converter(
                {},
                _make_patch_dict(
                    mock_document_converter_cls,
                    mock_image_format_option_cls,
                    mock_audio_format_option_cls,
                    mock_input_format,
                    mock_asr_pipeline_cls,
                    mock_asr_pipeline_options_cls,
                ),
            )

            mock_asr_pipeline_options_cls.assert_called_once()
            asr_options_arg = mock_asr_pipeline_options_cls.call_args.kwargs["asr_options"]
            assert asr_options_arg.repo_id == "turbo"

        def should_map_tiny_model_name_to_whisper_tiny(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_audio_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_asr_pipeline_cls = MagicMock()
            mock_asr_pipeline_options_cls = MagicMock()

            _run_get_converter(
                {"audio_asr_model": "tiny"},
                _make_patch_dict(
                    mock_document_converter_cls,
                    mock_image_format_option_cls,
                    mock_audio_format_option_cls,
                    mock_input_format,
                    mock_asr_pipeline_cls,
                    mock_asr_pipeline_options_cls,
                ),
            )

            mock_asr_pipeline_options_cls.assert_called_once()
            asr_options_arg = mock_asr_pipeline_options_cls.call_args.kwargs["asr_options"]
            assert asr_options_arg.repo_id == "tiny"

        def should_map_large_model_name_to_whisper_large(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_audio_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_asr_pipeline_cls = MagicMock()
            mock_asr_pipeline_options_cls = MagicMock()

            _run_get_converter(
                {"audio_asr_model": "large"},
                _make_patch_dict(
                    mock_document_converter_cls,
                    mock_image_format_option_cls,
                    mock_audio_format_option_cls,
                    mock_input_format,
                    mock_asr_pipeline_cls,
                    mock_asr_pipeline_options_cls,
                ),
            )

            mock_asr_pipeline_options_cls.assert_called_once()
            asr_options_arg = mock_asr_pipeline_options_cls.call_args.kwargs["asr_options"]
            assert asr_options_arg.repo_id == "large"

        def should_configure_vlm_pipeline_for_images(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_audio_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_vlm_pipeline_cls = MagicMock()
            mock_vlm_pipeline_options_cls = MagicMock()
            mock_vlm_convert_options_cls = MagicMock()
            mock_asr_pipeline_cls = MagicMock()
            mock_asr_pipeline_options_cls = MagicMock()

            _run_get_converter(
                {"image_pipeline": "vlm", "image_vlm_model": "smoldocling"},
                _make_patch_dict(
                    mock_document_converter_cls,
                    mock_image_format_option_cls,
                    mock_audio_format_option_cls,
                    mock_input_format,
                    mock_asr_pipeline_cls,
                    mock_asr_pipeline_options_cls,
                    extra={
                        "docling.datamodel.pipeline_options": MagicMock(
                            VlmPipelineOptions=mock_vlm_pipeline_options_cls,
                            VlmConvertOptions=mock_vlm_convert_options_cls,
                        ),
                        "docling.pipeline.vlm_pipeline": MagicMock(VlmPipeline=mock_vlm_pipeline_cls),
                    },
                ),
            )

            mock_vlm_convert_options_cls.from_preset.assert_called_once_with("smoldocling")
            mock_document_converter_cls.assert_called_once()
            call_kwargs = mock_document_converter_cls.call_args.kwargs
            assert call_kwargs["format_options"] is not None

        def should_use_granite_docling_preset_by_default_for_vlm(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_audio_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_vlm_pipeline_cls = MagicMock()
            mock_vlm_pipeline_options_cls = MagicMock()
            mock_vlm_convert_options_cls = MagicMock()
            mock_asr_pipeline_cls = MagicMock()
            mock_asr_pipeline_options_cls = MagicMock()

            _run_get_converter(
                {"image_pipeline": "vlm", "image_vlm_model": None},
                _make_patch_dict(
                    mock_document_converter_cls,
                    mock_image_format_option_cls,
                    mock_audio_format_option_cls,
                    mock_input_format,
                    mock_asr_pipeline_cls,
                    mock_asr_pipeline_options_cls,
                    extra={
                        "docling.datamodel.pipeline_options": MagicMock(
                            VlmPipelineOptions=mock_vlm_pipeline_options_cls,
                            VlmConvertOptions=mock_vlm_convert_options_cls,
                        ),
                        "docling.pipeline.vlm_pipeline": MagicMock(VlmPipeline=mock_vlm_pipeline_cls),
                    },
                ),
            )

            mock_vlm_convert_options_cls.from_preset.assert_called_once_with("granite_docling")

        def should_use_specified_vlm_model_preset(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_audio_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_vlm_pipeline_cls = MagicMock()
            mock_vlm_pipeline_options_cls = MagicMock()
            mock_vlm_convert_options_cls = MagicMock()
            mock_asr_pipeline_cls = MagicMock()
            mock_asr_pipeline_options_cls = MagicMock()

            _run_get_converter(
                {"image_pipeline": "vlm", "image_vlm_model": "phi4"},
                _make_patch_dict(
                    mock_document_converter_cls,
                    mock_image_format_option_cls,
                    mock_audio_format_option_cls,
                    mock_input_format,
                    mock_asr_pipeline_cls,
                    mock_asr_pipeline_options_cls,
                    extra={
                        "docling.datamodel.pipeline_options": MagicMock(
                            VlmPipelineOptions=mock_vlm_pipeline_options_cls,
                            VlmConvertOptions=mock_vlm_convert_options_cls,
                        ),
                        "docling.pipeline.vlm_pipeline": MagicMock(VlmPipeline=mock_vlm_pipeline_cls),
                    },
                ),
            )

            mock_vlm_convert_options_cls.from_preset.assert_called_once_with("phi4")
