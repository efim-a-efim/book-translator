# Book Translator Requirements

AI-powered fiction book translator. Produces bilingual EPUB (paragraph pairs: original + translation). CLI tool, Python, OSS.

## v1 Functional Requirements

### Inputs
1. Accept EPUB files as input.
2. Accept TXT files (split into paragraphs).
3. Accept Markdown files (split into paragraphs).

### Translation Engine
4. Simple mode: context-windowed chunking (surrounding paragraphs included in each prompt).
5. Support any OpenAI-compatible API endpoint with user-specified model + API key (OpenRouter, etc.).
6. Retry with exponential backoff on rate limits and transient errors (via tenacity).

### EPUB Output
7. Generate bilingual EPUB with paragraph pairs (original + translation) for each original paragraph.
8. Translate and pair special elements: chapter titles, captions, footnotes.
9. Split oversized chapters to stay under e-reader file limits (~300KB).

### Job Management
10. No database — use file/directory-based persistence only.
11. Use self-describing directory structure: `src/<book_name>.<lang_from>.<ext>` and `dst/<book_name>.<lang_to>.epub`; language pair derivable from file names.
12. Minimize special metadata files — store only what cannot be derived from file names (e.g., model name, API parameters).
13. Each run gets a unique persistent run ID (directory name).
14. Job listing = listing run directories.

## v1 Non-Functional Requirements

### CLI
15. CLI is fully standalone — no dependency on any running web server or application API; only external dependency is the AI provider API.
16. `translate <file> --from <lang_from> --to <lang_to> --model <model> --api-key <key> [--base-url <url>]` command.
17. `--verbose` flag for detailed logging.

### Performance / Reliability
18. Retry mechanism must not block the entire run on transient failures (graceful degradation).
19. Ensure e-reader files stay under limits to prevent corruption on small devices.

### Tech Stack
20. Python implementation.
21. OSS (open source).

## v2 Deferred Features

- FB2 / FB2.ZIP input (handle Windows-1251 encoding)
- Smart mode: pre-analyze book → extract character glossary + style notes → inject into every translation prompt
- Multi-language per run (multiple --to targets)
- EPUB metadata preservation (language tags, title, author)
- RTL language support (Arabic, Hebrew — CSS dir attribute)
- Resume from checkpoint (restart interrupted job from last completed chunk)
- Progress tracking (chunks done / total, ETA)
- `status <run-id>` command
- `download <run-id>` command
- `list` command
- Config file support (~/.config/book-translator/)
- Web interface

## Out of Scope (forever)

- PDF / OCR support (Calibre handles upstream).
- Cloud hosting / SaaS.
- Real-time collaborative editing.
