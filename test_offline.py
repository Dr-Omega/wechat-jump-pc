"""离线回归测试：用 samples/ 里冻结的真实截图验证识别算法。

自动抹掉图上的标注像素（纯红/绿/蓝/黄）后跑 detect，
与人工核对的期望值对比。新增样本：把目测无误的 debug 图复制到
samples/ 并在 EXPECTED 里登记期望值即可。

用法： python test_offline.py
"""

from __future__ import annotations

import json
import os
import sys
import types

# 托管 Python 没有 mss/cv2，打桩后导入（本测试不截屏、不画图）
sys.modules.setdefault("mss", types.SimpleNamespace(mss=lambda: None))

import numpy as np
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from jump import vision  # noqa: E402

# 每张图人工核对的期望值 (piece, board)；board 为顶面几何中心。
# 期望值 = 识别结果经逐张目视核对确认无误后回填。
# 样本固定在 samples/（debug/ 每局会被新运行覆盖，不能直接用作回归）。
# 样本覆盖：粉/米/绿/灰/蓝背景，方盒、圆桌、魔方、条纹盒、高台。
# 已排除：跳跃途中帧、结算页、排行榜页（非有效游戏画面）
EXPECTED = {
    "jump_0000.png": ((206, 900), (603, 656)),   # 粉背景，圆柱（环形图案顶面）
    # 浅紫背景，深色圆桌：椭圆顶面慢速区曾误触发平台导致中心偏上
    # 19px（641），修为平台确立加 dw8 停涨判据
    "jump_0006.png": ((240, 881), (609, 651)),
    "jump_0007.png": ((482, 830), (329, 722)),   # 粉背景，白色条纹方盒
    "jump_0022.png": ((292, 868), (558, 657)),   # 绿背景，深色圆桌
    "jump_0029.png": ((467, 857), (305, 713)),   # 绿背景，紫色方盒
    "jump_0034.png": ((358, 837), (510, 719)),   # 米背景，魔方（顶面多色块）
    "jump_0037.png": ((481, 815), (354, 704)),   # 米背景，深色圆桌近距
    # 米背景，白顶灰条高盒：平台爬升曾把 argmax 拖到正面（773），
    # 修为平台起始行 691
    "jump_0041.png": ((303, 865), (547, 691)),
    "jump_0045.png": ((400, 848), (528, 727)),   # 浅灰背景，棋子遮挡白盒
    "jump_0046.png": ((289, 849), (550, 661)),   # 浅灰背景，白色圆桌
    # 浅灰背景 + 深灰高台：阴影过滤曾误杀顶面，修为阈值 0.65
    "jump_0048.png": ((283, 857), (554, 687)),
    # 蓝紫背景 + 深棕大理石盒：盒底角残渣曾把 piece_y 拉低 ~130px，
    # 修为列段垂直断行切分取本体
    "jump_0049.png": ((271, 865), (566, 680)),
    # 浅紫背景：阴影+盒子描边连成 771px 垃圾列段骗过"最高段"规则，
    # 棋子站在白盒右角（部分被挡）；修为头部小球锚定
    "jump_0011.png": ((705, 734), (537, 685)),
}

TOLERANCE = 45  # px，人工核对本身有误差


def erase_annotations(img: np.ndarray) -> np.ndarray:
    """把标注纯色像素替换为该行非标注像素的中位色，避免干扰识别。"""
    img = img.astype(np.int16)
    ann = np.zeros(img.shape[:2], dtype=bool)
    for c in ([255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]):
        ann |= np.abs(img - c).sum(axis=2) < 90
    out = img.copy()
    for y in range(img.shape[0]):
        row_ann = ann[y]
        if not row_ann.any():
            continue
        clean = img[y][~row_ann]
        if len(clean) > 0:
            out[y][row_ann] = np.median(clean, axis=0)
    return out.astype(np.uint8)


def main() -> int:
    cfg = json.load(open(os.path.join(BASE_DIR, "config.json"),
                         encoding="utf-8"))
    debug_dir = os.path.join(BASE_DIR, "samples")
    passed = failed = 0

    for name, (exp_piece, exp_board) in sorted(EXPECTED.items()):
        path = os.path.join(debug_dir, name)
        if not os.path.exists(path):
            print(f"[跳过] {name} 不存在")
            continue
        img = np.asarray(Image.open(path).convert("RGB"))
        bgr = erase_annotations(img)[:, :, ::-1].copy()
        res = vision.detect(bgr, cfg)
        if res is None:
            print(f"[✗] {name}: 识别失败")
            failed += 1
            continue
        dp = ((res.piece_x - exp_piece[0]) ** 2
              + (res.piece_y - exp_piece[1]) ** 2) ** 0.5
        db = ((res.board_x - exp_board[0]) ** 2
              + (res.board_y - exp_board[1]) ** 2) ** 0.5
        ok = dp <= TOLERANCE and db <= TOLERANCE
        mark = "✓" if ok else "✗"
        print(f"[{mark}] {name}: "
              f"棋子=({res.piece_x},{res.piece_y}) 偏差{dp:.0f}px | "
              f"方块=({res.board_x},{res.board_y}) 偏差{db:.0f}px | "
              f"dist={res.distance:.0f}")
        passed += ok
        failed += not ok

    print(f"\n结果: {passed} 通过 / {failed} 失败")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
