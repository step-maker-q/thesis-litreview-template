#!/usr/bin/env python3
"""
Convert a Markdown file into a valid Microsoft Word (.docx) document.

Usage:
    python scripts/md_to_docx.py input.md output.docx
    python scripts/md_to_docx.py input.md            # writes input.docx next to input

Why this exists: a .docx is an OOXML (ZIP) binary format. Writing Markdown or
plain text to a file named *.docx produces a corrupt document that Word refuses
to open. This script always emits a real .docx.

This implementation uses only the Python standard library (no python-docx), so it
runs anywhere Python 3.10+ is available. It produces a valid OOXML package that
opens in Microsoft Word, LibreOffice, and Google Docs.

Supported Markdown (subset):
    # / ## / ### headings (up to 6)
    paragraphs, blank lines
    - / * / + bullet lists (nested one level)
    1. numbered lists
    **bold**, *italic*, `code` inline
    fenced code blocks (``` ... ```)
    tables (GFM pipe tables)
    > blockquotes
    --- horizontal rules
"""

import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


# ---------- inline formatting ----------

INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")


def parse_inline(text):
    """Return list of (text, bold, italic, code) tuples."""
    parts = INLINE_RE.split(text)
    out = []
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            out.append((part[2:-2], True, False, False))
        elif part.startswith("*") and part.endswith("*"):
            out.append((part[1:-1], False, True, False))
        elif part.startswith("`") and part.endswith("`"):
            out.append((part[1:-1], False, False, True))
        else:
            out.append((part, False, False, False))
    return out


def run_xml(text, bold=False, italic=False, code=False, size=None, color=None):
    rpr = ""
    if bold or italic or code or size or color:
        rpr_parts = ["<w:rPr>"]
        if bold:
            rpr_parts.append("<w:b/>")
        if italic:
            rpr_parts.append("<w:i/>")
        if code:
            rpr_parts.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>')
        if size:
            rpr_parts.append(f'<w:sz w:val="{size}"/>')
        if color:
            rpr_parts.append(f'<w:color w:val="{color}"/>')
        rpr_parts.append("</w:rPr>")
        rpr = "".join(rpr_parts)
    return f"<w:r>{rpr}<w:t xml:space=\"preserve\">{xml_escape(text)}</w:t></w:r>"


def inline_runs(text):
    return "".join(
        run_xml(t, bold=b, italic=i, code=c) for (t, b, i, c) in parse_inline(text)
    )


# ---------- block helpers ----------

def para_xml(runs_inner, style=None, indent=None, spacing_after=None, shading=None,
             border_bottom=False, align=None):
    ppr = ["<w:pPr>"]
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    if indent is not None:
        ppr.append(f'<w:ind w:left="{indent}"/>')
    if spacing_after is not None:
        ppr.append(f'<w:spacing w:after="{spacing_after}"/>')
    if shading:
        ppr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shading}"/>')
    if border_bottom:
        ppr.append(
            '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="999999"/></w:pBdr>'
        )
    ppr.append("</w:pPr>")
    return "<w:p>" + "".join(ppr) + runs_inner + "</w:p>"


def heading_xml(text, level):
    sizes = {1: 32, 2: 26, 3: 22, 4: 20, 5: 18, 6: 16}
    size = sizes.get(level, 16)
    return para_xml(
        run_xml(text, bold=True, size=size, color="1F3864"),
        spacing_after=60 if level <= 2 else 40,
    )


def code_para_xml(text):
    inner = run_xml(text if text.strip() != "" else " ", code=True, size=18)
    return para_xml(inner, shading="F2F2F2", spacing_after=0)


def bullet_xml(text, indent=360):
    inner = run_xml("\u2022  ", bold=True) + inline_runs(text)
    return para_xml(inner, indent=indent, spacing_after=20)


def numbered_xml(num, text, indent=360):
    inner = run_xml(f"{num}.  ", bold=True) + inline_runs(text)
    return para_xml(inner, indent=indent, spacing_after=20)


def blockquote_xml(text):
    inner = inline_runs(text)
    return para_xml(inner, indent=360, spacing_after=40)


def hr_xml():
    return para_xml("", border_bottom=True, spacing_after=40)


def table_xml(rows):
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    # normalize
    norm = [r + [""] * (ncols - len(r)) for r in rows]
    grid_cols = "".join("<w:gridCol w:w=\"1200\"/>" for _ in range(ncols))
    out = ['<w:tbl>',
           '<w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/>'
           '<w:tblBorders>'
           '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
           '</w:tblBorders></w:tblPr>',
           '<w:tblGrid>' + grid_cols + '</w:tblGrid>']
    for ri, r in enumerate(norm):
        out.append("<w:tr>")
        for ci, val in enumerate(r):
            cell_runs = inline_runs(val)
            if ri == 0:
                cell_runs = run_xml(val, bold=True) if False else cell_runs
                # bold all runs in header by re-rendering
                cell_runs = "".join(
                    run_xml(t, bold=True, italic=i, code=c) for (t, b, i, c) in parse_inline(val)
                )
            out.append(
                f'<w:tc><w:tcPr><w:tcW w:w="1200" w:type="dxa"/></w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:after="20"/></w:pPr>{cell_runs}</w:p></w:tc>'
            )
        out.append("</w:tr>")
    out.append("</w:tbl>")
    # spacing paragraph after table
    out.append(para_xml("", spacing_after=60))
    return "".join(out)


# ---------- converter ----------

def convert(md_text):
    lines = md_text.splitlines()
    body = []
    i = 0
    n = len(lines)
    in_code = False
    code_buf = []

    def flush_code():
        nonlocal code_buf
        if not code_buf:
            return
        for cl in code_buf:
            body.append(code_para_xml(cl))
        code_buf = []

    while i < n:
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()

        if stripped == "":
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            body.append(heading_xml(m.group(2).strip(), len(m.group(1))))
            i += 1
            continue

        if stripped.startswith(">"):
            body.append(blockquote_xml(stripped.lstrip(">").strip()))
            i += 1
            continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            body.append(hr_xml())
            i += 1
            continue

        # table
        if "|" in stripped and i + 1 < n and re.match(r"^\s*\|?[\s\-:|]+\|?\s*$", lines[i + 1].strip()):
            table_lines = []
            j = i
            while j < n and "|" in lines[j].strip():
                table_lines.append(lines[j].strip())
                j += 1
            rows = []
            for tl in table_lines:
                if re.match(r"^\s*\|?[\s\-:|]+\|?\s*$", tl):
                    continue
                cells = [c.strip() for c in tl.strip().strip("|").split("|")]
                rows.append(cells)
            body.append(table_xml(rows))
            i = j
            continue

        # bullet
        m = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        if m:
            indent = 360 if len(m.group(1)) < 4 else 720
            body.append(bullet_xml(m.group(2), indent=indent))
            i += 1
            continue

        # numbered
        m = re.match(r"^(\s*)\d+\.\s+(.*)$", line)
        if m:
            # extract number
            num = re.match(r"^\s*(\d+)\.", line).group(1)
            indent = 360 if len(m.group(1)) < 4 else 720
            body.append(numbered_xml(num, m.group(2), indent=indent))
            i += 1
            continue

        # paragraph: collect consecutive lines
        para_lines = [stripped]
        j = i + 1
        while j < n:
            s = lines[j].strip()
            if s == "" or s.startswith("#") or s.startswith("```") or s.startswith(">") or s.startswith("|") \
               or re.match(r"^[-*+]\s", lines[j]) or re.match(r"^\d+\.\s", lines[j]) \
               or re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
                break
            if "|" in s and j + 1 < n and re.match(r"^\s*\|?[\s\-:|]+\|?\s*$", lines[j + 1].strip()):
                break
            para_lines.append(s)
            j += 1
        body.append(para_xml(inline_runs(" ".join(para_lines)), spacing_after=80))
        i = j
        continue

    return "".join(body)


# ---------- document assembly ----------

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""

CORE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:dcmitype="http://purl.org/dc/dcmitype/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Converted document</dc:title>
  <dc:creator>md_to_docx</dc:creator>
</cp:coreProperties>"""

APP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
  xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>md_to_docx</Application>
</Properties>"""


def write_docx(md_text, out_path):
    body = convert(md_text)
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<w:body>{body}'
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        '</w:body></w:document>'
    )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("docProps/core.xml", CORE)
        z.writestr("docProps/app.xml", APP)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", document_xml)
    print(f"wrote {out_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/md_to_docx.py input.md [output.docx]")
        raise SystemExit(2)
    inp = Path(sys.argv[1])
    if not inp.exists():
        print(f"ERROR: {inp} not found")
        raise SystemExit(2)
    if len(sys.argv) >= 3 and sys.argv[2].strip():
        outp = Path(sys.argv[2])
    else:
        outp = inp.with_suffix(".docx")
    write_docx(inp.read_text(encoding="utf-8"), outp)


if __name__ == "__main__":
    main()
