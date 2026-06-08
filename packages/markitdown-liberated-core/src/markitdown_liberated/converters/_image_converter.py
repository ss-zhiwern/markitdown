from typing import BinaryIO, Any
from ._exiftool import exiftool_metadata
from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo

ACCEPTED_MIME_TYPE_PREFIXES = [
    "image/jpeg",
    "image/png",
]

ACCEPTED_FILE_EXTENSIONS = [".jpg", ".jpeg", ".png"]


class ImageConverter(DocumentConverter):
    """
    Converts images to markdown via extraction of metadata (if `exiftool` is installed).
    """

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        for prefix in ACCEPTED_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                return True

        return False

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        md_content = ""

        # Add metadata
        metadata = exiftool_metadata(
            file_stream, exiftool_path=kwargs.get("exiftool_path")
        )

        if metadata:
            for f in [
                "ImageSize",
                "Title",
                "Caption",
                "Description",
                "Keywords",
                "Artist",
                "Author",
                "DateTimeOriginal",
                "CreateDate",
                "GPSPosition",
            ]:
                if f in metadata:
                    md_content += f"{f}: {metadata[f]}\n"

        return DocumentConverterResult(
            markdown=md_content,
        )
