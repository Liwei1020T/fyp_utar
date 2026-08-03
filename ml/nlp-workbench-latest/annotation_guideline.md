# StringSense Gold Annotation Guideline v1

## Purpose

This task creates human Gold labels for badminton-string reviews. Annotators
must judge only the review text shown in their blind CSV. Do not inspect Silver
labels, model predictions, the other annotator's file, or product scores.

## Annotation unit

Each CSV row is one review. Fill one label for every aspect column:

- `attack`: attack, smash power, shuttle speed, repulsion, power transfer.
- `comfort`: softness, shock, arm or hand comfort, forgiveness.
- `control`: placement, touch, holding feel, net control, directional accuracy.
- `durability`: breakage, fraying, lifespan and resistance to wear.
- `elasticity`: bounce, responsiveness, elasticity and effortless power.
- `sound`: impact sound, crispness, loudness and acoustic feel.
- `string_movement`: string shifting, displacement and ability to stay aligned.
- `tension_retention`: tension loss, pound loss and performance stability over time.
- `value_for_money`: price, affordability and whether performance justifies cost.

`attack` is the internal NLP name. It covers the user-facing Attack / Repulsion
concept and remains distinct so the existing Silver and TF-IDF baseline is not
silently relabelled.

## Allowed labels

- `not_mentioned`: the aspect is not expressed or cannot reasonably be inferred.
- `positive`: the review expresses a positive opinion about the aspect.
- `negative`: the review expresses a negative opinion about the aspect.
- `neutral`: the aspect is mentioned factually without positive or negative opinion.
- `mixed`: both positive and negative opinions about the same aspect are present.
- `uncertain`: there is relevant text, but the intended aspect or polarity cannot be
  decided reliably. Use this sparingly and explain it in `annotator_notes`.

Use the exact lowercase values above. Do not invent labels or leave completed
files blank.

## Decision rules

1. Label the stated experience, not general product reputation or your own opinion.
2. Negation changes polarity: `不耐打` is negative durability.
3. Contrast preserves both sides: `弹但容易断` is positive elasticity and negative
   durability, not mixed for either aspect unless both polarities target that same
   aspect.
4. A comparison may label more than one aspect. `比 BG65 更弹但更容易断` is positive
   elasticity and negative durability for the reviewed string.
5. Product names, prices and tension numbers alone do not imply sentiment.
6. Chinese, English and code-mixed reviews follow the same label definitions.
7. Repeated emphasis does not create a second opinion.
8. If the text is too short or genuinely ambiguous, prefer `uncertain` over guessing.

## Blind workflow

1. Annotator A and B receive separate CSV files with identical review samples.
2. Each annotator completes all nine label columns independently.
3. Run strict validation before merging.
4. The merge tool calculates per-aspect and overall agreement and creates an
   adjudication CSV.
5. An adjudicator fills unresolved disagreements. Only then may the Gold export
   command create `gold_dataset.csv`.

## Examples

Review: `出球很弹，杀球有力，但是两天就断了。`

- `attack=positive`
- `elasticity=positive`
- `durability=negative`
- all unrelated aspects: `not_mentioned`

Review: `声音清脆，不过用久以后声音变闷。`

- `sound=mixed`

Review: `穿了 26 磅。`

- all aspects: `not_mentioned`
