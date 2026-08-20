"""鼠标按压模拟：长按时长决定跳跃距离。

防检测设计：
- 按压点在游戏窗口下半部随机选取（不要每次按同一个像素点）；
- 按压时长叠加 ±noise 的高斯抖动，模拟人手误差。
"""

from __future__ import annotations

import random
import time

import pyautogui

pyautogui.FAILSAFE = True   # 鼠标甩到左上角可紧急停止
pyautogui.PAUSE = 0.01


def press_and_hold(x: int, y: int, duration_ms: float) -> None:
    """在屏幕物理坐标 (x, y) 处按下，按住 duration_ms 毫秒后松开。"""
    pyautogui.moveTo(x, y, duration=0.05)
    pyautogui.mouseDown()
    _precise_sleep(duration_ms / 1000.0)
    pyautogui.mouseUp()


def _precise_sleep(seconds: float) -> None:
    """毫秒级延时：先普通 sleep，末尾自旋校准，降低系统调度抖动。"""
    if seconds <= 0:
        return
    end = time.perf_counter() + seconds
    if seconds > 0.02:
        time.sleep(seconds - 0.015)
    while time.perf_counter() < end:
        pass


def random_press_point(region, fixed: tuple[int, int] | None = None):
    """按压点：优先用配置固定点，否则在游戏区下半部随机取点。"""
    if fixed:
        return fixed
    x = random.randint(int(region.left + region.width * 0.3),
                       int(region.left + region.width * 0.7))
    y = random.randint(int(region.top + region.height * 0.6),
                       int(region.top + region.height * 0.8))
    return x, y


def jump(region, distance_px: float, cfg: dict) -> float:
    """执行一次跳跃，返回实际按压毫秒数。"""
    duration = distance_px * cfg["press_coefficient"]
    noise = duration * cfg.get("press_noise_ratio", 0.0)
    duration += random.gauss(0, noise)
    duration = max(80.0, duration)  # 下限，避免误触成单击

    fixed = tuple(cfg["press_point"]) if cfg.get("press_point") else None
    x, y = random_press_point(region, fixed)
    press_and_hold(x, y, duration)
    return duration


def wait_after_jump(cfg: dict) -> None:
    """等待跳跃动画 + 相机滚动结束再截下一帧。"""
    lo, hi = cfg.get("jump_wait_seconds", [1.8, 2.6])
    time.sleep(random.uniform(lo, hi))
