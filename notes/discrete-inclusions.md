# Discrete inclusions: what the data says before any loss is written

A proposal came in for per-voxel material labels — K-means on the section photographs for the
material classes, a volume quota from their area fractions, a relaxed-band volume loss, a
total-variation term for spatial coherence, an entropy term to harden the labels, and a hard
argmax at the end feeding per-material physics.

The machinery is a good fit for this lattice: one primitive per cell already, `cell_level.pt`
and `cell_face.pt` already written alongside it, and `report/dynamic_cut.py` already cutting by
connected components and running a solver per piece. A `cell_material.pt` is a short step, and
a discrete label is exactly what a physics engine wants.

Three things were measurable without training any of it. All three came back against the
proposal's premises, and they are recorded here so the premises are not assumed again.

Reproduce with `notes/measure_inclusions.py <ply> <lattice_dir>`.

## 1. Only one of the four objects has a discrete material at all

K-means in LAB over each object's own section photographs, separation measured as the mean
between-centre distance over the mean within-cluster spread:

              K=2    K=3    K=4    K=5    K=6    K=7    K=8
    orange    3.09   3.33   3.72   4.02   3.91   4.10   4.35
    melon     3.71   3.64   4.09   4.20   4.38   4.55   4.85
    loaf      3.25   4.29   5.18   5.65   6.54   6.87   7.38

All three rise monotonically. A real class structure gives a knee at the right K and then
flattens; a monotone rise is the signature of slicing a continuous gradient finer. The loaf
rises fastest despite its cinnamon swirl looking the most like two substances.

The exception is the watermelon at K≥4: a cluster at **1.7%** of pixels, centre (93, 42, 34),
far from every other centre and not split further at K=5. Those are the seeds, and they are
the only discrete material in the set. The orange, the loaf and the doughnut are continuous
colour fields, and a hard argmax over them would turn a gradient into flat bands.

**So this is a method for sparse discrete inclusions, not for material segmentation in
general.** That is a narrower claim and a better one: the motivation is concrete, the metric
is concrete, and the physics consequence is real.

**Correction, from building the exporter.** The claim above that the loaf is a continuous
field is wrong, and the K-sweep is the wrong test for it. Separation over all K clusters rises
monotonically when any distribution is sliced finer, so it cannot distinguish a gradient from
a gradient with something embedded in it. Asking the narrower question -- how far does the
*darkest* centre stand off from the next, in units of the clusters' own spread -- separates
them, and the loaf scores 4.64 against the orange's 2.12. Painting that cluster back onto the
photograph shows it is the cinnamon swirl, exactly and only. The loaf has two materials.

## 2. The material was not crushed. It was scattered.

`models/watermelon_k1d8_blendinit.ply`, dark interior cells against the photographs:

                        photographs        model
    fraction            3.11 ± 3.17 %      1.97 % by volume
    connected pieces    1,095              1,569
    median piece        10 px              **1 cell**
    singletons          26 %               **65.8 % of pieces**
    mean / p90 / max    —                  4.4 / 7 / 160 cells

The total survived — same order of magnitude — and the organisation did not. Two thirds of the
pieces are one isolated cell. A single interior slab has 116 dark pieces where the photograph
of the same cut has 19, and 91% of them are single pixels against the photograph's 26%.

A claim I made here and then measured, wrongly: that the seeds' radial arrangement was lost.
A watermelon is three fused carpels and its seeds sit on the lines where they meet, so a
transverse cut should show them in six groups. **The photographs do not show it.** Six-fold
concentration averages 0.311 ± 0.206 against a uniform null of about 1/sqrt(n) = 0.205, and
the split is diagnostic: every photograph with many seeds is at or below its own null (228
seeds → 0.028 against 0.066; 23 → 0.077 against 0.209), while every high value comes from a
photograph with five to eight detections, where 0.88 arises by chance.

So there is no angular structure in the supervision, and the model cannot be faulted for
lacking one. This removes carpel alignment as a metric, and it removes the strongest argument
for constraining during training rather than organising afterwards: there is no 3-D
arrangement to learn.

**The failure is not the volume loss's to fix.** It is spatial, so the TV term is the load-
bearing part of the proposal and the volume term is not.

The consequence that matters is not visual. `report/dynamic_cut.py` cuts by connected
components; 1,569 isolated cells assigned as rigid bodies is a thousand rigid crumbs where
there should be two hundred seeds.

## 3. A quota from 2-D area fractions would be six times too large

The interior is 385,816 coarse cells, a ball of radius 45.2 cells, so 90 cells across. At a
melon diameter of 180–250 mm that is a cell of 2.0–2.8 mm, and a seed of 9–11 × 5.5–7 × 2–2.5 mm
is:

    melon 180 mm   cell 1.99 mm   seed 4.5 × 2.8 × 1.0 cells    6.5 cells
    melon 200 mm   cell 2.21 mm   seed 4.1 × 2.5 × 0.9 cells    4.8 cells
    melon 250 mm   cell 2.77 mm   seed 3.3 × 2.0 × 0.7 cells    2.4 cells

Two things follow.

**A seed is under one cell thick.** The lattice cannot resolve a seed's shape at this
resolution; the best it can represent is a clump of about five cells. Any coherence term is
working against the discretisation, and no amount of it produces a seed-shaped seed. The
model's p90 of 7 cells is already the right size — the median of 1 is the defect.

**The volume fraction is nothing like the area fraction.** Two hundred to four hundred seeds
in a 200 mm melon is **0.33–0.66 %** by volume. The photographs read 3.11 % by area and the
model holds 1.97 % by volume. So the area fraction over-reads the true volume fraction by
about six, partly because a darkness threshold catches shadow and dark flesh as well as seed,
and partly because Delesse's area-equals-volume needs isotropic uniform random sections and
these are two privileged families chosen about the object's axis.

A quota of 3.11 % against a truth near 0.5 %, with a ±15 % band around it, would spend the run
pushing the model to make *more* dark material — and it already has three to six times too
much.

## What the numbers do support

    problem      sparse inclusions are scattered, not clumped, and not where they belong
    target       pieces of about 5–7 cells, from a median of 1 and 65.8 % singletons
    metrics      piece count, median piece size, singleton fraction
    volume       an upper bound near 0.5 %, not a target to pull toward
    limit        a seed is ~1 cell thick here; a finer lattice or a sub-cell representation
                 is required before "seed-shaped" is even expressible

One measurement that was expected and did not appear: the seed area fraction is the same in
both cut families, transverse 3.12 ± 3.97 % against longitudinal 3.10 ± 2.26 %, a ratio of
0.99. Seeds on carpel lines should have biased the two apart -- and as above, the lines are
not in this data either, which is consistent. So a
per-family weighting is not needed — but the per-photograph spread is enormous (transverse
ranges 0.20 % to 19.07 %), so the standard error on the mean is 28 % relative. **A ±15 %
relaxation band is narrower than the uncertainty in the quota it relaxes around.** Whatever
band is used should be at least the quota's own confidence interval, and that is computable
rather than a hyperparameter.


## 4. The organisation can be recovered afterwards, in seconds

If the label is derived from the trained field rather than constrained during it, none of the
training-time machinery is needed. The lattice is a regular grid, so adjacency is free.
Reproduce with `notes/recover_inclusions.py`.

Target: a seed is 5-7 cells, a few hundred of them, about 0.5% of the interior by volume, and
the photographs themselves are 26% singletons.

    method                          pieces   volume   median   singletons
    as trained                       1,408    1.96 %       1        65 %
    majority vote >=8 of 26 nbrs       127    0.39 %       4        25 %
    smooth sigma 0.8, darkest 0.5%     167    0.50 %       4        23 %
    smooth sigma 1.2, darkest 1.0%     138    1.00 %       6        17 %
    binary opening, radius 1          none        —        —          —

Smoothing the colour field and taking the darkest half a percent lands on every target at
once, and its singleton fraction matches the photographs'. Opening deletes everything, which
is how fine the dust is: nothing survives a one-cell erosion.

**The volume fraction becomes a knob rather than a learned quantity.** Take the darkest q%,
with q from the physical estimate near 0.5%, and the spatial smoothing does the organisation.
That replaces the volume loss and the TV loss together, along with the annealing schedule that
carried them, at a cost of seconds against roughly twenty-five hours per object.

What it does not do: the render still shows the dust. Only the exported label is clean, which
is what a physics engine reads and is not what a viewer sees. Making the two agree means
writing the labels back into the colours, which is a separate decision. And the piece count,
127-167, sits below the 200-400 a real melon has, so some seeds are being merged or missed.
