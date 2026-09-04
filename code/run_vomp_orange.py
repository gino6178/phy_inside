"""Run VoMP (ICLR 2026, nv-tlabs) on the orange Gaussian splat and compare its per-splat material field with ours.
usage: run_vomp_orange.py ASSET.ply OUR_LABELS.pt GRID.pt OUT_DIR   (run inside the `vomp` env, from the VoMP repo root)"""
import sys, os, json, time, numpy as np, torch
PLY, LAB, GRID, OUT = sys.argv[1:5]; os.makedirs(OUT, exist_ok=True); t0 = time.time()
from vomp.inference import Vomp
cfg = 'weights/inference.json' if os.path.exists('weights/inference.json') else 'configs/materials/inference.json'
model = Vomp.from_checkpoint(config_path=cfg, use_trt=False)
print('model loaded', f'{time.time()-t0:.0f}s', flush=True)
hdr = b''
with open(PLY, 'rb') as f:
    while b'end_header' not in hdr: hdr += f.readline()
n_rest = hdr.count(b'f_rest_'); sh_degree = int(round(((n_rest + 3) / 3) ** 0.5 - 1)); print('PLY f_rest', n_rest, '-> sh_degree', sh_degree, flush=True)
res = model.get_splat_materials(PLY, query_points='splat_centers', output_dir=OUT, sh_degree=sh_degree, num_views=int(os.environ.get('NV', 60)), voxel_level=int(os.environ.get('VL', 5)), dino_batch_size=int(os.environ.get('DBS', 1)))
E = np.asarray(res['youngs_modulus']).reshape(-1); nu = np.asarray(res.get('poisson_ratio', np.zeros_like(E))).reshape(-1); rho = np.asarray(res.get('density', np.zeros_like(E))).reshape(-1)
np.savez_compressed(os.path.join(OUT, 'vomp_orange.npz'), E=E, nu=nu, rho=rho, keys=np.array(list(res.keys())))
print('VoMP done', f'{time.time()-t0:.0f}s', 'n', len(E), 'E: min %.3g median %.3g max %.3g  unique %d' % (E.min(), np.median(E), E.max(), len(np.unique(np.round(E, -3)))), flush=True)
# ---- compare with our per-cell labels (same PLY order)
lab = torch.load(LAB, map_location='cpu').numpy().astype(int); n = min(len(lab), len(E)); lab, Ev = lab[:n], E[:n]
names = {0: 'fibrous', 1: 'flesh', 2: 'peel'}; out = {'n': int(n), 'E_global': dict(min=float(Ev.min()), median=float(np.median(Ev)), max=float(Ev.max()), cv=float(Ev.std() / Ev.mean()))}
for k, nm in names.items():
    m = lab == k; out[f'E_{nm}'] = dict(n=int(m.sum()), median=float(np.median(Ev[m])), p10=float(np.percentile(Ev[m], 10)), p90=float(np.percentile(Ev[m], 90)))
# variance of VoMP's log E explained by our three classes
lE = np.log10(np.clip(Ev, 1, None)); tot = lE.var(); within = sum(lE[lab == k].var() * (lab == k).mean() for k in names); out['logE_variance_explained_by_our_classes'] = float(1 - within / max(tot, 1e-12))
out['peel_over_flesh_median_ratio'] = float(np.median(Ev[lab == 2]) / max(np.median(Ev[lab == 1]), 1e-9))
print(json.dumps(out, indent=1)); json.dump(out, open(os.path.join(OUT, 'vomp_vs_ours.json'), 'w'), indent=1)
