from __future__ import annotations

import zipfile
from pathlib import Path

import ebooklib
import pytest
from ebooklib import epub

from book_translator.assembler import assemble
from book_translator.models.document import BookDocument, Chapter, Paragraph


@pytest.fixture
def translated_job_dir(tmp_path):
    job_dir = tmp_path / "run_abc123"
    (job_dir / "src").mkdir(parents=True)
    (job_dir / "dst").mkdir(parents=True)

    doc = BookDocument(
        title="Test Book",
        author="Test Author",
        source_lang="en",
        chapters=[
            Chapter(
                id="ch1",
                title="Chapter One",
                paragraphs=[
                    Paragraph(
                        id="p1",
                        text="Hello world.",
                        raw_html="<p>Hello world.</p>",
                        translation="Привет мир.",
                        kind="paragraph",
                    ),
                    Paragraph(
                        id="p2",
                        text="",
                        raw_html='<img src="fig.png"/>',
                        translation=None,
                        kind="image",
                    ),
                    Paragraph(
                        id="p3",
                        text="Quote.",
                        raw_html="<blockquote>Quote.</blockquote>",
                        translation="Цитата.",
                        kind="paragraph",
                    ),
                ],
            ),
            Chapter(
                id="ch2",
                title="Chapter Two",
                paragraphs=[
                    Paragraph(
                        id="p4",
                        text="Second chapter.",
                        raw_html="<p>Second chapter.</p>",
                        translation="Вторая глава.",
                        kind="paragraph",
                    ),
                ],
            ),
        ],
    )
    (job_dir / "dst" / "test_book.en.json").write_text(doc.to_json(), encoding="utf-8")
    return job_dir


def test_assemble_returns_epub_path(translated_job_dir):
    result = assemble(translated_job_dir, "ru")
    assert isinstance(result, Path)
    assert result.name == "test_book.ru.epub"
    assert result.parent == translated_job_dir / "dst"


def test_assemble_writes_epub_file(translated_job_dir):
    assemble(translated_job_dir, "ru")
    assert (translated_job_dir / "dst" / "test_book.ru.epub").exists()


def test_assemble_epub_is_valid_zip(translated_job_dir):
    assemble(translated_job_dir, "ru")
    assert zipfile.is_zipfile(translated_job_dir / "dst" / "test_book.ru.epub")


def test_assemble_epub_contains_spine_xhtml(translated_job_dir):
    assemble(translated_job_dir, "ru")
    read_book = epub.read_epub(str(translated_job_dir / "dst" / "test_book.ru.epub"))
    docs = list(read_book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    assert len(docs) >= 2
    filenames = [item.file_name for item in docs]
    assert any("chapter-01-pt1.xhtml" in fn for fn in filenames)


def test_assemble_epub_metadata(translated_job_dir):
    assemble(translated_job_dir, "ru")
    read_book = epub.read_epub(str(translated_job_dir / "dst" / "test_book.ru.epub"))
    assert read_book.title == "Test Book"
    # ebooklib does not populate .language on read_epub; check DC metadata directly
    lang_meta = read_book.get_metadata("DC", "language")
    assert lang_meta and lang_meta[0][0] == "ru"


def test_assemble_no_json_raises(tmp_path):
    job_dir = tmp_path / "run_empty"
    (job_dir / "dst").mkdir(parents=True)
    with pytest.raises(ValueError):
        assemble(job_dir, "ru")


def test_assemble_multiple_json_raises(tmp_path):
    job_dir = tmp_path / "run_multi"
    dst = job_dir / "dst"
    dst.mkdir(parents=True)
    (dst / "book1.en.json").write_text("{}", encoding="utf-8")
    (dst / "book2.en.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        assemble(job_dir, "ru")


def test_assemble_no_tmp_file_left(translated_job_dir):
    assemble(translated_job_dir, "ru")
    tmp_files = list((translated_job_dir / "dst").glob("*.tmp"))
    assert len(tmp_files) == 0


# --- Monolingual integration tests (MONO-04, MONO-05, MONO-06) ---


def test_assemble_monolingual_epub(tmp_path):
    """Monolingual EPUB assembly produces translated-only output."""
    from book_translator.assembler import assemble_monolingual

    job_dir = tmp_path / "run_mono"
    (job_dir / "src").mkdir(parents=True)
    (job_dir / "dst").mkdir(parents=True)

    doc = BookDocument(
        title="Test Book",
        author="Test Author",
        source_lang="en",
        chapters=[
            Chapter(
                id="ch1",
                title="Chapter One",
                paragraphs=[
                    Paragraph(
                        id="p1",
                        text="Hello world.",
                        raw_html="<p>Hello world.</p>",
                        translation="Привет мир.",
                        kind="paragraph",
                    ),
                ],
            ),
        ],
    )
    (job_dir / "dst" / "test_book.en.json").write_text(doc.to_json(), encoding="utf-8")

    result = assemble_monolingual(job_dir, "ru")
    assert isinstance(result, Path)
    assert result.name == "test_book.ru.epub"
    assert zipfile.is_zipfile(result)
