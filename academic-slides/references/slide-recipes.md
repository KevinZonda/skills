# Academic Slide Recipes

## Slide budget

- 10-minute talk: usually 8-12 main slides
- 15-minute talk: usually 12-18 main slides
- 20-minute talk: usually no more than 20 main slides
- Reserve 2-6 backup slides after acknowledgements

## Title slide

- Center the title.
- Put speaker, affiliation, and date below the title.
- Add collaborators only if they are relevant to authorship or supervision.
- Keep the slide visually sparse.

## Outline slide

- Organize around the logic of the talk.
- Prefer outline items such as `Dataset and Selection`, `Calibration Strategy`, `Signal Extraction`, `Systematic Uncertainties`, `Physics Reach`.
- Do not read each line verbatim during the talk.

## Standard content slide

- Include a fixed section header.
- Include a slide-specific title that states the claim or task.
- Use one dominant visual block: one figure, one table, or one schematic cluster.
- Add 1-3 short bullets or labels only if they help the audience parse the visual.
- End with a visible takeaway if the conclusion is not obvious from the figure.
- For progress talks, the slide title should usually be the module, task, or result being reported, not a slogan about why it matters.
- For default progress decks, keep the deck-level title and context line fixed across slides and vary only the work-package title and body content.

## Method or setup slide

- Show the pipeline, detector region, workflow, or data sample visually.
- Keep procedural text short.
- Name the one setup choice that matters for later interpretation.

## Result slide

- Make the result figure dominant.
- State the comparison baseline explicitly.
- Highlight only the one or two curves, bins, or regions that support the claim.
- If a result requires multiple conclusions, split it into multiple slides.
- Include concrete result markers whenever available: throughput, latency, efficiency, resolution, speedup, acceptance rate, bug count, or other task-relevant numbers.

## Progress update slide

- Use the default `SoftwareProgress`-style repeated deck-level frame: deck title, short context subtitle, slide-specific work-package title, then compact progress bullets and optional evidence.
- Keep the slide body anchored on one work package or subsystem.
- State 2-4 concrete progress points as full technical sentences, not generic ambitions.
- If the slide is about a system, include the actual subsystem name, interface, or artifact contract.
- If the slide is about performance, state the baseline and the key numbers.
- Use screenshots, architecture sketches, or small benchmark panels when they make the result more concrete than text alone.
- If there is no screenshot, table, or figure, default to one text block rather than splitting the page into text columns.
- Prefer pairing the text block with a concrete visual block: a workflow diagram for systems work, a benchmark or metric table for performance work, or a screenshot for UI/tooling work.

## System progress slide

- Default successful pattern:
  left block = 2-4 full-sentence progress bullets
  right block = one workflow / control-flow / data-flow diagram
- Use this pattern when the topic is a software system, orchestration layer, workflow engine, or tooling stack and no better evidence image exists.
- The bullets should report what was built, constrained, improved, or re-planned.
- The diagram should explain why the reported progress matters operationally.

## Literature figure adaptation

- Download the cleanest available source figure.
- Crop tightly to the relevant content.
- Split composite figures across slides instead of shrinking them to unreadable size.
- Replace panel-letter references with local labels when needed.

## Conclusion slide

- Keep 2-4 bullets.
- Each bullet should be a conclusion, not a topic name.
- Tie conclusions back to the talk goal or physics question.

## Acknowledgement slide

- List advisor, collaborators, and funding.
- Keep it short.
- Do not add `Thank you` or `Thanks for listening`.

## Backup slides

- Place all backup slides after acknowledgements.
- Label them clearly as `Appendix` or `Backup`.
- Include items that support Q&A: selection details, alternative plots, control studies, extra tables, derivations, or dataset checks.
