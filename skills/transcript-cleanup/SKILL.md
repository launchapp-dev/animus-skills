---
name: transcript-cleanup
description: Correct ASR errors, punctuation, speaker labels, and obvious transcript noise without changing meaning or summarizing. Use only when cleaning a raw meeting transcript or when the Animus transcript workflow invokes its clean-transcript phase; do not rewrite ideas, omit content, or produce meeting notes.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---

# Transcript Cleanup

You are cleaning a raw speech-to-text meeting transcript. Your only job is to
correct transcription errors — never to edit the conversation itself.

## Correction policy

1. Correct ONLY transcription errors: misheard homophones, garbled proper
   nouns and product names, broken or misattributed speaker turns, and ASR
   punctuation artifacts.
2. Never paraphrase, summarize, reorder, or invent content. Preserve original
   wording, speaker labels, and timestamps exactly.
3. Proper-noun glossary — normalize these when misheard: Animus (not
   'animos'/'enemas'), Krisp (not 'crisp'), Granola, LaunchApp, Postgres,
   MCP, OAuth, worktree, daemon, Rafal.
4. Mark genuinely unintelligible spans as `[inaudible]` instead of guessing.
5. Read the raw transcript from the subject's `data.raw_transcript` and leave
   that field untouched; write the corrected transcript to the subject body in
   ONE subject update call, adding a labels entry `cleaned` in the same call.
