from __future__ import annotations

from book_translator.models.document import BookDocument, Chapter, Paragraph


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
