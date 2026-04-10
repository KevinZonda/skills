---
name: academic-slides
description: Create or revise academic slide decks (`.pptx`) for paper talks, group meetings, seminars, conference reports, progress updates, and thesis defenses. Use when Codex needs to turn research content, figures, tables, papers, or an existing deck/template into a rigorous academic talk with white background, black text, Arial for English, HeiTi for Chinese, fixed headers and page numbers, one claim per slide, low text density, and backup slides after acknowledgements.
---

# Academic Slides

## Overview

Produce slides for spoken academic presentations, not marketing decks. Optimize for clarity, pacing, and scientific credibility.

Default academic progress decks in this environment should follow the `SoftwareProgress` style template:
- repeated deck title and short context subtitle across slides
- one concrete work package, subsystem, or deliverable per slide
- task or result titles instead of slogans
- 2-4 concrete progress bullets written as full sentences, not slogan fragments
- default to a single main text column; only split into columns when one side is occupied by an image, table, or other evidence block
- each content slide should include at least one figure, table, screenshot, or workflow diagram when the topic permits it
- black text on white background with restrained use of blue/red emphasis

Use `assets/template.pptx` as the bundled starting template or geometry reference. Read `references/style-guide.md` for the full rules, `references/slide-recipes.md` for common slide types, and `references/template-spec.md` when matching the bundled template.

## Workflow

1. Determine the talk format before making slides.
   - Identify the setting: conference, group meeting, candidacy, thesis defense, paper reading, or progress report.
   - Identify the time budget. Default to at most 20 main slides for a 15-minute talk unless the user gives a different constraint.
   - Reserve backup slides after acknowledgements.

2. Build a slide-by-slide story first.
   - Write the message of every slide in one line before designing it.
   - Enforce one slide, one claim. If a slide contains two unrelated claims, split it.
   - Keep background short. Default to no more than 3 background slides unless the topic truly requires more.
   - For progress or software update talks, default to result-first ordering: one work package, subsystem, or deliverable per slide; do not spend multiple slides on generic framing.
   - Unless the user explicitly asks for another format, treat the `SoftwareProgress`-style progress template as the default academic progress layout.

3. Choose concrete section titles.
   - Avoid generic headings such as `Background`, `Experiment`, or `Results and Discussion`.
   - Use titles that expose the logic of the talk, such as `Event Selection Strategy`, `Detector Geometry Constraints`, or `Mass Resolution Improvement`.
   - Keep the section header position and slide-title position fixed across the deck.
   - Prefer task or result titles over slogans. `Development of Kafka-based automated validation` is usually better than `Why Automation Matters`.

4. Apply the hard visual rules.
   - Use white background and black text by default.
   - Use `Arial` for English and `黑体` for Chinese. Override conflicting template defaults.
   - Keep text sparse. Prefer figures, tables, schematics, and plots with only the words needed to guide the audience.
   - Add page numbers to every slide except the title slide.
   - Do not add humor, decorative backgrounds, unnecessary arrows, irrelevant images, or flashy transitions.
   - Only use color when it improves structure or emphasis. Default to black; if emphasis is needed, prefer red or blue.
   - Avoid over-building slides from many small boxes. The default progress template should read through a few larger blocks, not a field of micro-cards.

5. Structure content for speaking, not reading.
    - Only place content that will actually be discussed on the current slide.
    - Move secondary material, anticipated questions, and extra derivations to backup slides after acknowledgements.
    - Do not paste dense multi-panel paper figures unchanged; split them into separate slides when needed.
    - Write as fragments, labels, or bullets rather than full prose sentences.
    - In progress reports, make the hard evidence explicit: concrete module names, baseline names, comparison targets, and quantitative outcomes should appear on the slide whenever they are central to the claim.
    - In the default progress template, bullet items should usually be full technical sentences rather than very short fragments.
    - Avoid text-only multi-column layouts. If there is no image or table to justify a split layout, keep the text in one main reading block.

6. Validate before delivery.
   - Check spelling, abbreviations, units, axis labels, superscripts/subscripts, and figure readability from the back row.
   - Check that every non-title slide has a stable header, a specific slide title, and a page number.
   - Check playback on another machine if the deck contains media or animations.
   - Remove anything the presenter will not say aloud.
   - Compare the output against the default `SoftwareProgress`-style template for slide density, title specificity, number of major blocks per slide, and how concretely results are stated.

## Bundled Resources

- `assets/template.pptx`: bundled template supplied by the user; use it as a starting point or layout reference.
- `references/style-guide.md`: detailed academic slide rules and delivery checklist.
- `references/slide-recipes.md`: concrete patterns for title, outline, content, conclusion, acknowledgement, and backup slides.
- `references/template-spec.md`: extracted geometry and override notes for the bundled template.

## Output Requirements

- Deliver an editable `.pptx`.
- If the deck is generated programmatically, also deliver the source used to generate it.
- Keep backup slides in the same deck after acknowledgements unless the user explicitly asks for a separate appendix deck.
