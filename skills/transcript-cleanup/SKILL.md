---
name: transcript-cleanup
description: Correction policy for cleaning raw meeting transcripts — fix ASR errors without altering meaning. Used by the transcript workflow's clean-transcript phase.
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
