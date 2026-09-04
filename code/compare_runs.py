"""Compare the three cutting runs: per-piece squash of skin vs interior over time (from trace.json),
piece counts, and gifs.  Squash = extent along gravity / rest extent; a stiff shell around a soft
interior keeps its own extent (ratio near 1) and lets the interior lose more."""
import json, glob, os, numpy as np, imageio.v2 as iio, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = os.path.dirname(os.path.abspath(__file__)); runs = [r for r in ('nmfs', 'uniform', 'colour') if os.path.exists(f'{R}/{r}/trace.json')]
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2)); summary = {}
for r in runs:
    tr = json.load(open(f'{R}/{r}/trace.json')); f = np.array([t[0] for t in tr]); npc = np.array([t[1] for t in tr])
    skin, inter = [], []
    for t in tr:
        sq = np.array(t[3], float)
        if len(sq) == 0: skin.append(np.nan); inter.append(np.nan); continue
        skin.append(np.nanmean(sq[0::2])); inter.append(np.nanmean(sq[1::2]))          # [skin, interior] per body
    skin, inter = np.array(skin), np.array(inter)
    ax[0].plot(f, skin, label=f'{r}: skin', lw=2); ax[0].plot(f, inter, '--', label=f'{r}: interior', lw=2)
    ax[1].plot(f, inter / skin, label=r, lw=2)
    last = slice(len(f) - 20, len(f)); summary[r] = dict(pieces_final=int(npc[-1]), skin_squash_last20=float(np.nanmean(skin[last])), interior_squash_last20=float(np.nanmean(inter[last])), interior_over_skin=float(np.nanmean(inter[last]) / np.nanmean(skin[last])))
    frames = sorted(glob.glob(f'{R}/{r}/d_*.png')); iio.mimsave(f'{R}/{r}_cut.gif', [iio.imread(p) for p in frames[::2]], duration=0.08, loop=0)
ax[0].set_xlabel('frame'); ax[0].set_ylabel('extent along gravity / rest'); ax[0].set_title('squash per level (mean over pieces)'); ax[0].legend(fontsize=7); ax[0].grid(alpha=.3)
ax[1].set_xlabel('frame'); ax[1].set_ylabel('interior squash / skin squash'); ax[1].set_title('< 1 : interior deforms more than the shell'); ax[1].axhline(1, c='k', lw=.8); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
plt.tight_layout(); plt.savefig(f'{R}/squash_compare.png', dpi=120); json.dump(summary, open(f'{R}/squash_summary.json', 'w'), indent=1); print(json.dumps(summary, indent=1))
