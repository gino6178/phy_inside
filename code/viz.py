import os, sys, glob, numpy as np, cv2, torch, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, '.')
from clust import load, fg_mask, lab_feats, dino_feats, gather, ROOT, DEV
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA

K = int(sys.argv[2]) if len(sys.argv) > 2 else 4
fam = sys.argv[1]
spl, hld = load(f'spl_{fam}'), load(f'hld_{fam}')
names = [n for n, _ in spl] + [n for n, _ in hld]
ims = [i for _, i in spl] + [i for _, i in hld]
masks = [fg_mask(i) for i in ims]
n_spl = len(spl)

from transformers import AutoImageProcessor, AutoModel
proc = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
model = AutoModel.from_pretrained('facebook/dinov2-base').to(DEV).eval()

def fit_apply(feats, tag):
    """fit the GMM on the supervision photos only, apply to all."""
    Xs, Is = gather(feats[:n_spl], masks[:n_spl])
    mu, sd = Xs.mean(0), Xs.std(0) + 1e-6
    Z = (Xs - mu) / sd; p = None
    if Z.shape[1] > 32:
        p = PCA(32, random_state=0).fit(Z[np.random.default_rng(0).choice(len(Z), min(20000, len(Z)), replace=False)]); Z = p.transform(Z)
    g = GaussianMixture(K, covariance_type='full', random_state=0, n_init=3, reg_covar=1e-4).fit(Z)
    # order clusters by mean radius so colours mean the same thing across methods
    order = {}
    lab = g.predict(Z)
    for i in range(n_spl):
        s = Is[:, 0] == i
        ys, xs = Is[s, 1].astype(float), Is[s, 2].astype(float); cy, cx = ys.mean(), xs.mean()
        r = np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2) / max(1e-6, np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2).max())
        for k in range(K): order.setdefault(k, []).append(r[lab[s] == k].mean() if (lab[s] == k).any() else np.nan)
    rank = np.argsort([np.nanmean(order[k]) for k in range(K)]); remap = np.zeros(K, int); remap[rank] = np.arange(K)
    outs = []
    for f, m in zip(feats, masks):
        mm = cv2.resize(m.astype(np.uint8), (f.shape[1], f.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
        ys, xs = np.nonzero(mm); X = (f[ys, xs] - mu) / sd
        if p is not None: X = p.transform(X)
        L = np.full(f.shape[:2], -1, int); L[ys, xs] = remap[g.predict(X)]
        outs.append(cv2.resize(L.astype(np.int16), (512, 512), interpolation=cv2.INTER_NEAREST))
    return outs

L_lab = fit_apply(lab_feats(ims), 'LAB')
L_dino = fit_apply(dino_feats(ims, model, proc), 'DINOv2')
cmap = np.array([[0, 0, 0], [230, 90, 40], [250, 220, 120], [220, 60, 140], [60, 140, 230], [90, 200, 120], [150, 100, 220], [120, 120, 120]], np.uint8)
def paint(L): 
    o = cmap[np.clip(L + 1, 0, len(cmap) - 1)]; o[L < 0] = 255; return o
fig, ax = plt.subplots(3, len(ims), figsize=(2.1 * len(ims), 6.6))
for j in range(len(ims)):
    ax[0, j].imshow(ims[j]); ax[0, j].set_title(('spl ' if j < n_spl else 'held-out ') + names[j].replace('or_', ''), fontsize=8)
    ax[1, j].imshow(paint(L_lab[j])); ax[2, j].imshow(paint(L_dino[j]))
    for i in range(3): ax[i, j].axis('off')
ax[1, 0].set_ylabel('LAB'); ax[2, 0].set_ylabel('DINOv2')
for i, t in enumerate(['photograph', f'LAB colour, K={K}', f'DINOv2, K={K}']):
    ax[i, 0].axis('on'); ax[i, 0].set_xticks([]); ax[i, 0].set_yticks([]); ax[i, 0].set_ylabel(t, fontsize=9)
plt.suptitle(f'orange {fam} sections: GMM fit on the 3 supervision photographs, applied to 3 held-out oranges', fontsize=10)
plt.tight_layout(); plt.savefig(f'clusters_{fam}_K{K}.png', dpi=130); print('saved', f'clusters_{fam}_K{K}.png')
