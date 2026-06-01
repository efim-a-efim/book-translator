from __future__ import annotations

import html as _html
import uuid

from ebooklib import epub

from book_translator.models.document import BookDocument
from book_translator.assembler.html_gen import build_pair_html, wrap_chapter_xhtml
from book_translator.assembler.splitter import split_chapter_parts


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
                toc_entries.append((
                    epub.Section(chapter.title or ""),
                    [
                        epub.Link(
                            href=item.file_name,
                            title=f"{chapter.title or ''} (Part {k})",
                            uid=item.file_name,
                        )
                        for k, item in enumerate(chapter_items, 1)
                    ],
                ))

        book.spine = ["nav"] + all_chapter_items
        book.toc = tuple(toc_entries)

        return book
