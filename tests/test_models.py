from __future__ import annotations

import dataclasses

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.models.job import JobMeta


def test_paragraph_defaults():
    p = Paragraph(id="p1", text="hello", raw_html="<p>hello</p>")
    assert p.translation is None
    assert p.kind == "paragraph"


def test_paragraph_translation_slot():
    p = Paragraph(id="p1", text="hello", raw_html="<p>hello</p>")
    p = p.model_copy(update={"translation": "hola"})
    assert p.translation == "hola"


def test_book_document_round_trip():
    doc = BookDocument(
        title="War and Peace",
        source_lang="ru",
        chapters=[
            Chapter(
                id="ch01",
                title="Chapter 1",
                paragraphs=[
                    Paragraph(
                        id="ch01:p001",
                        text="Ну что, князь...",
                        raw_html='<p id="p1">Ну что, князь...</p>',
                    )
                ],
            )
        ],
    )
    json_str = doc.to_json()
    doc2 = BookDocument.from_json(json_str)
    assert doc2.title == "War and Peace"
    assert doc2.source_lang == "ru"
    assert doc2.chapters[0].id == "ch01"
    assert doc2.chapters[0].paragraphs[0].text == "Ну что, князь..."
    assert doc2.chapters[0].paragraphs[0].raw_html == '<p id="p1">Ну что, князь...</p>'
    assert doc2.chapters[0].paragraphs[0].translation is None


def test_book_document_empty_translation_vs_none():
    p_none = Paragraph(id="p1", text="x", raw_html="x", translation=None)
    p_empty = Paragraph(id="p2", text="x", raw_html="x", translation="")
    assert p_none.translation is None
    assert p_empty.translation == ""


def test_chapter_empty_paragraphs():
    ch = Chapter(id="ch1")
    assert ch.paragraphs == []


def test_paragraph_kind_variants():
    for kind in ("heading", "caption", "footnote", "image", "table"):
        p = Paragraph(id="p1", text="x", raw_html="x", kind=kind)  # type: ignore[arg-type]
        assert p.kind == kind


def test_jobmeta_default_params():
    m = JobMeta(model="openai/gpt-4o")
    assert m.params == {}
    fields = {f.name for f in dataclasses.fields(m)}
    assert fields == {"model", "params"}
