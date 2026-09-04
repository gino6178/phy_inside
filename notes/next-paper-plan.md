# Physically interactive digital twins from cut photographs

**Pain.** Generated 3D assets carry appearance and nothing else. TRELLIS.2 and Hunyuan3D 2.1
put full PBR on the *outer surface*; cut the asset open and the material description vanishes.
FruitNinja, GaussianFluent and InnerGS give the interior a colour per primitive and no statement
about what anything *is*. So a generated object cannot be lit correctly when opened, cannot be
deformed heterogeneously, and cannot resist a knife.

**Claim.** From two to three uncalibrated, family-labelled cut photographs we recover a
*material field* on the volume -- a small inventory of substances with optical (SVBRDF + SSS)
and mechanical (E, nu, rho, cut resistance) parameters -- so an arbitrary cut is relightable and
the object responds to contact the way the real one does.

**What would falsify it** (write these down before running anything):
- F1. The material inventory the data supports is 1 (i.e. the interior is one substance). Then
      the field reduces to a constant and there is no paper. *Partly tested already: no.*
- F2. A homogeneous field reproduces the measured cut-force profile as well as ours. Then
      heterogeneity buys nothing. **This is the main falsifier for the mechanical branch.**
- F3. Baked RGB, relit naively, matches held-out lighting as well as our fitted SVBRDF+SSS.
      Then the optical branch buys nothing.

---

## 0b. Positioning: the exact gap, verified 2026-09-04

Material granularity of the closest work. Checked against each paper, because the paper's novelty
claim rests on this table and a reviewer will check it too.

| method | granularity | how the interior gets its material |
|---|---|---|
| PhysX-Anything (CVPR 2026) | per part, exported as URDF / XML | no interior field; a part is uniform |
| PhysX-Omni (2026) | per part, part-level voxel grids | same |
| VoMP (2025), AdaVoMP (ICML 2026) | per voxel, but annotated per part | "we treat each part as having isotropic material"; limitations: "we assume part-level materials are isotropic, which is not a true assumption for some common materials like wood", and "fixed-grid voxelization ... causing oversmoothing in highly heterogeneous regions" |
| Pixie (2025), UniPixie (2026) | per voxel, 64^3 | labels come from CLIP-driven segmentation of *surface* semantics; the interior inherits its part's label. UniPixie lists "estimating properties for occluded regions" as future work |
| Phys4DGen (ACM MM 2025) | per particle | rays are cast along the six principal axes and "the most frequently observed material group" from the intersected *surface* particles is assigned to the internal particle |
| GaussianFluent (CVPR 2026) | per Gaussian | the only one with within-part heterogeneity, and it is **manual**: "we assign beta values based on the color of the gs" (watermelon rind 2 / flesh 0.6 / seed 5, E = 2000 / 1000 / 10^4 Pa). Its limitations: "the current physical parameters are manually set; automating this process through inverse rendering or learning-based approaches would significantly reduce tuning efforts" |

**The claim, stated so it survives checking.** Two layers are unoccupied, and only these two:

1. *Within-part heterogeneity.* To every method above, an orange is one part: peel, albedo,
   flesh, columella and seeds share one material. We do not claim voxel-level material fields are
   new -- VoMP, AdaVoMP and Pixie output them -- we claim that nothing inside a part varies in
   any of them.
2. *Supervision from interior observation.* Every method above derives material from the outside:
   surface semantics, a VLM's reading of a photograph, or rays cast inward from the surface. Ours
   is the only supervision that has seen the inside.

**Do not claim:** that per-voxel material prediction is new, that we predict absolute moduli, or
that our inputs are unposed. Each of those is checkable and false.

**The obvious review attack, pre-empted: "just segment more parts."** Part-aware generators
(PartCrafter, OmniPart) decompose an object into *separable* components -- a drawer, a handle, a
leg -- from the outside. Peel, albedo, flesh, columella and seeds are concentric layers and
inclusions of one connected solid, invisible from the outside, and no part segmenter produces
them because nothing in the exterior image indicates them. Finer part decomposition does not
reach this; only an observation of the inside does.

**The invitation.** GaussianFluent's limitation section asks for exactly this work, on exactly
the watermelon, and its manual per-colour assignment is the natural strongest baseline in E5.

---

## 0c. The head-to-head: GaussianFluent (CVPR 2026)

Checked 2026-09-04. Three facts decide how the comparison must be built.

1. **No code is released.** The GitHub repo is the project page only. So the baseline is a faithful
   re-implementation of their material rule on *our* geometry and *our* solver. That is the
   cleaner experiment anyway: the only thing that differs is the material field.
2. **They have no cutting experiment.** Slicing appears in a list of capabilities; there is no
   knife model, no cutting section and no cutting metric. Their evaluation is CLIP score and a
   user study. So we are not beating them on their benchmark -- **we introduce the evaluation
   they do not have**, and their rule is the baseline in it.
3. **Their mixed-material claim rests on one object.** Table A1 gives beta 2 / 0.6 / 5 and
   E = 2000 / 1000 / 1e4 Pa for the watermelon; jelly and pumpkin are single-material. The rule is
   one sentence: "we assign beta values based on the color of the gs".

### Where we can actually win, and where we cannot

Their rule is *colour thresholds chosen by hand*. It succeeds exactly when colour separates the
substances and fails when it does not. We already know both cases on our own objects:

| object | does colour separate the substances? | expected outcome |
|---|---|---|
| watermelon | yes -- seeds are the one class colour finds (`discrete-inclusions.md`), rind green, flesh red | **tie.** Report it as a tie. |
| orange | **no** -- LAB merges the peel and the columella, both pale (measured 2026-09-04, longitudinal figure, LAB row) | **win.** The two have opposite mechanics: tough fibrous peel, soft spongy core. Colour assignment gives them one material. |
| loaf | the cinnamon swirl **is** found by colour (darkest-centre standoff 4.64, `discrete-inclusions.md`); crust vs crumb is a texture difference, not a colour one | win on crust/crumb only; do not claim the swirl |
| apple, cake, doughnut | to be measured (E1b) | unknown |

**The money figure.** A transverse cut through an orange, force vs blade displacement:

    ours          spike (peel) -- plateau (flesh) -- dip (columella) -- plateau -- spike
    colour rule   spike        -- plateau         -- SPIKE (wrong)   -- plateau -- spike
    homogeneous   flat
    measured      the arbiter

The columella is the discriminator: it is pale like the peel, so a colour rule stiffens it, and
the force trace says whether that is right. This is a single measured curve that separates three
methods, and it needs one afternoon with the load cell.

**Say the honest version first.** Against GaussianFluent our claim is not capability -- a human
picking colour thresholds can also produce a heterogeneous field. It is: automatic, from cut
photographs, on six objects, with one program and no per-object tuning, and correct where colour
and material disagree. Put that sentence in the paper before a reviewer writes it.

---

## 1. Constraints already measured (do not re-derive)

From `notes/discrete-inclusions.md` and the DINOv2 clustering run of 2026-09-04:

| finding | consequence for the plan |
|---|---|
| LAB colour K-sweep rises monotonically on orange/melon/loaf; no knee | colour alone cannot select K |
| Watermelon seeds are the only discrete class colour finds (1.7% of pixels); loaf's cinnamon swirl found by the darkest-centre-standoff test | discrete inclusions are sparse and object-specific |
| DINOv2 BIC has a minimum at K=4 where LAB has none; DINOv2 separates columella from peel (both pale) consistently on held-out fruit; LAB merges them | semantic features are required, and they fix a specific known failure |
| DINOv2 patch stride 14 at 512 px = 26 patches across the fruit; albedo layer and segment membranes are sub-patch; interior labels are blocky noise | **feature upsampling is mandatory**, see 2.1 |
| GMM fit on 3 spl photographs: held-out log-likelihood collapses (-76 at K=2 to -276 at K=7) while held-out radial MI stays 0.41 | **labels transfer, densities do not**: fuse posteriors, never raw likelihoods, see 2.2 |
| Seeds are ~1 cell thick at the current lattice; model holds 66% singleton pieces vs photographs' 26% | inclusions need a sub-cell representation or a finer lattice |
| A seed's volume fraction is ~0.5%, the photographs' area fraction reads 3.11% | never set a volume quota from 2D area |
| Cylindrical A[r,phi,z]: radial membranes become axis-parallel stripes | keep the cylinder; it is what makes patch priors work |

---

## 2. Algorithm

**Input is the 3DFusion asset itself**: the cylindrical grid `A[r, phi, z]` with a colour per cell,
the shell and core masks, and the object axis. The lifting from 2D to 3D is already done upstream;
this paper decomposes a volume that is consistent by construction. The original cut photographs
enter only in Stage 3, as the ground truth for the optical fit.

### 2.1 Stage 1 -- virtual slicing and cellular back-projection

**Virtual slices.** Render the volume unlit (its colour is already baked from photographs) along
both cut families: N_t transverse slices scanning z, N_l longitudinal slices rotating about the
axis. The asset is a volume, so N is unbounded and oblique slices are free -- this is what removes
the "an interior cannot be re-photographed" limitation of working on photographs directly.

**Feature stack per slice**, each block standardised within the slice:
1. semantic: DINOv2-base at effective stride 4 (4x4 shifted crops, interleaved);
2. colour: LAB plus local mean and std at three scales;
3. texture: structure-tensor coherence and Gabor energy at three scales, four orientations.

Feature resolution should match the lattice, not exceed it: the volume carries no information
finer than its cells, and stride 4 at 512 px is ~128 samples across, which is the lattice.

**Back-projection.** A cell c = (r, phi, z) is intersected by several slices S_c. Its descriptor is

    f(c) = ( sum_{s in S_c} w_s(c) f_s(pi_s(c)) ) / sum_s w_s(c),   F(c) = [ f(c), r, |z| ]

with pi_s the orthographic projection of the cell centre into slice s. **Weighting is by
sampling density, not by any "slice normal"** -- a cell has no normal. In a cylindrical grid the
longitudinal slices converge at the axis: a cell near r = 0 is hit by all N_l of them and a cell
at the rim by about one, so a uniform average over-smooths the axis. Set w_s(c) proportional to
1 / (number of slices of that family through the cell's radial shell), so both families
contribute equally at every radius.

Cost: (N_t + N_l) slices x 16 DINOv2 passes; at 64 + 64 slices that is ~2000 ViT-B passes at
518 px, a few minutes on one GPU.

### 2.2 Stage 2 -- volumetric decomposition into a mixed field

**Clustering.** Full-covariance GMM on F(c) over the core cells, soft posteriors kept.

**Choosing K -- not by BIC on the volume.** BIC's penalty is O(log n); on ~10^6 cells it is
swamped by likelihood gains and K drifts upward monotonically. The K = 4 knee measured on
2026-09-04 was on ~10^4 pixels of photographs, not on a volume. Use a stability criterion
instead: fit on the features of half the slices (alternating), score held-out likelihood and
label agreement (Hungarian) on the other half, and take the largest K that is stable. Report the
inventory per object as a result.

**Anisotropic MRF -- the sign matters.** Alpha-expansion on the lattice with pairwise cost
w_ij [l_i != l_j]. The pairwise cost is the price of a label *change* between neighbours.
Tissue is layered radially, so a change along r is expected and must be **cheap**; within a
layer the substance is constant tangentially, so a change along phi or z is unexpected and must
be **expensive**:

    w_r  << w_phi ~ w_z

(The earlier draft had this inverted; inverted, the MRF fights exactly the radial boundaries we
want.) Thin tangentially-varying structures -- segment membranes, seeds -- would be erased by a
high w_phi, so they do not go through the MRF at all; they are handled as discrete inclusions
below.

**Mixed discrete-continuous field.**

    material(c) = ( k(c), t(c) )

- *Discrete inclusions* (peel, columella, seeds, swirl): connected components of their class,
  each fitted with an ellipsoid (centre, axes, orientation) so that a seed one cell thick keeps a
  shape below lattice resolution. Piece-size statistics against the photographs are the metric
  (target: median piece 5-7 cells, singleton fraction near the photographs' 26%).
- *Continuous modulation* within the dominant tissue class: t(c) in [0, 1] is the first
  principal component of F(c) within the class, normalised. Not the Mahalanobis distance, which
  measures typicality rather than a monotone axis. **t has no physical calibration**; in the
  paper it is an appearance modulation that drives the optical interpolation, and it is set
  to zero in every mechanical validation (see 2.4).

### 2.3 Stage 3 -- optical branch, fitted on the photographs, not on the volume

**Per-class parameters:** { rho_d, alpha, F0, sigma_s, sigma_a, g }_k. One set per substance.

**Why the fit cannot be pixel-wise against the rendered volume.** The generated interior and the
photograph come from different individuals; a slice of the volume at the photograph's plane does
not match it pixel for pixel, and a pixel loss between them is meaningless. So the volume is
never rendered during the optical fit.

**Fit on the photographs with a planar proxy.** Geometry = a flat cut face; per-pixel class =
the photograph's own material mask (Stage 1 features run on the photograph, labels assigned
with the volume's class centres). Illumination = known where possible: fit on the *new*
captures, where flash on / off gives a known point light plus ambient, and treat the original
uncontrolled photographs as evaluation only. Render in Mitsuba 3, Adam on the per-class
parameters, loss on pixels within each class. Because the unknowns are per class, highlights
that vary within a class are absorbed by the shading model rather than baked into rho_d.

**Anchoring.** Backlit thin slices give sigma_t,k = sigma_s + sigma_a per class directly from
exp(-sigma_t d) with d the slice thickness; fit the albedo split second. Absolute values
sanity-checked against Jensen et al. 2001.

**Transfer.** The fitted per-class parameters are attached to the volume by k(c), interpolated
by t(c) within the tissue class. That is the only place the volume and the photographs meet.

### 2.4 Stage 4 -- mechanics and cutting, with the circularity removed

Hexahedral elements one per cell; MPM per cell as in `report/dynamic_cut.py`.

**Two models, and they are separate -- say so.** E_k, nu_k, rho_k enter the solver and govern
deformation and fragment dynamics; they are validated by the compression test (E6). Cut
resistance is an independent empirical model that never goes through the solver:

    F_cut(s) = sum_{c in front(s)} tau_{k(c)} dl_c        (beta = 0 in all validation)

A reviewer will ask what E and nu do during a cut; the answer is "nothing, and the paper says
so". Moduli come from published measurements per class and are stated as assumed.

**Removing the circularity in tau.** If tau_k is fitted to the measured profile the match is by
construction. Protocol: fit tau_k on one cut path and *predict* another -- transverse to
longitudinal, centred to off-centre, and orange A to orange B. What is falsifiable is the shape
of the profile given the spatial layout k(c), never the absolute level. The peel-flesh-columella
-flesh-peel double spike with a dip is the shape a homogeneous field cannot produce and a
colour-assigned field gets wrong at the columella.

**Timing.** Do not quote "8-16 ms per cut"; the existing measurement is 272.5 ms per cut for
labelling (`report/fig_cut.png`). Re-measure in E7 and report what is measured.

## 3. Data to capture

Objects: the existing six (orange, watermelon, doughnut, loaf, apple, cake). Per object:

| capture | how | why |
|---|---|---|
| cut faces, 3 lighting conditions | phone, flash off / flash on / lamp at 45 deg, colour checker in frame | held-out lighting is the optical evaluation |
| cut faces, held-out cuts | oblique 45 deg and off-centre planes | the existing split discipline, extended |
| backlit thin slices | slice on a lightbox, 2-3 thicknesses | sigma_t ground truth |
| cut-force profiles | load cell rig, 5 repeats x 3 cut paths | falsifier F2 |
| compression curves | load cell, 2 plates | elasticity sanity |
| hand-annotated material masks | 6 held-out photographs per object, ~1 h | Stage 1 accuracy has a real number |

Everything is a weekend of kitchen work plus one afternoon of annotation. No lab.

---

## 4. Experiment plan

Each experiment names what it decides. Ordered so the cheapest falsifier comes first.

**E0. Feature-resolution fix.** Re-run the 2026-09-04 clustering with the stride-4 DINOv2 stack
and per-photograph whitening. *Decides:* whether Stage 1 can separate anything beyond peel and
columella. Metric: held-out radial purity and Hungarian label agreement against the current
0.658 / -. Half a day. **If the interior classes are still blocky noise, Stage 1 falls back to
"peel + columella + one flesh class" and the paper's clustering contribution shrinks to a
component, which is survivable.**

**E1. Material inventory per object.** K selection by BIC knee plus transfer, all six objects,
one program, no per-object knobs (repo rule). *Decides:* the inventory table in 2.1. Output is a
table and six figures. Two days.

**E1b. Colour-separability audit -- run this in week 1.** For each object, fit a colour-only
classifier (the GaussianFluent rule, and LAB K-means) to the hand-annotated material classes and
report the per-class confusion. *Decides:* exactly which objects the head-to-head can be won on,
and therefore whether the paper's comparison has content at all. **If colour separates every
class on all six objects, the delta against GaussianFluent collapses to "we automated a manual
step" and the paper must be repositioned -- and we need to know that in week 1, not month 5.**
Prediction from the 2026-09-04 run: peel/columella confusion on the orange, crust/crumb confusion
on the loaf, watermelon clean. Half a day once the annotations exist.

**E2. Annotated accuracy.** mIoU of Stage 1 against the hand-annotated held-out masks, against
baselines: LAB K-means (the note's method), colour+radius rule (`report/material_field.py`),
SAM2 automatic masks, raw DINOv2. *Decides:* whether the feature stack is worth its complexity.
Ablations: drop semantic / drop texture / drop radius / drop whitening. Three days.

**E3. Lifting quality.** PoE + MRF on the cylinder. *Decides:* whether the 3D field is coherent.
Metrics: cross-family disagreement at plane intersections (x3d measured 0.012 for colour --
this is the comparable number), label continuity across an unsupervised 45 deg oblique cut,
inclusion piece-size statistics vs photographs (target: median piece 5-7 cells, singleton
fraction near the photographs' 26%, from a current 1 cell and 66%). One week.

**E4. Optical fitting.** Per-class SVBRDF + SSS by differentiable rendering. *Decides:*
falsifier F3. Metric: re-rendering PSNR / LPIPS on the held-out lighting condition, and
transmission error on the backlit slices. Baselines: baked RGB as albedo (FruitNinja and our
own O-Voxel paper), constant material tuned globally, per-pixel SVBRDF without the class
constraint, off-the-shelf estimator applied per cut render with no 3D field (expect flicker
between cuts -- that is the ablation figure). Two weeks.

**E5. Cut-force validation.** *Decides:* falsifier F2, the mechanical branch's only real claim.
tau_k is fitted on one cut path and predicted on another (see 2.4); never report a curve fitted
and evaluated on the same cut.
Metric: force-profile MAE and the presence of the peel spikes. Baselines, all on the same lattice, same solver, same cut, differing only in the material field:
(a) homogeneous at the best-fit single stiffness (PhysGaussian); (b) **the GaussianFluent rule
re-implemented** -- colour thresholds picked by hand per object, their watermelon values as the
anchor; (c) our rule-based `material_field.py`; (d) an **oracle** field from the hand annotations,
which upper-bounds what any material assignment can achieve and separates "the field is wrong"
from "the solver is wrong". Two weeks including capture.

**E6. Deformation validation.** Compression curve vs simulation, same baselines. One week.

**E7. Interactive cutting demo.** Real-time cut through the heterogeneous field with force
feedback, piece enumeration by connected components, one solver per piece (all existing).
*Decides:* the systems claim. Metric: ms per cut (current baseline 272.5 ms labelling, re-measured), fps, piece-count correctness. One week.

**E8. Generality.** Every experiment on all six objects, one program, no per-object tuning.
Report per-object numbers, including the failures. This is the repo's standing rule and it is
also the strongest defence against "tuned on the orange".

**E9. Head-to-head against part-level predictors.** The comparison is not "who predicts a better
number" -- PhysX-Anything, VoMP and Pixie cannot express within-part heterogeneity at all, so the
experiment must show that the part-level assumption *fails*, not that it is less accurate.
Protocol: run each on the same six objects, take their material assignment, put it through the
same MPM cut and compression, and overlay the measured force profiles. Prediction: a part-level
field cannot produce the peel entry/exit spikes at any single stiffness, because it has one
stiffness. Also report the trivially strong baseline that GaussianFluent uses -- per-colour
manual assignment -- which *can* produce the spikes, and against which our claim is
"automatically, from photographs, on six objects, with one program". One week.

---

## 5. Contribution list (what the paper claims, in order of defensibility)

1. A material field on the interior recovered from a handful of cut photographs, mixed
   discrete-continuous, lifted by posterior product on a cylindrical lattice. *Evidence: E1-E3.*
2. Relightable cuts: per-class SVBRDF and subsurface scattering, so an arbitrary cut face
   responds to light. No prior interior method has any material at all. *Evidence: E4.*
3. Within-part heterogeneity, which no existing method expresses, validated against measured
   cut forces rather than assumed. *Evidence: E5, E6, E9.*
4. A simulation-ready pipeline: the same lattice is the render target and the FEM/MPM element
   set; cutting is connected components; force feedback is an integral over the blade.
   *Evidence: E7.*

**Stated honestly in the paper:** absolute moduli come from published measurements per material
class, not from the network. What is predicted is *which substance is where*; what is validated
is the *behaviour* that follows.

---

## 6. Timeline (6 months)

| month | work |
|---|---|
| 1 | E0, E1, E2. Capture rig built. Annotation done. |
| 2 | E3. Lifting, MRF, sub-cell inclusions. |
| 3 | E4. Optical fitting, differentiable rendering, backlit calibration. |
| 4 | E5, E6. Force capture and validation. |
| 5 | E7, E9. Demo and head-to-head. E9 includes one week to set up GaussianFluent's released code and assets (22 3DGS assets, 32 configs) and run its watermelon with its own solver. |
| 6 | E8 sweep over all objects, ablations, writing. |

---

## 7. Risks and mitigations

| risk | mitigation |
|---|---|
| Stage 1 finds only 2-3 classes (likely) | frame the inventory as a finding; the pipeline is unchanged, the claim shrinks honestly |
| Off-the-shelf material estimators fail on cut tissue | that failure is E4's first figure; the per-class fit does not depend on them beyond initialisation |
| Cut-force rig too noisy | five repeats, report the spread; the peel spike is a large effect and does not need precision |
| "You assumed the moduli" | pre-empted in the contribution list; E5 validates behaviour, not parameters |
| "This is MaterialMVP for the inside" | the defence is the information asymmetry: an interior cannot be re-photographed, every cut destroys the object, photographs come from different individuals, and consistency must hold across intersecting planes rather than across camera views |
| Cylindrical prior needs an axis | the loaf has none and is the one object outside the assumption; report it as such, do not tune around it |
| Inclusions one cell thick | ellipsoid representation below lattice resolution; state the limit |
| Upstream quality | the field inherits 3DFusion's artefacts (held-out DreamSim 0.087); stated as the dependency that makes the pipeline a bridge, not a fault |
| Scope too large | E4 and E5 are the two load-bearing experiments; if month 4 slips, ship the optical branch with the mechanical branch as a demo |

## 8. Abstract wording rules (from the 2026-09-04 review)

- say "where colour and material disagree", never "naive colour-based heuristics" -- the
  baseline is a CVPR 2026 paper and its authors may review;
- say "cut resistance", never "fracture resistance" -- we do not model fracture, GaussianFluent does;
- say "cut photographs under multiple illuminations", never "multi-view" -- SVBRDF fitting needs
  lighting variation, not viewpoint variation;
- say "six objects", never "six diverse objects" -- they are all food; generality is a limitation;
- say "uncalibrated, family-labelled", never "unposed".

## 9. Venue

Optical + mechanical + interactive cutting is a graphics paper: SIGGRAPH Asia, EGSR, Pacific
Graphics, TVCG. CVPR is possible if the material-field recovery is foregrounded and the
simulation is the application, but the appearance-modelling reviewers are at the graphics
venues.

## 10. Stage 2 is now learned: NMFS (2026-09-04)

The GMM + mean-field MRF of 2.2 is kept as the baseline. The method is a neural material-field
segmenter on the cylinder (`Fruit3D_Fusion/material/nmfs.py`): per-cell MLP with positional encoding,
one head per cut family on that family's back-projected features, a fused head, thin periodic 3D-conv
context, and an inclusion head. Trained with no 3D labels: cross-entropy on confident pseudo-labels from
the photograph classifier (itself verified on held-out oranges at 0.93), symmetric KL between the two
family heads, the anisotropic gradient penalty of 2.2 as a loss (inclusion cells exempt), focal loss for
thin fibrous structures. The differentiable-rendering and force terms are NOT training losses (2.3, 2.4).

Orange, versus GMM+MRF: cross-family disagreement 0.187 -> 0.001; agreement with the classifier on
non-confident cells 0.67 -> 0.84; fibre outside the core 0.078 -> 0.123 (membranes kept; classifier 0.122);
oblique-slice change rate 0.052 vs transverse 0.069 (no seam). 265 s on one GPU.
Report the 0.001 as consistency, not accuracy -- the two heads share the class layer and are pulled
together by the KL term. Dropped claims: zero-shot to new objects, speed over GMM.

## 11. Stage 4, simulation side, first numbers (2026-09-04)

Cut-force profile shapes on the Cartesian export (relative tau: peel 1.0, fibrous 0.5, flesh 0.15;
`Fruit3D_Fusion/material/stage4_cutforce.py`): NMFS and GMM+MRF give entry/exit spikes (0.98 / 0.85 of
max) over a low flesh plateau (0.70 / 0.59); the homogeneous field is the chord-length arch (spike 0.60,
centre/plateau 1.05). **The colour rule, automated as K-means on voxel colour, does not find the peel at
all on the orange -- skin and flesh are both orange -- so its curve has no entry/exit spike and is
essentially the homogeneous arch.** That is the discriminator: colour assignment fails where skin and
flesh share a colour, which is the case for the orange and not for the watermelon. The centre feature's
sign (bump vs dip at the columella) depends on tau_fibre vs tau_flesh and is left to the load cell.

MPM cutting with the field (`report/dynamic_cut.py`, MATERIAL=classes): the fruit range maps peel to
E=8e6 Pa, whose CFL margin at dt=3e-4 is 1.29x -> Warp illegal-memory-access crashes. Run at DT=1.5e-4,
SUBSTEPS=60 (margin 2.6x). Behavioural metric from the trace: squash of skin vs interior per piece along
gravity; heterogeneous fields should give interior/skin < 1, uniform ~ 1 (`report/mat_runs/compare_runs.py`).

Cutting runs (2026-09-04, DT=1.5e-4, SUBSTEPS=60, three cuts -> 6 pieces, 130 frames, all three fields,
0 CUDA errors): NMFS pieces make far fewer contacts than uniform (mean over the last 40 frames 6.4k vs
16.1k; colour rule 12.5k) -- the stiff shell keeps pieces from spreading and overlapping. The per-piece
squash metric is confounded by rigid tumbling after the cuts (interior/skin > 1 for all three); the clean
version is the intact drop (`CUT_SPEC=999:...`), which is the E6 analogue and is run separately.

Intact drop (2026-09-04, 90 frames, no cut): NMFS field vs uniform. Minimum extent along gravity /
rest -- skin 0.955 vs 0.944, interior 0.979 vs 0.958; interior/skin at impact 1.036 vs 1.008. With the
stiff peel the whole body deforms less and the interior is shielded (deforms half as much as under the
uniform material). The effect is percent-level because the drop is gentle and the shell is 1-3 cells
thick; this is the simulated analogue of E6, and the load-cell compression test is what gives it a
real number to match. Sign convention to state in the paper: under floor impact the shell takes the
contact, so interior/skin > 1 for a hard-shell object; the earlier comment in dynamic_cut.py assumed the
opposite loading.

## 12. Decision 2026-09-04: no load cell. Evidence moves to optics and structure.

The user dropped the physical force / compression measurements. Consequences, so the claims stay
inside what is measured:

- **E5 / E6 are demonstrations, not validation.** Cut-force profile shape, fragment contact count
  (16,113 -> 6,438), and the drop test show that heterogeneity changes macroscopic behaviour. The
  paper says "physically plausible, simulation-ready", never "mechanically validated".
- **E4 becomes the primary quantitative claim**, in its valid form only: the SAME real cut face
  photographed under diffuse light and under flash; per-class SVBRDF + SSS fitted on the diffuse
  photo, the flash photo predicted; LPIPS / PSNR against baked RGB and a homogeneous material.
  Pixel-wise comparison of an asset render against a photograph of a *different* orange is NOT a
  valid metric (different individual) and is not used; distribution-level DreamSim stays upstream's.
- **New E2b, structural statistics on an unsupervised real oblique cut.** One 45-degree cut
  photograph per object, never used in generation or in NMFS. 2D classifier -> class area
  fractions; asset oblique slice -> cell class fractions; KL / Wasserstein between them. Plus
  morphology: membrane count and spacing for the orange (9-12 segments), seed size / aspect for the
  watermelon. **This also arbitrates the GaussianFluent comparison without force data**: the real
  oblique photo has ~15-20% peel, the colour rule assigns ~0% peel on the orange, NMFS is near the
  photo.
- **Cross-family consistency and anisotropic TV are diagnostics**, reported only next to an
  external reference (agreement with the held-out-verified classifier on non-confident cells,
  0.84). A constant field scores perfectly on them alone.

Capture needed (one afternoon, phone only): per object one oblique cut photograph; per cut face
one diffuse and one flash photograph. Stage 3 (Mitsuba fit) is ~2 weeks and was already planned.
