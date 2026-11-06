"""Figure 2: conditional generation, drawn to match Section III-E of the paper."""

from diagram import Canvas

W, H = 2200, 830
c = Canvas(W, H)

BW, BH = 368, 190
GAP = 56
LEFT = 68
ROW1 = 80
ROW2 = 390
ROW3 = 625

xs = [LEFT + i * (BW + GAP) for i in range(5)]

c.box(xs[0], ROW1, BW, BH, [
    "Design specification",
    "target family",
    "structural constraint",
    "functional requirement",
], style="input", badge=1)

c.box(xs[1], ROW1, BW, BH, [
    "Control tags",
    "drawn from the dataset",
    "annotations of Section III-B",
], style="input", badge=2)

c.box(xs[2], ROW1, BW, BH, [
    "Prompt",
    "control tags prepended",
    "to the generation context",
], style="model", badge=3)

c.box(xs[3], ROW1, BW, BH, [
    "Adapted LLM",
    "autoregressive decoding",
    "temperature · top-k · top-p",
], style="model", badge=4)

c.box(xs[4], ROW1, BW, BH, [
    "Candidate sequences",
    "generated under the",
    "stated conditions",
], style="model", badge=5)

for a, b in zip(xs, xs[1:]):
    y = ROW1 + BH / 2
    c.arrow([(a + BW, y), (b - 8, y)])

# ------------------------------------------------- condition check
c.box(xs[4], ROW2, BW, 150, [
    "Conditions satisfied?",
    "tags present in the output",
], style="filter", badge=6)
c.arrow([(xs[4] + BW / 2, ROW1 + BH), (xs[4] + BW / 2, ROW2 - 8)])

# accept path
c.box(xs[4], ROW3, BW, 150, [
    "To filtering",
    "Fig. 1, stage 5",
], style="struct", badge=None)
c.arrow([(xs[4] + BW / 2, ROW2 + 150), (xs[4] + BW / 2, ROW3 - 8)])
c.label("yes", xs[4] + BW / 2 + 46, (ROW2 + 150 + ROW3) / 2, fs=24)

# reject path: back round to the model
back_y = ROW2 + 150 + 62
c.arrow([
    (xs[4], ROW2 + 75),
    (xs[3] + BW / 2, ROW2 + 75),
    (xs[3] + BW / 2, ROW1 + BH + 8),
], colour="#8C3A3A")
c.label("no — regenerate", (xs[3] + BW / 2 + xs[4]) / 2, ROW2 + 75, fs=24,
        colour="#8C3A3A")

# ------------------------------------------------- note
c.note(LEFT, ROW2 + 25, BW * 3 + GAP * 2, 195, [
    "Control tags condition generation on an explicit requirement rather than leaving it unconstrained.",
    "A candidate that does not carry the requested tags is returned for regeneration, so compliance is",
    "checked before any structural prediction is attempted — the stage that dominates pipeline cost.",
])

size = c.save("fig2_conditional.png")
print("fig2_conditional.png", size)
