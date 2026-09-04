"""Attach the predicted material field to the 3DFusion lattice asset, per cell.
Writes (1) <out>.ply : the asset with three extra float properties per cell -- mat_label (0 fibrous,
1 flesh, 2 peel), mat_E (Pa), mat_t (continuous modulation in [0,1]) -- so any reader that keeps
unknown properties carries the field with the cells; (2) <out>_material.pt : the same field as
tensors aligned with the PLY order, which is what the cutting pipeline reads (MATERIAL_LABELS);
(3) <out>_matview.ply : the same asset with f_dc replaced by a class colour, for a 'material view'
render under the same physics.
usage: attach_material.py ASSET.ply GRID.pt FIELDS_CARTESIAN.pt NMFS_CELLS.npz CELL_LEVEL.pt OUT_PREFIX [category]"""
import sys, numpy as np, torch
PLY, GRID, FIELDS, CELLS, LEVEL, OUT = sys.argv[1:7]; CAT = sys.argv[7] if len(sys.argv) > 7 else 'fruit'
C0 = 0.28209479177387814
E_RANGE = {'fruit': (2.0e5, 8.0e6), 'bread': (1.0e5, 3.0e6), 'generic': (2.0e5, 5.0e6)}[CAT]
CLASS_R = {0: 0.68, 1: 0.0, 2: 1.0}                        # relative stiffness per class, as material_from_labels derives for the orange
CLASS_RGB = {0: (60, 140, 230), 1: (230, 90, 40), 2: (250, 220, 120)}
f = open(PLY, 'rb'); hdr = b''
while b'end_header' not in hdr: hdr += f.readline()
lines = hdr.split(b'\n'); names = [l.split()[-1].decode() for l in lines if l.startswith(b'property')]
n = int([l for l in lines if l.startswith(b'element vertex')][0].split()[-1])
a = np.frombuffer(f.read(n * len(names) * 4), dtype='<f4').reshape(n, len(names)).copy()
xyz = torch.from_numpy(a[:, [names.index(k) for k in ('x', 'y', 'z')]])
g = torch.load(GRID, map_location='cpu'); N = g['N']; ctr = g['ctr']; ext = g['ext']
L = torch.load(FIELDS, map_location='cpu')['NMFS'].long()
ii = (((xyz - ctr) / ext + 0.5) * (N - 1)).round().long().clamp(0, N - 1)
lab = L[ii[:, 0], ii[:, 1], ii[:, 2]]; lab[lab < 0] = 1
lvl = torch.load(LEVEL, map_location='cpu').reshape(-1)[:n].long(); lab[lvl == 1] = 2
# t from the NMFS cells (cylinder) -> nearest Cartesian voxel via the same mapping used for labels
d = np.load(CELLS); t_cells = torch.zeros(n)
import math
NR, NPHI, NZ = [int(x) for x in d['shape']]; idx = torch.from_numpy(d['idx'].astype(np.int64))
tgrid = torch.zeros(NR, NPHI, NZ); tv = torch.from_numpy(d['P'].astype(np.float32))[:, 1] if 't' not in d else torch.from_numpy(d['t'].astype(np.float32))
tgrid[idx[:, 0], idx[:, 1], idx[:, 2]] = tv
# cylinder coordinates in GRID-INDEX units, exactly as planes.Vol builds them (EXT = max radial / axial
# extent of the occupied voxels over 0.82; polar axis = grid dim 1)
fi = ((xyz - ctr) / ext + 0.5) * (N - 1); c = (N - 1) / 2; AXD = 1; rest = [k for k in range(3) if k != AXD]
occ = g['OCC'][0] > 0.5; oi = torch.nonzero(occ).float() - c
EXT = max(float(torch.sqrt(oi[:, rest[0]] ** 2 + oi[:, rest[1]] ** 2).max()), float(oi[:, AXD].abs().max())) / 0.82
u = fi - c; rad = torch.sqrt(u[:, rest[0]] ** 2 + u[:, rest[1]] ** 2); ang = torch.atan2(u[:, rest[1]], u[:, rest[0]]) % (2 * math.pi)
ri = (rad / EXT * NR - 0.5).round().long().clamp(0, NR - 1); pi_ = (ang / (2 * math.pi) * NPHI).round().long() % NPHI; zi = ((u[:, AXD] / EXT + 1) / 2 * NZ - 0.5).round().long().clamp(0, NZ - 1)
t = tgrid[ri, pi_, zi].clamp(0, 1)
E = torch.tensor([E_RANGE[0] + CLASS_R[int(k)] * (E_RANGE[1] - E_RANGE[0]) for k in lab.tolist()])
# (1) PLY with extra properties
new_names = names + ['mat_label', 'mat_E', 'mat_t']
b = np.concatenate([a, lab.float().numpy()[:, None], E.numpy()[:, None].astype('<f4'), t.numpy()[:, None]], 1).astype('<f4')
hdr2 = b'\n'.join([l for l in lines if not l.startswith(b'end_header') and l != b''] + [b'property float mat_label', b'property float mat_E', b'property float mat_t', b'end_header', b''])
open(OUT + '.ply', 'wb').write(hdr2 + b.tobytes())
# (2) companion tensors (labels in PLY order; the cutting pipeline masks with is_interior itself)
torch.save({'labels': lab.to(torch.uint8), 'E': E, 't': t, 'classes': {0: 'fibrous core/membranes', 1: 'flesh', 2: 'peel'}}, OUT + '_material.pt')
torch.save(lab.to(torch.uint8), OUT + '_labels.pt')
# (3) material-view PLY: same geometry, class colours
c = a.copy(); cols = [names.index(f'f_dc_{i}') for i in range(3)]
rgb = np.array([CLASS_RGB[int(k)] for k in lab.tolist()], np.float32) / 255
for i in range(3): c[:, cols[i]] = (rgb[:, i] - 0.5) / C0
open(OUT + '_matview.ply', 'wb').write(hdr + c.astype('<f4').tobytes())
print(f'{n:,} cells: labels', torch.bincount(lab, minlength=3).tolist(), 'E range', float(E.min()), float(E.max()), 'wrote', OUT + '.ply / _material.pt / _labels.pt / _matview.ply')
