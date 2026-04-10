# Bundled Template Spec

## Asset

- Template path: `assets/template.pptx`

## Deck geometry

- Aspect ratio: 16:9
- Slide size: 13.333 in x 7.5 in
- Slide count in bundled template: 1
- Active layout in the sample slide: title + content + slide number

## Extracted placeholder geometry

- Title placeholder: `x=0.447 in`, `y=0.250 in`, `w=12.484 in`, `h=0.722 in`
- Content placeholder: `x=0.470 in`, `y=1.419 in`, `w=12.445 in`, `h=5.477 in`
- Page number placeholder: `x=10.018 in`, `y=7.000 in`, `w=2.778 in`, `h=0.417 in`

## What to reuse

- Reuse the slide size.
- Reuse the general title/body/page-number placement if it fits the content.
- Keep the title region stable across slides.
- Keep the page number at the bottom-right on non-title slides.

## What to override

- Override all font defaults to `Arial` for English and `黑体` for Chinese.
- Ignore the template's noncompliant East Asian defaults such as `微软雅黑`, `宋体`, or other inherited placeholder fonts.
- Remove or avoid decorative color accents when rebuilding slides.
- Do not rely on the template's bullet styling.

## Practical usage

- If editing the bundled template directly, normalize fonts and colors before adding real content.
- If generating slides programmatically, treat this template as a geometry reference rather than a style authority.
