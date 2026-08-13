import re


SEPARATOR_GROUPS = (
    ("\n\n",),
    ("\n",),
    ("。", "！", "？", "!", "?"),
    ("；", ";"),
    ("，", ","),
)


def normalize_text(text):
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_split_end(
        text,
        start,
        limit,
        chunk_size
):
    min_chunk_size = max(
        20,
        chunk_size // 2
    )
    search_start = min(
        start + min_chunk_size,
        limit
    )

    for separators in SEPARATOR_GROUPS:
        best_end = -1

        for separator in separators:
            position = text.rfind(
                separator,
                search_start,
                limit
            )

            if position != -1:
                best_end = max(
                    best_end,
                    position + len(separator)
                )

        if best_end != -1:
            return best_end

    return limit


def find_overlap_start(
        text,
        chunk_start,
        chunk_end,
        overlap
):
    if overlap == 0:
        return chunk_end

    target = max(
        chunk_start + 1,
        chunk_end - overlap
    )
    search_start = max(
        chunk_start + 1,
        target - overlap
    )
    best_start = -1

    for separators in SEPARATOR_GROUPS:
        for separator in separators:
            position = text.rfind(
                separator,
                search_start,
                target
            )

            if position != -1:
                best_start = max(
                    best_start,
                    position + len(separator)
                )

    if best_start <= chunk_start:
        return target

    return best_start


def split_text(
        text,
        source,
        chunk_size=400,
        overlap=60,
        page_number=None,
        chunk_id_start=0
):
    if chunk_size <= 0:
        raise ValueError(
            "chunk_size必须大于0"
        )

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap必须大于等于0且小于chunk_size"
        )

    text = normalize_text(
        text
    )

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        limit = min(
            start + chunk_size,
            len(text)
        )

        if limit < len(text):
            end = find_split_end(
                text,
                start,
                limit,
                chunk_size
            )
        else:
            end = limit

        content = text[start:end].strip()

        if content:
            chunk = {
                "content": content,
                "source": source,
                "chunk_id": chunk_id_start + len(chunks)
            }

            if page_number is not None:
                chunk["page_number"] = page_number

            chunks.append(
                chunk
            )

        if end >= len(text):
            break

        next_start = find_overlap_start(
            text,
            start,
            end,
            overlap
        )

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks
