# Academic Slides Style Guide

## Core principles

- Make the deck serve the talk. The audience should understand the story without being forced to read paragraphs.
- Put one claim or one question on each slide.
- Show only material that will actually be discussed on that slide.
- Move secondary details, likely questions, and supporting derivations to backup slides after acknowledgements.
- Do not add humor. Academic talks should read as professional and controlled.
- For progress updates, make the deck result-first: each slide should map to one work package, subsystem, or deliverable, not to one abstract theme.
- In this environment, the default academic progress template is the `SoftwareProgress` style: repeated top matter, concrete work-package titles, compact progress bullets, and limited decorative structure.

## Hard visual rules

- Use white background and black text.
- Do not use decorative backgrounds or theme-heavy templates.
- Use `Arial` for English and `黑体` for Chinese.
- Do not use `Times New Roman`, `宋体`, or ad hoc personal font choices.
- Keep typography consistent through the deck.
- Default text size range is 20-28 pt.
- A practical default system is:
  - section header: 20 pt bold
  - slide title: 24-28 pt bold
  - body text: 20-24 pt
  - page number: 14-18 pt

## Page structure

- Exclude page number on the title slide.
- Add page number on every other slide.
- Keep the section header and slide title in fixed positions across the deck.
- Use concrete titles that tell the audience what this page is doing.
- Avoid empty labels such as `Background`, `Experimental Part`, or `Results`.
- Prefer task or result titles over slogans. In software progress talks, titles should usually name the module, method, or system being advanced.
- For default progress decks, keep a repeated deck-level title and short context subtitle across slides, then place the slide-specific work-package title below.

## Content density

- Use figures, plots, tables, and diagrams as the dominant content.
- Use only the minimum text required to orient the audience.
- Avoid large text blocks.
- Use bullet fragments rather than full sentences.
- Use standard round bullets when bullets are needed.
- Use line spacing around 1.25-1.5 for short bullet lists.
- Default progress decks should be denser than a concept pitch: reduce decorative structure first, not the specificity of the technical content.
- Prefer a few large reading blocks over a collage of micro-cards.
- In the default progress template, prefer full technical sentences over ultra-short fragments. The slide should read like a concise progress report, not like slogan bullets.
- Avoid text-only column splits. If both columns are just text, that is usually a sign the content should be recomposed into one stronger reading block.
- Pure text progress slides should be rare. When the topic allows it, add at least one figure, table, screenshot, or workflow diagram per slide.

## Figures and tables

- Do not place irrelevant images.
- Do not paste paper figures blindly, especially dense multi-panel figures.
- Split dense literature figures into multiple slides when different panels support different claims.
- Remove panel labels such as `(a)(b)(c)(d)` when they are no longer needed.
- Use high-resolution source images when possible.
- Ensure plots remain readable for the last row, including axis labels, tick labels, legends, and line weights.
- For software or systems progress decks, use concrete artifacts when possible: architecture snippets, benchmark tables, ablation plots, workflow diagrams, screenshots, or result numbers.
- Split a slide into columns only when one side is occupied by such an artifact. Do not create multi-column text layouts without evidence content.

## Color and emphasis

- Use color only when necessary to clarify structure or highlight a result.
- Default to black text on white background.
- If emphasis is necessary, prefer red or blue.
- Avoid bright yellow, green, cyan, and decorative text fills.
- Do not add colored text backgrounds unless there is a strong reason.

## Animation and motion

- Avoid slide transition effects.
- If progressive reveal is necessary, only use simple `Appear` style reveals.
- Do not use animations to create suspense or jokes.

## Title slide

- Center the talk title.
- Include speaker name, affiliation, and date.
- For research talks, include major collaborators and advisor.
- Emphasize the speaker name with bold and underline when appropriate.
- Put the advisor last and mark with `*` when that convention is expected.
- Use `we`, not `I`, when presenting collaborative research.

## Outline and flow

- Build the outline around the logic of the work, not generic report labels.
- Do not put `Acknowledgements` in the outline.
- Keep background short; in most cases it should not exceed 3 slides.
- Enter the research question quickly.
- Avoid broad and inflated framing that delays the main content.
- In progress reports, background should usually collapse to one short setup line. The main body should move quickly into what was built, improved, measured, or validated.

## Acknowledgements and backup

- Acknowledgements should include advisor, collaborators, and funding.
- Do not write `Thanks for listening`, `Thank you`, or similar filler.
- Put backup slides after acknowledgements.
- Backup slides may include anticipated questions, secondary checks, derivations, extra tables, or omitted controls.

## Pre-delivery checklist

- Check spelling and grammar.
- Check abbreviations and define nonstandard ones.
- Check physical quantities, units, superscripts, and subscripts.
- Check axis labels and tick marks.
- Check slide numbers.
- Check that each slide has one clear message.
- Check that anything shown is something the presenter will explain.
- Check that playback still works on another machine when media is embedded.
- Compare against the default `SoftwareProgress`-style template for title specificity, result concreteness, and the number of major content blocks per slide.
