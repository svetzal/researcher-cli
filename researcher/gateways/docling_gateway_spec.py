from unittest.mock import MagicMock, patch


class DescribeDoclingGateway:
    class DescribeGetConverter:
        def should_use_standard_pipeline_by_default(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_input_format = MagicMock()

            with patch.dict(
                "sys.modules",
                {
                    "docling": MagicMock(),
                    "docling.document_converter": MagicMock(
                        DocumentConverter=mock_document_converter_cls,
                        ImageFormatOption=mock_image_format_option_cls,
                    ),
                    "docling.datamodel": MagicMock(),
                    "docling.datamodel.base_models": MagicMock(InputFormat=mock_input_format),
                },
            ):
                from researcher.gateways.docling_gateway import DoclingGateway

                gateway = DoclingGateway()
                gateway._get_converter()

            mock_document_converter_cls.assert_called_once_with(format_options=None)

        def should_configure_vlm_pipeline_for_images(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_vlm_pipeline_cls = MagicMock()
            mock_vlm_pipeline_options_cls = MagicMock()
            mock_vlm_convert_options_cls = MagicMock()

            with patch.dict(
                "sys.modules",
                {
                    "docling": MagicMock(),
                    "docling.document_converter": MagicMock(
                        DocumentConverter=mock_document_converter_cls,
                        ImageFormatOption=mock_image_format_option_cls,
                    ),
                    "docling.datamodel": MagicMock(),
                    "docling.datamodel.base_models": MagicMock(InputFormat=mock_input_format),
                    "docling.datamodel.pipeline_options": MagicMock(
                        VlmPipelineOptions=mock_vlm_pipeline_options_cls,
                        VlmConvertOptions=mock_vlm_convert_options_cls,
                    ),
                    "docling.pipeline": MagicMock(),
                    "docling.pipeline.vlm_pipeline": MagicMock(VlmPipeline=mock_vlm_pipeline_cls),
                },
            ):
                from researcher.gateways.docling_gateway import DoclingGateway

                gateway = DoclingGateway(image_pipeline="vlm", image_vlm_model="smoldocling")
                gateway._get_converter()

            mock_vlm_convert_options_cls.from_preset.assert_called_once_with("smoldocling")
            mock_document_converter_cls.assert_called_once()
            call_kwargs = mock_document_converter_cls.call_args.kwargs
            assert call_kwargs["format_options"] is not None

        def should_use_granite_docling_preset_by_default_for_vlm(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_vlm_pipeline_cls = MagicMock()
            mock_vlm_pipeline_options_cls = MagicMock()
            mock_vlm_convert_options_cls = MagicMock()

            with patch.dict(
                "sys.modules",
                {
                    "docling": MagicMock(),
                    "docling.document_converter": MagicMock(
                        DocumentConverter=mock_document_converter_cls,
                        ImageFormatOption=mock_image_format_option_cls,
                    ),
                    "docling.datamodel": MagicMock(),
                    "docling.datamodel.base_models": MagicMock(InputFormat=mock_input_format),
                    "docling.datamodel.pipeline_options": MagicMock(
                        VlmPipelineOptions=mock_vlm_pipeline_options_cls,
                        VlmConvertOptions=mock_vlm_convert_options_cls,
                    ),
                    "docling.pipeline": MagicMock(),
                    "docling.pipeline.vlm_pipeline": MagicMock(VlmPipeline=mock_vlm_pipeline_cls),
                },
            ):
                from researcher.gateways.docling_gateway import DoclingGateway

                gateway = DoclingGateway(image_pipeline="vlm", image_vlm_model=None)
                gateway._get_converter()

            mock_vlm_convert_options_cls.from_preset.assert_called_once_with("granite_docling")

        def should_use_specified_vlm_model_preset(self):
            mock_converter_instance = MagicMock()
            mock_document_converter_cls = MagicMock(return_value=mock_converter_instance)
            mock_image_format_option_cls = MagicMock()
            mock_input_format = MagicMock()
            mock_vlm_pipeline_cls = MagicMock()
            mock_vlm_pipeline_options_cls = MagicMock()
            mock_vlm_convert_options_cls = MagicMock()

            with patch.dict(
                "sys.modules",
                {
                    "docling": MagicMock(),
                    "docling.document_converter": MagicMock(
                        DocumentConverter=mock_document_converter_cls,
                        ImageFormatOption=mock_image_format_option_cls,
                    ),
                    "docling.datamodel": MagicMock(),
                    "docling.datamodel.base_models": MagicMock(InputFormat=mock_input_format),
                    "docling.datamodel.pipeline_options": MagicMock(
                        VlmPipelineOptions=mock_vlm_pipeline_options_cls,
                        VlmConvertOptions=mock_vlm_convert_options_cls,
                    ),
                    "docling.pipeline": MagicMock(),
                    "docling.pipeline.vlm_pipeline": MagicMock(VlmPipeline=mock_vlm_pipeline_cls),
                },
            ):
                from researcher.gateways.docling_gateway import DoclingGateway

                gateway = DoclingGateway(image_pipeline="vlm", image_vlm_model="phi4")
                gateway._get_converter()

            mock_vlm_convert_options_cls.from_preset.assert_called_once_with("phi4")
