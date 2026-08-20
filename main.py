"""微信跳一跳 PC 端自动辅助 —— 主程序。

用法：
    python main.py              # 全自动连续跳
    python main.py --once       # 只跳一步（调参时用）
    python main.py --config my_config.json

前置条件：
    1. PC 微信打开「跳一跳」小程序，窗口可见、不要最小化；
    2. 已进入游戏对局（棋子站在方块上）；
    3. 运行期间不要遮挡游戏窗口，鼠标甩到屏幕左上角可紧急停止。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import cv2
import pyautogui

from jump import control, vision, winutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_image(img, path: str) -> bool:
    """cv2.imwrite 在 Windows 下写不了含中文的路径（静默失败），
    改用 imencode + tofile。"""
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        return False
    buf.tofile(path)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="微信跳一跳 PC 端自动辅助")
    parser.add_argument("--config", default=os.path.join(BASE_DIR, "config.json"))
    parser.add_argument("--once", action="store_true", help="只跳一步")
    parser.add_argument("--snap", action="store_true",
                        help="只截一帧并保存识别标记图，不跳（诊断用）")
    args = parser.parse_args()

    cfg = load_config(args.config)
    winutil.set_dpi_aware()

    print("[*] 正在定位游戏窗口……")
    region = winutil.locate_game_region(cfg["window_title_keywords"],
                                        cfg["title_bar_height"])
    if region is None:
        print("[!] 找不到游戏窗口。请确认 PC 微信已打开跳一跳小程序，"
              "或修改 config.json 的 window_title_keywords。")
        return 1
    print(f"[*] 游戏区域: left={region.left} top={region.top} "
          f"{region.width}x{region.height}")

    debug_dir = os.path.join(BASE_DIR, cfg.get("debug_dir", "debug"))
    if cfg.get("debug_save_screenshots"):
        os.makedirs(debug_dir, exist_ok=True)

    capturer = vision.ScreenCapturer()
    fails = 0
    jumps = 0

    print("[*] 3 秒后开始，请切换到游戏窗口……（Ctrl+C 停止）")
    time.sleep(3)

    while True:
        cfg = load_config(args.config)  # 每跳前重读配置，边跑边调不重启
        region = winutil.locate_game_region(cfg["window_title_keywords"],
                                            cfg["title_bar_height"]) or region
        frame = capturer.grab_bgr(region)
        res = vision.detect(frame, cfg)

        if res is None:
            fails += 1
            print(f"[!] 识别失败（连续 {fails} 次）")
            if fails >= cfg.get("fail_retry_limit", 8):
                print("[*] 连续识别失败，可能已游戏结束。共跳跃 "
                      f"{jumps} 步。")
                break
            time.sleep(0.8)
            continue
        fails = 0

        if cfg.get("debug_save_screenshots"):
            path = os.path.join(debug_dir, f"jump_{jumps:04d}.png")
            if not save_image(vision.annotate(frame, res), path):
                print(f"[!] 调试图保存失败: {path}")

        if args.snap:
            print(f"[*] 已保存标记图到 {debug_dir}\\jump_{jumps:04d}.png，"
                  "未执行跳跃。")
            break

        angles = cfg.get("jump_axis_angles_deg")
        dist = res.axis_distance(angles) if angles else res.distance
        duration = control.jump(region, dist, cfg)
        jumps += 1
        print(f"[+] 第 {jumps} 跳: 轴向距离 {dist:.1f}px"
              f"（欧氏 {res.distance:.1f}）→ 按压 {duration:.0f}ms")

        if args.once:
            break
        if jumps >= cfg.get("max_score_stop", 10 ** 9):
            print(f"[*] 达到设定的 {jumps} 步上限，主动停止（防封）。")
            break
        control.wait_after_jump(cfg)

    print("[*] 结束。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[*] 用户停止。")
    except pyautogui.FailSafeException:  # noqa: F821
        print("\n[*] 触发了 FailSafe（鼠标在左上角），紧急停止。")
