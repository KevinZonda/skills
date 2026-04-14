---
name: academic-paper-writing
description: Guide and draft academic papers (high-energy physics and machine learning focus) following a rigorous section-by-section structure: Abstract, Introduction, Method, Results, Discussion, Conclusion. Use when the user needs to write, review, restructure, or improve an academic manuscript — including drafting sections, critiquing drafts against the structure below, or generating outline scaffolds.
---

# Academic Paper Writing

## Overview

This skill provides a prescriptive structure for writing research papers, primarily targeting high-energy physics (HEP) and machine learning (ML) audiences. Each section has a defined internal logic. Follow it both when drafting from scratch and when critiquing an existing draft.

---

## Paper Structure

### 1. Abstract

The abstract must cover five elements **in order**. Do not merge or reorder them.

| Part | Guidance |
|------|----------|
| **a. Background** | State the current landscape and its deficiency. Two components: (1) what is known / what exists; (2) what is missing, insufficient, or problematic. |
| **b. Purpose** | Directly respond to the deficiency stated in (a). The purpose sentence must be traceable to the gap — do not introduce new motivation here. |
| **c. Method** | Concisely name the approach, dataset, and key design choices. |
| **d. Results** | State the quantitative or qualitative outcome. Be specific — include numbers when the journal/venue permits. |
| **e. Conclusion** | Abstract and elevate the results to a higher-level insight. **Do not repeat the result sentence verbatim.** The conclusion should answer: "What does this finding mean for the field, the theory, or future work?" |

---

### 2. Introduction

The introduction follows a five-step funnel.

#### a. Research background and purpose
Open with the broad scientific or technical context. State the research objective early so the reader knows the destination before the literature review begins.

#### b. Related work, expected outcomes, and current status
Identify the specific sub-area(s) relevant to the objective. Describe what has been attempted, what is expected from theory or prior experiment, and where the field currently stands.

#### c. Systematic literature review
Build on (a) and (b) to survey the literature **in relation to the stated objective**. Requirements:
- Organize references into a logical taxonomy: by research sub-field, by methodological approach, by chronological development, or by any other principled scheme — but never as a flat sequential list.
- Synthesize, do not annotate. For each group, summarize the collective finding and its significance, not a paper-by-paper description.
- Use the literature to establish what is established, what is contested, and what is merely assumed.

#### d. Research gap
Based on (c), identify the specific gap: what question the community has not yet answered, what limitation no existing method addresses, or what contradiction remains unresolved. The gap must follow logically from the review — it should feel inevitable, not asserted.

#### e. This paper's contribution
State concisely: (1) which gap this paper addresses, (2) the high-level research design (study type, methodology, data), and (3) the scope. End with a brief roadmap of sections if the journal convention requires it.

---

### 3. Method

Follow the conventions of the relevant sub-field:

**High-Energy Physics (HEP):**
- Detector description and data-taking conditions (beam energy, luminosity, run period)
- Monte Carlo simulation and generator settings
- Event selection and cut flow with efficiency and background rejection
- Observable definitions, kinematic variables, and units
- Systematic uncertainty sources and estimation procedure
- Statistical analysis framework (likelihood, frequentist / Bayesian choice)

**Machine Learning:**
- Dataset description (source, size, splits, preprocessing, class balance)
- Model architecture and key design choices with justification
- Loss function and training objective
- Optimization: optimizer, learning rate schedule, regularization, early stopping
- Evaluation metrics and their definition
- Baseline models and comparison protocol
- Implementation details: framework, hardware, training time, random seeds

For combined HEP+ML papers (e.g., particle reconstruction with deep learning), cover both blocks in logical order — detector and data first, then the ML pipeline applied to that data.

---

### 4. Results

#### Figures and tables
- Every figure and table must be **self-contained**: a reader who skips the body text must understand what is shown from the caption alone.
- Caption requirements: (1) a specific descriptive title — not "Figure 1" but "Energy resolution as a function of pseudorapidity for the upgraded calorimeter"; (2) all symbols, colors, and line styles defined; (3) units stated; (4) any selection or condition applied to produce the plot noted.
- Axis labels must include units. Legends must not overlap data.

#### Describing results
Use a **topic-sentence-first (general → specific)** structure for each result block:
1. **Topic sentence**: one sentence stating the main finding of this result block.
2. **Supporting description**: walk through the evidence — panel by panel, row by row, or condition by condition — to substantiate the claim.
3. **Quantitative anchors**: every non-trivial claim should cite a number (value ± uncertainty, percentage improvement, significance in σ, etc.).

Do not interpret or explain results in this section. Save causal arguments and comparisons to prior work for Discussion.

---

### 5. Discussion

The discussion has four required paragraphs (or paragraph groups). Do not collapse them.

#### a. Summary of principal findings (paragraph 1)
Open with a concise restatement of the main results. This paragraph serves readers who skip from Abstract directly to Discussion. Keep it tight — two to four sentences.

#### b. Comparison with prior work (paragraph 2)
For each principal finding:
- Find relevant published results and compare directly (same observable, similar conditions).
- If results **agree**: cite and briefly explain why agreement is expected.
- If results **disagree**: explicitly state the discrepancy, then analyze the likely causes (different dataset, different selection, different model architecture, different systematic treatment, different definition of the observable, etc.). Do not downplay disagreements.

#### c. Practical significance and generalizability (paragraph 3)
Elevate the findings beyond the immediate experiment:
- What does this mean for practitioners, experimentalists, or theorists?
- How broadly does the result generalize? (Different detectors, different energy scales, different datasets, different domains?)
- What design decisions or policy choices does this inform?

#### d. Limitations (paragraph 4)
State the boundaries of the result honestly:
- Data limitations (statistics, coverage, selection bias)
- Model or method limitations (assumptions, approximations, known failure modes)
- What the study does **not** address that a reader might expect
- What follow-up work is required to extend the validity

Do not frame limitations as future work. Acknowledge them as current constraints.

---

### 6. Conclusion

- Synthesize the overall contribution in three to five sentences.
- Do not introduce new results or new citations.
- End with the broader implication or the most important open question the work raises.
- The conclusion is not a second abstract — it should read as a forward-looking synthesis, not a backward-looking summary.

---

## Cross-Cutting Rules

### Language and style
- Prefer active voice for method descriptions; passive voice is acceptable for results when the subject is the observable rather than the authors.
- Avoid hedging chains: "it may be possible that" → "this suggests".
- State uncertainty explicitly (statistical vs. systematic; aleatory vs. epistemic) rather than using vague qualifiers.

### Citation discipline
- Cite the original source, not a review that cites it.
- When a claim is common knowledge in the sub-field, no citation is needed; when it is not, cite it.
- Do not cite papers you have not read. If you are uncertain about a reference, flag it for the user to verify.

### Consistency checks before submission
- Abstract conclusion ↔ Discussion paragraph (c): same level of claim?
- Introduction gap ↔ Contribution statement: does the paper address exactly the gap it identified?
- Method ↔ Results: every reported metric must be defined in Method.
- Results numbers ↔ Abstract numbers: must match exactly.
- All figures cited in text in the order they appear.
