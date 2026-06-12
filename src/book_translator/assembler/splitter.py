from __future__ import annotations


def split_chapter_parts(
    pairs: list[str],
    title_html: str,
    chapter_num: int,
    size_limit: int = 300_000,
) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    current_pairs: list[str] = []
    current_size = len(title_html.encode("utf-8"))
    part_num = 1

    for pair in pairs:
        pair_bytes = len(pair.encode("utf-8"))
        if current_pairs and (current_size + pair_bytes) > size_limit:
            # flush current part
            if part_num == 1:
                body_html = title_html + "".join(current_pairs)
            else:
                body_html = "".join(current_pairs)
            parts.append((body_html, f"chapter-{chapter_num:02d}-pt{part_num}.xhtml"))
            part_num += 1
            current_pairs = [pair]
            current_size = pair_bytes
        else:
            current_pairs.append(pair)
            current_size += pair_bytes

    # flush remaining
    if current_pairs:
        if part_num == 1:
            body_html = title_html + "".join(current_pairs)
        else:
            body_html = "".join(current_pairs)
        parts.append((body_html, f"chapter-{chapter_num:02d}-pt{part_num}.xhtml"))

    # guard: title-only chapter (empty pairs) must still emit one part
    if not parts and title_html:
        parts.append((title_html, f"chapter-{chapter_num:02d}-pt1.xhtml"))

    return parts
