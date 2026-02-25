from typing import Any

from researcher.models import Fragment


def fragments_from_chunks(chunks: list[Any], document_path: str) -> list[Fragment]:
    """Convert raw chunk objects into domain Fragment models, filtering empties.

    Strips whitespace from chunk text and excludes chunks that are empty
    after stripping. Preserves the original chunk index as fragment_index.

    Args:
        chunks: Raw chunk objects from the docling chunker. Each chunk should
            have a `.text` attribute, or be convertible to string.
        document_path: The path of the source document (used as the fragment key).

    Returns:
        A list of Fragment models with non-empty text.
    """
    fragments: list[Fragment] = []
    for i, chunk in enumerate(chunks):
        text = chunk.text.strip() if hasattr(chunk, "text") else str(chunk).strip()
        if not text:
            continue
        fragments.append(
            Fragment(
                text=text,
                document_path=document_path,
                fragment_index=i,
            )
        )
    return fragments
