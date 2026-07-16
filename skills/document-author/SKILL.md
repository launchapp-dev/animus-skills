---
name: document-author
description: Authoring policy for producing Office documents (xlsx/pptx/docx) as `document` subjects. Used by the author-document workflow's generate phase — draft a spec, render via the animus-document-engine, and persist with author_document.
---

# Document Author

You produce a real Office document — a spreadsheet (**xlsx**), a slide deck
(**pptx**), or a text document (**docx**) — and store it as a `document` subject.
You never hand-write OOXML: you write a structured **spec**, and the
`animus-document-engine` renders it to real bytes. The spec is the source of
truth (edits re-render from it losslessly).

## Tools you use

- `get_subject` — read the SOURCE subject when the request is "make a deck/sheet/
  doc from `<subject>`" (e.g. a transcript, requirement, or note).
- `render_document` (animus-document-engine) — turn your spec into base64 OOXML
  bytes: `render_document({ format, spec })`.
- `author_document` (animus) — persist the rendered bytes as a `document` subject:
  `author_document({ format, spec, bytes_base64, title, visibility, source_subject_id })`.
- `apply_edits` + `edit_document` — only when revising an existing document.

## Procedure

1. **Understand the ask.** Determine the target `format` (xlsx | pptx | docx),
   the title, and the visibility: `org` for a workspace-shared document,
   `private` for a personal one. If a source subject is named, `get_subject` it
   and ground the content in its real contents — never invent facts.
2. **Draft the spec** for the chosen format (shapes below). Keep it faithful,
   well-structured, and complete — this is the document's content.
3. **Render** with `render_document({ format, spec })`; take the returned
   `bytes_base64`.
4. **Persist** with `author_document({ format, spec, bytes_base64, title,
   visibility, source_subject_id })`. Pass the SAME spec you rendered (it is
   stored as the source of truth) and set `source_subject_id` when you generated
   from another subject (e.g. `transcript:TRANSCRIPT-054`).
5. Report the created `document:DOC-…` id.

Do NOT create the document subject with `create_subject` — `author_document`
both uploads the file to storage and creates the subject; the server sets you as
the owner.

## Spec shapes

```jsonc
// xlsx — sheets of rows; optional bold header row from columns[].header
{ "sheets": [ { "name": "Revenue",
                "columns": [ { "header": "Month" }, { "header": "USD" } ],
                "rows": [ ["Jul", 1200], ["Aug", 1500] ] } ] }

// pptx — one object per slide; bullets OR a body block, plus optional notes
{ "title": "Kickoff",
  "slides": [ { "title": "Agenda", "bullets": ["Scope", "Timeline", "Owners"] },
              { "title": "Next steps", "body": "…", "notes": "speaker note" } ] }

// docx — an ordered stream of blocks
{ "title": "Spec",
  "blocks": [ { "type": "heading", "level": 1, "text": "Overview" },
              { "type": "paragraph", "text": "…" },
              { "type": "bullets", "items": ["a", "b"] },
              { "type": "table", "rows": [["Col A","Col B"],["1","2"]] } ] }
```

## Editing an existing document

`get_document({ id })` to read its stored `spec`, compute the change with
`apply_edits({ format, spec, ops })` (ops: `set` / `append` / `remove` /
`replace`), `render_document` the edited spec, then `edit_document({ id,
bytes_base64, spec })`. Only the owner may edit.

## Rules

- Ground every fact in the source subject or the user's request — never fabricate
  numbers, quotes, or names.
- Choose `visibility` deliberately: default to `org` only when the document is
  meant for the whole workspace.
- Keep the spec and the rendered bytes in sync — always render the exact spec you
  persist.
