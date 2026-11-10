# Readability: the core standard

Write every page for a reader with no working memory to spare: tired, interrupted, skimming between two other tasks. If that reader gets it, everyone does. These rules apply to the whole page, not only the TL;DR. `$WAB/scripts/verify.sh` warns on the measurable ones (⚠ lines); the rest are yours to apply.

What drives the rules:

1. **What isn't on screen is forgotten.** Never make the reader hold a fact from an earlier section to understand this one.
2. **Knowing isn't doing.** The step between "I get it" and "I did it" is where a reader drops off; the page ends on an action.
3. **Starting is the hardest part.** The first thing the reader sees must answer "what is this and does it matter to me?".
4. **Vague sizes all feel the same.** "Some", "a few", "a while" carry nothing; numbers do.
5. **Wins that aren't visible don't register.** What now works is said plainly and early.

## Rules

1. **Lead with the outcome.** Every section's first line (its `takeaway`) is the result, not the background: "Every 6 hours, a check disabled Ido", not "To understand the issue, we first need to look at how accounts work". Background comes after, and only if needed.
2. **Takeaways are one or two short sentences, ≤ 25 words.** Read in order, the takeaways tell the whole story (the takeaway test). ⚠ when over 25 words.
3. **Short paragraphs.** ≤ 3 lines, ≤ 60 words. One idea per paragraph. A paragraph that needs a second read gets shorter or becomes a block (table, before/after, steps). ⚠ when over 60 words.
4. **Numbers, not adjectives.** "6 people, 35 memberships, every 6 hours", not "several users, regularly". Times and dates are concrete ("15:43 UTC", "since Nov 4"). Time estimates are ranges in units ("about 15 minutes", "one afternoon").
5. **Ordered actions are numbered `<Steps>`.** One bounded action per step, no "and then" twice. Done steps say so (✓), the next one is marked ("Next: …").
6. **Lists stay at ≤ 5 items.** Group or rank longer ones, or split into "now" and "later". ⚠ when a list runs past 5.
7. **One word per thing, plain words first.** Pick one name per concept and keep it everywhere (prose, tables, diagrams, TL;DR). Prefer the everyday word ("sign-in") to the system's word until a `<Term>` introduces the system's word.
8. **Matter-of-fact about failures.** State what broke, the cause and the fix. No "unfortunately", no drama, no blame.
9. **No filler.** No preamble ("In this document we will…"), no recap of what the reader just read, no closing pleasantries, no hedges that carry nothing ("perhaps", "basically", "it is worth noting"), no idioms ("circle back", "get the ball rolling"). Keep a hedge only when the uncertainty is real, and say what is uncertain. ⚠ on common hedges and idioms.
10. **Tangents get their own place.** A second issue doesn't interrupt the story; it goes to *What's next* (or a short "Separately:" note at the end of its section).
11. **End on one action.** The TL;DR's last row and the page's last section each name what the reader does next, even when the answer is "Nothing: it resolves on deploy".
12. **Honest status.** Merged is not deployed; planned is not agreed. Say which, with links.

## Before you publish

Read only the TL;DR and the first line of each section. Do you know (a) what happened and (b) what to do next? If not, rewrite those lines before touching anything else.
