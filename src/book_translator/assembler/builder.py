from __future__ import annotations

import html as _html
import uuid

from ebooklib import epub

from book_translator.assembler.html_gen import (
    _PASS_THROUGH_KINDS,
    build_interactive_html,
    build_pair_html,
    wrap_chapter_xhtml,
)
from book_translator.assembler.splitter import split_chapter_parts
from book_translator.models.document import BookDocument, Chapter


def _make_css_item(content: bytes = b"") -> epub.EpubItem:
    """Create a stub CSS EpubItem for inclusion in EPUB manifests."""
    return epub.EpubItem(
        uid="style",
        file_name="Styles/style.css",
        media_type="text/css",
        content=content,
    )


def _find_title_translation(chapter: Chapter, target_lang: str) -> str:
    """Return h1 HTML for the chapter title, with optional inline translation span.

    D-01: If a heading paragraph whose .text matches chapter.title has a translation,
    embed it in a bt-heading-translation span.
    D-02: If no match, return plain <h1>.
    """
    if not chapter.title:
        return ""
    match = next(
        (
            p
            for p in chapter.paragraphs
            if p.kind == "heading" and p.text == chapter.title and p.translation
        ),
        None,
    )
    if match:
        span = (
            f'<span class="bt-heading-translation"'
            f' xml:lang="{target_lang}" lang="{target_lang}">'
            f"{match.translation}</span>"
        )
        return f"<h1>{_html.escape(chapter.title)}{span}</h1>"
    return f"<h1>{_html.escape(chapter.title)}</h1>"


class EpubBuilder:
    def build(
        self,
        doc: BookDocument,
        target_lang: str,
        book_id: str = "",
    ) -> epub.EpubBook:
        book = epub.EpubBook()
        book.set_identifier(book_id or str(uuid.uuid4()))
        book.set_title(doc.title)
        book.add_author(doc.author)
        book.set_language(target_lang)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        css_item = _make_css_item()
        book.add_item(css_item)

        all_chapter_items: list[epub.EpubHtml] = []
        toc_entries: list = []

        for chapter_num, chapter in enumerate(doc.chapters, 1):
            title_html = f"<h1>{_html.escape(chapter.title)}</h1>" if chapter.title else ""
            pairs = [build_pair_html(p) for p in chapter.paragraphs]
            parts = split_chapter_parts(pairs, title_html, chapter_num)

            chapter_items: list[epub.EpubHtml] = []
            for body_html, filename in parts:
                xhtml_content = wrap_chapter_xhtml([body_html], chapter.title or "", lang=target_lang)
                ch_item = epub.EpubHtml(title=chapter.title or "", file_name=filename, lang=target_lang)
                ch_item.content = xhtml_content.encode("utf-8")
                ch_item.add_item(css_item)
                book.add_item(ch_item)
                chapter_items.append(ch_item)

            all_chapter_items.extend(chapter_items)

            if len(chapter_items) == 1:
                toc_entries.append(
                    epub.Link(
                        href=chapter_items[0].file_name,
                        title=chapter.title or "",
                        uid=chapter_items[0].file_name,
                    )
                )
            else:
                toc_entries.append(
                    (
                        epub.Section(chapter.title or ""),
                        [
                            epub.Link(
                                href=item.file_name,
                                title=f"{chapter.title or ''} (Part {k})",
                                uid=item.file_name,
                            )
                            for k, item in enumerate(chapter_items, 1)
                        ],
                    )
                )

        book.spine = ["nav"] + all_chapter_items
        book.toc = tuple(toc_entries)

        return book

    def build_monolingual(
        self,
        doc: BookDocument,
        target_lang: str,
        book_id: str = "",
    ) -> epub.EpubBook:
        """Build monolingual EPUB with translated-only content.
        
        No paragraph pairing or source text interleaving.
        """
        book = epub.EpubBook()
        book.set_identifier(book_id or str(uuid.uuid4()))
        book.set_title(doc.title)
        book.add_author(doc.author)
        book.set_language(target_lang)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        css_item = _make_css_item()
        book.add_item(css_item)

        all_chapter_items: list[epub.EpubHtml] = []
        toc_entries: list = []

        for chapter_num, chapter in enumerate(doc.chapters, 1):
            # Monolingual: only translated text, no pairing
            title_html = f"<h1>{_html.escape(chapter.title)}</h1>" if chapter.title else ""
            content_parts = []
            for para in chapter.paragraphs:
                if para.kind in ("image", "table"):
                    content_parts.append(para.raw_html)
                elif para.kind == "heading":
                    content_parts.append(f"<h2>{_html.escape(para.text)}</h2>")
                elif para.translation:
                    # Only translation, no original
                    content_parts.append(f"<p>{_html.escape(para.translation)}</p>")

            body_html = "\n".join(content_parts)
            parts = split_chapter_parts([body_html], title_html, chapter_num)

            chapter_items: list[epub.EpubHtml] = []
            for part_html, filename in parts:
                xhtml_content = wrap_chapter_xhtml([part_html], chapter.title or "", lang=target_lang)
                ch_item = epub.EpubHtml(title=chapter.title or "", file_name=filename, lang=target_lang)
                ch_item.content = xhtml_content.encode("utf-8")
                ch_item.add_item(css_item)
                book.add_item(ch_item)
                chapter_items.append(ch_item)

            all_chapter_items.extend(chapter_items)

            if len(chapter_items) == 1:
                toc_entries.append(
                    epub.Link(
                        href=chapter_items[0].file_name,
                        title=chapter.title or "",
                        uid=chapter_items[0].file_name,
                    )
                )
            else:
                toc_entries.append(
                    (
                        epub.Section(chapter.title or ""),
                        [
                            epub.Link(
                                href=item.file_name,
                                title=f"{chapter.title or ''} (Part {k})",
                                uid=item.file_name,
                            )
                            for k, item in enumerate(chapter_items, 1)
                        ],
                    )
                )

        book.spine = ["nav"] + all_chapter_items
        book.toc = tuple(toc_entries)

        return book

    def build_interactive(
        self,
        doc: BookDocument,
        target_lang: str,
        book_id: str = "",
    ) -> epub.EpubBook:
        """Build interactive EPUB with CSS-only details/summary paragraph toggles."""
        book = epub.EpubBook()
        book.set_identifier(book_id or str(uuid.uuid4()))
        book.set_title(doc.title)
        book.add_author(doc.author)
        book.set_language(target_lang)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        css_item = _make_css_item()
        book.add_item(css_item)

        all_chapter_items: list[epub.EpubHtml] = []
        toc_entries: list = []

        for chapter_num, chapter in enumerate(doc.chapters, 1):
            title_html = _find_title_translation(chapter, target_lang)
            html_parts = []
            first_details_emitted = False

            for para in chapter.paragraphs:
                is_first = False
                if para.kind not in _PASS_THROUGH_KINDS and para.kind != "heading":
                    if not first_details_emitted:
                        is_first = True
                        first_details_emitted = True
                html_parts.append(build_interactive_html(para, target_lang, is_first=is_first))

            parts = split_chapter_parts(html_parts, title_html, chapter_num)

            chapter_items: list[epub.EpubHtml] = []
            for body_html, filename in parts:
                xhtml_content = wrap_chapter_xhtml([body_html], chapter.title or "", lang=target_lang)
                ch_item = epub.EpubHtml(title=chapter.title or "", file_name=filename, lang=target_lang)
                ch_item.content = xhtml_content.encode("utf-8")
                ch_item.add_item(css_item)
                book.add_item(ch_item)
                chapter_items.append(ch_item)

            all_chapter_items.extend(chapter_items)

            if len(chapter_items) == 1:
                toc_entries.append(
                    epub.Link(
                        href=chapter_items[0].file_name,
                        title=chapter.title or "",
                        uid=chapter_items[0].file_name,
                    )
                )
            else:
                toc_entries.append(
                    (
                        epub.Section(chapter.title or ""),
                        [
                            epub.Link(
                                href=item.file_name,
                                title=f"{chapter.title or ''} (Part {k})",
                                uid=item.file_name,
                            )
                            for k, item in enumerate(chapter_items, 1)
                        ],
                    )
                )

        book.spine = ["nav"] + all_chapter_items
        book.toc = tuple(toc_entries)

        return book
