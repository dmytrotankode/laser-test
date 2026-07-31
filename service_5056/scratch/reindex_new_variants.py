import re
import os
import shutil
import numpy as np
from icp_reindex_new_variants import load_pts_full, trim_whiskers, euler_zyx
from icp_reindex_v2 import icp_hungarian as icp

BASE = "input"
TO_FIX = ['v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13']  # v13 reindexed too, for correct held-out validation (not training)


def parse_blocks(path):
    """Return list of (index, full_block_text, x, y, z) in file order."""
    content = open(path, 'r', encoding='utf-8', errors='ignore').read()
    block_pattern = re.compile(r'P\[(\d+)\]\{.*?\};', re.DOTALL)
    xyz_pattern = re.compile(r'X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+).*?Z\s*=\s*([-\d.]+)', re.DOTALL)
    blocks = []
    for m in block_pattern.finditer(content):
        idx = int(m.group(1))
        text = m.group(0)
        xm = xyz_pattern.search(text)
        x, y, z = float(xm.group(1)), float(xm.group(2)), float(xm.group(3))
        blocks.append((idx, text, x, y, z))
    header_end = content.find(f"P[{blocks[0][0]}]")
    header = content[:header_end]
    footer = content[content.rfind("};") + 2:]
    return header, blocks, footer


def whisker_split(blocks):
    coords = np.array([[b[2], b[3], b[4]] for b in blocks])
    seg = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    normal_med = np.median(seg[len(seg)//4: 3*len(seg)//4])
    threshold = normal_med * 3.0
    lo = 0
    while lo < len(seg) and seg[lo] > threshold:
        lo += 1
    hi = len(blocks) - 1
    while hi > 0 and seg[hi - 1] > threshold:
        hi -= 1
    return blocks[:lo], blocks[lo:hi + 1], blocks[hi + 1:]


def renumber(header, blocks, footer, out_path):
    parts = [header]
    for new_idx, (old_idx, text, x, y, z) in enumerate(blocks, start=1):
        new_text = re.sub(r'^P\[\d+\]', f'P[{new_idx}]', text, count=1)
        parts.append(new_text)
        parts.append('\n')
    parts.append(footer)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(''.join(parts))


if __name__ == "__main__":
    cad_header, cad_blocks, cad_footer = parse_blocks(f"{BASE}/ls_file/TORXL_NEW_PROG.LS")
    _, cad_loop, _ = whisker_split(cad_blocks)
    cad_xyz = np.array([[b[2], b[3], b[4]] for b in cad_loop])
    print(f"CAD loop: {len(cad_loop)} points")

    for v in TO_FIX:
        path = f"{BASE}/archive/{v}/ground_truth.ls"
        backup_path = f"{BASE}/archive/{v}/ground_truth_original.ls"
        if not os.path.exists(backup_path):
            shutil.copy2(path, backup_path)
            print(f"{v}: backed up original -> {backup_path}")
        else:
            print(f"{v}: backup already exists, re-reading from backup (idempotent)")
            path = backup_path

        header, blocks, footer = parse_blocks(path)
        approach, loop, retreat = whisker_split(blocks)
        xyz = np.array([[b[2], b[3], b[4]] for b in loop])
        print(f"{v}: approach={len(approach)} loop={len(loop)} retreat={len(retreat)}")

        best = None
        for yaw_guess in range(0, 360, 3):
            th = np.radians(yaw_guess)
            init_rot = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
            rot, trans, corr, err = icp(cad_xyz, xyz, init_rot=init_rot)
            if best is None or err < best[3]:
                best = (rot, trans, corr, err)
        rot, trans, corr, err = best
        yaw, pitch, roll = euler_zyx(rot)
        print(f"{v}: ICP err={err:.2f}mm yaw={yaw:.2f} pitch={pitch:.2f} roll={roll:.2f}")

        # Reorder loop blocks to match CAD's canonical index order via nearest-point correspondence.
        # corr[k] = index into `loop` (target) that is nearest to CAD's k-th loop point.
        used = set()
        reordered_loop = []
        for k in range(len(cad_loop)):
            j = corr[k]
            reordered_loop.append(loop[j])
            used.add(j)
        dropped = [i for i in range(len(loop)) if i not in used]
        print(f"{v}: reordered {len(reordered_loop)}/{len(cad_loop)} loop points, dropped target indices {dropped} (extra/unmatched)")

        new_blocks = approach + reordered_loop + retreat
        out_path = f"{BASE}/archive/{v}/ground_truth.ls"
        renumber(header, new_blocks, footer, out_path)
        print(f"{v}: wrote reindexed ground_truth.ls ({len(new_blocks)} points)\n")
