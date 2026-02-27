from typing import Any

from researcher.models import Fragment

PLAIN_TEXT_EXTENSIONS = {"txt", "md"}

DEFAULT_CHUNK_MAX_CHARS = 1000
DEFAULT_CHUNK_OVERLAP_CHARS = 200


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


def chunk_plain_text(
    text: str,
    document_path: str,
    max_chars: int = DEFAULT_CHUNK_MAX_CHARS,
    overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
) -> list[Fragment]:
    """Split plain text into overlapping fragments by paragraph boundaries.

    Groups consecutive paragraphs into chunks up to max_chars, then advances
    by (max_chars - overlap_chars) to create overlap between chunks.

    Args:
        text: The full document text.
        document_path: The path of the source document.
        max_chars: Maximum character count per chunk.
        overlap_chars: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of Fragment models with non-empty text.
    """
    stripped = text.strip()
    if not stripped:
        return []

    paragraphs = stripped.split("\n\n")

    fragments: list[Fragment] = []
    current_chunk: list[str] = []
    current_len = 0
    fragment_index = 0
    start_para = 0

    for i, para in enumerate(paragraphs):
        para_text = para.strip()
        if not para_text:
            continue

        addition = len(para_text) + (2 if current_chunk else 0)

        if current_chunk and current_len + addition > max_chars:
            fragments.append(
                Fragment(
                    text="\n\n".join(current_chunk),
                    document_path=document_path,
                    fragment_index=fragment_index,
                )
            )
            fragment_index += 1

            # Rebuild chunk from overlap: walk backwards from current paragraphs
            overlap_chunk: list[str] = []
            overlap_len = 0
            for j in range(i - 1, start_para - 1, -1):
                p = paragraphs[j].strip()
                if not p:
                    continue
                candidate = len(p) + (2 if overlap_chunk else 0)
                if overlap_len + candidate > overlap_chars:
                    break
                overlap_chunk.insert(0, p)
                overlap_len += candidate

            current_chunk = overlap_chunk
            current_len = overlap_len
            start_para = i

        current_chunk.append(para_text)
        current_len += addition

    if current_chunk:
        fragments.append(
            Fragment(
                text="\n\n".join(current_chunk),
                document_path=document_path,
                fragment_index=fragment_index,
            )
        )

    return fragments
