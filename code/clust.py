"""Does an orange's cross-section have discrete material classes?
Colour (LAB) was already measured in notes/discrete-inclusions.md and said no.
This repeats it with DINOv2 patch features, which is the proposal's premise.

Three tests, because a K-sweep separation number cannot tell a gradient sliced finer
from real classes (the repo's own note says so):
  1. BIC knee of a GMM  -- a real class structure gives a knee, a gradient does not.
  2. transfer to held-out photographs of *other* oranges -- real materials transfer.
  3. radial sharpness   -- on a transverse cut, real materials are radial bands with
     sharp transitions; a gradient gives a label that drifts smoothly with radius.
"""
import os, sys, glob, json, numpy as np, cv2, torch
from sklearn.mixture import GaussianMixture

ROOT = '/home/gino/project/FruitNinja_clean/cfsd/slicefill/split'
DEV = 'cuda'

def load(split):
    out = []
    for f in sorted(glob.glob(f'{ROOT}/{split}/*.png')):
        im = cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2RGB)
        out.append((os.path.basename(f)[:-4], im))
    return out

def fg_mask(im):
    """the cut face: everything that is not the white background."""
    g = im.astype(np.float32).mean(2)
    m = (g < 245) & (im.astype(np.float32).std(2) > 4)
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1: m = (lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    return m.astype(bool)

@torch.no_grad()
def dino_feats(ims, model, proc):
    """-> list of (H/14, W/14, C) patch-token grids"""
    out = []
    for im in ims:
        inp = proc(images=im, return_tensors='pt').to(DEV)
        o = model(**inp).last_hidden_state[0, 1:]          # drop CLS
        s = int(np.sqrt(o.shape[0]))
        out.append(o.reshape(s, s, -1).float().cpu().numpy())
    return out

def lab_feats(ims):
    return [cv2.cvtColor(im, cv2.COLOR_RGB2LAB).astype(np.float32) for im in ims]

def gather(feats, masks, stride=1):
    X, idx = [], []
    for i, (f, m) in enumerate(zip(feats, masks)):
        mm = cv2.resize(m.astype(np.uint8), (f.shape[1], f.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
        ys, xs = np.nonzero(mm)
        X.append(f[ys, xs]); idx.append(np.stack([np.full(len(ys), i), ys, xs], 1))
    return np.concatenate(X), np.concatenate(idx)

def radial_sharpness(labels, idx, shapes, K):
    """on transverse cuts: how much of the label variation is explained by radius,
    and how sharp are the transitions. Returns (MI/H, mean transition width in radius units)."""
    r_all, l_all = [], []
    for i, sh in enumerate(shapes):
        s = idx[:, 0] == i
        if not s.any(): continue
        ys, xs = idx[s, 1].astype(float), idx[s, 2].astype(float)
        cy, cx = ys.mean(), xs.mean()
        r = np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2); r /= r.max()
        r_all.append(r); l_all.append(labels[s])
    r = np.concatenate(r_all); l = np.concatenate(l_all)
    bins = np.linspace(0, 1, 21); b = np.clip(np.digitize(r, bins) - 1, 0, 19)
    P = np.zeros((20, K))
    for k in range(K): P[:, k] = np.bincount(b[l == k], minlength=20)
    P = P / P.sum(1, keepdims=True).clip(1)
    pk = np.bincount(l, minlength=K) / len(l)
    H = -(pk * np.log(pk + 1e-9)).sum()
    Hc = -(P * np.log(P + 1e-9)).sum(1)
    w = np.bincount(b, minlength=20).astype(float); w /= w.sum()
    MI = H - (w * Hc).sum()
    purity = (P.max(1) * w).sum()          # how deterministic is label|radius
    return float(MI / H), float(purity)

def run(name, feats_spl, feats_hld, masks_spl, masks_hld, Ks=(2, 3, 4, 5, 6, 7, 8)):
    Xs, Is = gather(feats_spl, masks_spl); Xh, Ih = gather(feats_hld, masks_hld)
    mu, sd = Xs.mean(0), Xs.std(0) + 1e-6
    Xs = (Xs - mu) / sd; Xh = (Xh - mu) / sd
    if Xs.shape[1] > 32:                                   # PCA for DINO
        from sklearn.decomposition import PCA
        p = PCA(32, random_state=0).fit(Xs[np.random.default_rng(0).choice(len(Xs), min(20000, len(Xs)), replace=False)])
        Xs, Xh = p.transform(Xs), p.transform(Xh)
    rows = []
    for K in Ks:
        g = GaussianMixture(K, covariance_type='full', random_state=0, n_init=3, reg_covar=1e-4).fit(Xs)
        ls, lh = g.predict(Xs), g.predict(Xh)
        mi_s, pur_s = radial_sharpness(ls, Is, [f.shape for f in feats_spl], K)
        mi_h, pur_h = radial_sharpness(lh, Ih, [f.shape for f in feats_hld], K)
        rows.append(dict(K=K, bic=float(g.bic(Xs)), ll_spl=float(g.score(Xs)), ll_hld=float(g.score(Xh)),
                         radial_mi_spl=mi_s, radial_purity_spl=pur_s, radial_mi_hld=mi_h, radial_purity_hld=pur_h))
        print(f'{name} K={K}  BIC {g.bic(Xs):12.0f}  loglik spl {g.score(Xs):7.3f} hld {g.score(Xh):7.3f}  '
              f'radial MI/H spl {mi_s:.3f} hld {mi_h:.3f}  purity spl {pur_s:.3f} hld {pur_h:.3f}', flush=True)
    return rows

if __name__ == '__main__':
    fam = sys.argv[1] if len(sys.argv) > 1 else 'trans'
    spl, hld = load(f'spl_{fam}'), load(f'hld_{fam}')
    ims_s, ims_h = [x[1] for x in spl], [x[1] for x in hld]
    ms, mh = [fg_mask(i) for i in ims_s], [fg_mask(i) for i in ims_h]
    print('foreground fraction', [round(float(m.mean()), 3) for m in ms + mh])
    res = {}
    res['lab'] = run('LAB   ', lab_feats(ims_s), lab_feats(ims_h), ms, mh)
    from transformers import AutoImageProcessor, AutoModel
    proc = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
    model = AutoModel.from_pretrained('facebook/dinov2-base').to(DEV).eval()
    res['dino'] = run('DINOv2', dino_feats(ims_s, model, proc), dino_feats(ims_h, model, proc), ms, mh)
    json.dump(res, open(f'res_{fam}.json', 'w'), indent=1)
