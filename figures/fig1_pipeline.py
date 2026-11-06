"""Figure 1: the LPDF pipeline, drawn to match Section III of the paper."""

from diagram import Canvas

W, H = 2200, 1090
c = Canvas(W, H)

BW, BH = 372, 184
GAP = 58
LEFT = 60
ROW1 = 70
ROW2 = 450
ROW3 = 830

xs = [LEFT + i * (BW + GAP) for i in range(5)]

# ---------------------------------------------------------------- row 1
c.box(xs[0], ROW1, BW, BH, [
    "Corpora & preprocessing",
    "UniProt · UniRef50 · PDB",
    "deduplicate · drop ambiguous",
    "length filter · provenance",
], style="input", badge=1)

c.box(xs[1], ROW1, BW, BH, [
    "Tokenization & embedding",
    "residue-level tokens over the",
    "20-letter vocabulary",
], style="input", badge=2)

c.box(xs[2], ROW1, BW, BH, [
    "Adapt base model",
    "LoRA (r=8, α=16) or",
    "full fine-tuning (lr 3e-5)",
], style="model", badge=3)

c.box(xs[3], ROW1, BW, BH, [
    "Conditional generation",
    "control tags from annotations",
    "temperature · top-k · top-p",
], style="model", badge=4)

c.box(xs[4], ROW1, BW, BH, [
    "Filter",
    "20 standard residues · length",
    "≤ 50% hydrophobic",
], style="filter", badge=5)

for a, b in zip(xs, xs[1:]):
    y = ROW1 + BH / 2
    c.arrow([(a + BW, y), (b - 8, y)])

# ---------------------------------------------------------------- row 2
c.box(xs[0], ROW2, BW, BH, [
    "ESMFold screen",
    "fold every candidate",
    "promote if mean pLDDT ≥ 70",
], style="struct", badge="6a")

c.box(xs[1], ROW2, BW, BH, [
    "AlphaFold2 confirm",
    "high confidence ≥ 80",
], style="struct", badge="6b")

c.box(xs[2], ROW2, BW, BH, [
    "Energy & stability",
    "Rosetta, or ProteinMPNN proxy",
    "length-normalized REU",
], style="struct", badge=7)

c.box(xs[3], ROW2, BW, BH, [
    "Homology search",
    "BLAST / HHsearch",
    "penalty above 80% identity",
], style="filter", badge=8)

c.box(xs[4], ROW2, BW, BH, [
    "Functional plausibility",
    "motifs · disorder · aggregation",
    "score in [0, 1]",
], style="filter", badge=9)

for a, b in zip(xs, xs[1:]):
    y = ROW2 + BH / 2
    c.arrow([(a + BW, y), (b - 8, y)])

# wrap: end of row 1 down and back to the start of row 2
wrap1 = ROW1 + BH + 88
c.arrow([
    (xs[4] + BW / 2, ROW1 + BH),
    (xs[4] + BW / 2, wrap1),
    (xs[0] + BW / 2, wrap1),
    (xs[0] + BW / 2, ROW2 - 8),
])
c.label("candidates that pass filtering", xs[2] + BW / 2, wrap1, fs=24)

# ---------------------------------------------------------------- row 3
c.box(xs[0], ROW3, BW, BH, [
    "Masked re-sampling",
    "3–5 iterations; accept on",
    "pLDDT +5 or energy −2 REU",
], style="refine", badge=11)

c.box(xs[2], ROW3, BW, BH, [
    "Multi-objective ranking",
    "0.35 structure · 0.30 energy",
    "0.20 novelty · 0.15 function",
], style="model", badge=10)

c.box(xs[3], ROW3, BW, BH, [
    "Top-k candidates",
    "ranked, with provenance",
], style="out", badge=None)

c.arrow([(xs[2] + BW, ROW3 + BH / 2), (xs[3] - 8, ROW3 + BH / 2)])

# wrap: end of row 2 down and back to ranking
wrap2 = ROW2 + BH + 88
c.arrow([
    (xs[4] + BW / 2, ROW2 + BH),
    (xs[4] + BW / 2, wrap2),
    (xs[2] + BW / 2, wrap2),
    (xs[2] + BW / 2, ROW3 - 8),
])
c.label("four components per candidate", xs[3] + BW / 2, wrap2, fs=24)

# ------------------------------------------------- refinement loop
c.arrow([(xs[0] + BW * 0.30, ROW2 + BH), (xs[0] + BW * 0.30, ROW3 - 8)],
        colour="#8C3A3A")
c.label("below 70", xs[0] + BW * 0.30, (ROW2 + BH + ROW3) / 2, fs=23,
        colour="#8C3A3A")
c.arrow([(xs[0] + BW * 0.74, ROW3), (xs[0] + BW * 0.74, ROW2 + BH + 8)],
        colour="#8C3A3A")
c.label("re-screen", xs[0] + BW * 0.74, (ROW2 + BH + ROW3) / 2, fs=23,
        colour="#8C3A3A")

size = c.save("fig1_pipeline.png")
print("fig1_pipeline.png", size)
