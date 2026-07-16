---
name: document-author
description: Authoring policy for producing Office documents (xlsx/pptx/docx) as `document` subjects. Used by the author-document workflow's generate phase — draft a spec, render+store via the animus-document-engine store_document tool, then record it with create_subject.
---

# Document Author

You produce a real Office document — a spreadsheet (**xlsx**), a slide deck
(**pptx**), or a text document (**docx**) — and record it as a `document` subject.
You never hand-write OOXML: you write a structured **spec**, and the
`animus-document-engine` renders + stores it. The spec is the source of truth
(edits re-render from it losslessly).

## Tools you use

- `get_subject` — read the SOURCE subject when the request is "make a deck/sheet/
  doc from `<subject>`" (e.g. a transcript, requirement, or note).
- `store_document` (animus-document-engine) — render your spec AND persist the
  bytes to S3 in one call:
  `store_document({ format, spec, title, owner, visibility })` →
  `{ s3_key, size_bytes, url, content_type, filename }`.
- `create_subject` (animus) — record the stored document as a `document` subject
  with the returned `s3_key` + your metadata.

## Procedure

1. **Understand the ask.** Parse the request. Tasks enqueued by the portal carry a
   machine block `Machine request: {...}` with `intent`, `format`,
   `source_subject_id`, `visibility`, `prompt`, and `requested_by` — use those.
   Determine `format` (xlsx|pptx|docx), a `title`, `visibility` (`org` for a
   workspace-shared doc, `private` for a personal one), and the owner
   (`requested_by`). If a source subject is named, `get_subject` it and ground the
   content in its real contents — never invent facts.
2. **Draft the spec** for the chosen format (shapes below) — faithful, complete.
3. **Render + store** with `store_document({ format, spec, title, owner:
   <requested_by>, visibility })`. Keep the returned `s3_key`, `size_bytes`,
   `content_type`, `filename`, `url`.
4. **Record** the document with `create_subject`:
   ```
   create_subject(kind="document", title=<title>, custom={
     format, spec,                         // the SAME spec you rendered (source of truth)
     s3_key, size_bytes, url,
     mime_type: <content_type>, filename,
     owner_id: <requested_by>, visibility,
     source_subject_id: <if generated from a subject>
   })
   ```
   Set `owner_id` to the requester (`requested_by`) and `visibility` to the chosen
   scope — this is what controls who can see the document.
5. Report the created `document:DOC-…` id.

Do NOT try to upload bytes yourself and do NOT call `author_document` — that tool
is portal-external and not available to you. `store_document` does the S3 upload;
`create_subject` records the subject.

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

## Rules

- Ground every fact in the source subject or the user's request — never fabricate
  numbers, quotes, or names.
- Choose `visibility` deliberately: `org` only when the document is meant for the
  whole workspace; otherwise `private` to the requester.
- Keep the spec and the stored bytes in sync — always store the exact spec you
  record on the subject (it is the source of truth for later edits/re-render).
