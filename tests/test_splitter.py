import pytest

from app.rag.splitter import split_text


def test_short_text_creates_one_chunk():
    text = "深圳大学位于广东省深圳市南山区。"

    chunks = split_text(
        text,
        "szu.txt"
    )

    assert len(chunks) == 1,"短文本应该只生成一个chunk"

def test_empty_text_returns_empty_list():
    chunks = split_text(
        "",
        "empty.txt"
    )

    assert chunks == []

def test_chunk_contains_source_and_id():
    chunks = split_text(
        "深圳大学位于深圳市。",
        "szu.txt"
    )

    first_chunk = chunks[0]

    assert first_chunk["source"] == "szu.txt"
    assert first_chunk["chunk_id"] == 0
    assert first_chunk["content"] == "深圳大学位于深圳市。"

def test_long_text_creates_multiple_valid_chunks():
    text = (
        "深圳大学是一所综合性大学，"
        "学校拥有多个校区和多个本科专业。"
    ) * 30

    chunks = split_text(
        text,
        "long.txt",
        chunk_size=100,
        overlap=20
    )

    assert len(chunks) > 1

    for chunk in chunks:
        assert len(chunk["content"]) <= 100
        assert chunk["source"] == "long.txt"

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    assert chunk_ids == list(
        range(len(chunks))
    )

def test_chunk_size_must_be_greater_than_zero():
    with pytest.raises(ValueError):
        split_text(
            "测试内容",
            "test.txt",
            chunk_size=0
        )

def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        split_text(
            "测试内容",
            "test.txt",
            chunk_size=100,
            overlap=100
        )


def test_page_number_and_chunk_ids_are_preserved():
    chunks = split_text(
        "第一页内容。" * 30,
        "manual.pdf",
        chunk_size=50,
        overlap=10,
        page_number=2,
        chunk_id_start=5
    )

    assert len(chunks) > 1
    assert all(
        chunk["page_number"] == 2
        for chunk in chunks
    )
    assert [
        chunk["chunk_id"]
        for chunk in chunks
    ] == list(
        range(5, 5 + len(chunks))
    )
