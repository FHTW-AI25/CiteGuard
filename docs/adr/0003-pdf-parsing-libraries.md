# 0003. PDF parsing libraries

| | |
| :--- | :--- |
| **Status** | Proposed |
| **Date** | 2026-11-27 |
| **Deciders** | _the four group members, on acceptance_ |
| **Plan item** | P-03 |

## Context

The ingest worker turns reference PDFs into text chunks. The TDD names "Docling/PyMuPDF" for this in several places. The parser has two separate jobs:

1. **Structured extraction.** Text in reading order with page numbers, and tables as tables. At least 15 benchmark claims have their evidence in a table, and claims about exact numbers depend on table cells being read correctly.
2. **Hidden-text detection.** TDD §10.1 requires removing text a human reader cannot see: zero or tiny font size, text in the background colour, invisible render mode. This needs per-character font size, fill colour and render mode, which is lower-level information than a layout-oriented parser normally returns.

Licences:

| Library | Licence |
| :--- | :--- |
| Docling | MIT |
| PyMuPDF | AGPL-3.0, or a commercial licence from Artifex |
| pdfplumber (built on pdfminer.six) | MIT |
| pypdfium2 (bindings to PDFium) | Apache-2.0 or BSD-3-Clause |

This repository is MIT-licensed. CiteGuard is a network service, and the AGPL's terms extend to users who interact with a program over a network. Using PyMuPDF would mean the deployed service has to be offered under AGPL terms, which conflicts with presenting the project as MIT. The practical risk for a public university project is small, but the mismatch is real and anyone reusing the code would inherit it. This is our reading, not legal advice.

The licence column reflects each project's stated licence as we know it and was not re-verified on the date above.

## Options

### A. Docling and PyMuPDF, as in the TDD

- PyMuPDF gives font size, colour and render flags per text span directly, and is fast.
- Brings the AGPL into an MIT project.

### B. Docling only

- One permissive dependency.
- Docling is built for layout and structure. It is not established that it exposes the per-character properties needed for hidden-text detection. If it does not, a mandatory security control cannot be implemented.

### C. Docling for structure, pdfplumber for hidden-text detection

- Both MIT.
- pdfplumber reports each character with its font size, fill colour and position.
- pdfplumber is pure Python and slow on long documents. With 15 to 20 papers ingested once, this does not matter.
- Two parsers read every PDF, and their outputs have to be reconciled by position.
- It is not confirmed that pdfplumber exposes invisible render mode or zero opacity.

### D. Docling for structure, pypdfium2 for hidden-text detection

- Both permissive. PDFium exposes the text render mode and colours.
- The needed calls are in pypdfium2's low-level interface, which is more awkward to use and to test than pdfplumber's.

## Decision

Proposed:

1. **Do not use PyMuPDF.** The project stays under permissive licences only.
2. **Docling performs structured extraction**: text, reading order, page numbers and tables.
3. **pdfplumber performs hidden-text detection (option C).** For each page it yields the characters that fail a visibility rule: font size below a threshold, fill colour matching the background, or position outside the page's visible area. Those regions are removed from the parsed text before chunking.
4. **The visibility check is one module with its own tests**, driven by the hidden-text PDFs of the injection suite. Its thresholds are configuration.
5. **If the checks below show pdfplumber cannot see a technique in the injection suite**, that technique is covered with pypdfium2 (option D) inside the same module. The decision between C and D is therefore settled by test results, not by preference.
6. **Hidden-text removal has an ablation switch**, since it is part of what the `unsanitized` profile turns off.

## Consequences

- Every PDF is read twice. Ingestion is slower, which is acceptable for a one-off corpus load.
- Docling pulls in large model files and a deep-learning runtime. The ingest worker should get its own dependency group, and probably its own image, so the API and audit worker images stay small. TDD §11.3 currently builds all three from one image.
- Matching hidden regions from one parser to text from another by page and bounding box is a likely source of bugs. It needs tests with known PDFs.
- No part of the project carries a copyleft obligation.

## Before accepting

- [ ] Confirm each library's current licence from its repository.
- [ ] Run Docling on three corpus papers and check that table cells with numbers are extracted correctly and carry page numbers.
- [ ] Build one PDF per hidden-text technique (white text, tiny font, invisible render mode, zero opacity, text outside the visible page) and record which ones pdfplumber detects.
- [ ] Measure ingestion time for one paper with both parsers.

## On acceptance

- Set the status to Accepted and record the test results for each technique here.
- Replace "Docling/PyMuPDF" in TDD §2, §7.2, §10.1 and §12, and in the README's tech stack table.
- Give the ingest worker its own dependency group or image in TDD §11.
- Add a changelog entry.

## Sources

- [Docling](https://github.com/docling-project/docling)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [pypdfium2](https://github.com/pypdfium2-team/pypdfium2)
- [PhantomLint: principled detection of hidden LLM prompts in structured documents](https://arxiv.org/pdf/2508.17884)
