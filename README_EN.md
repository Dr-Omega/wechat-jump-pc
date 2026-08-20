# WeChat Jump-Jump PC Auto Player

[中文](README.md) | English

An auto-player for the WeChat "Jump-Jump" (跳一跳) mini-game on PC WeChat.
It captures the mini-program window, detects the piece and the target block
with OpenCV/numpy, converts pixel distance into press duration, and simulates
a long mouse press to jump automatically.

## Project Structure

| File / Directory | Purpose |
|---|---|
| `main.py` | Entry point: locate window → capture → detect → compute press duration → simulate long press, in a loop |
| `jump/vision.py` | Core vision: head-ball anchored piece detection; per-row width tracking with a plateau stop-growth (dw8) rule to find the target top-face center; isometric axis-projection distance |
| `jump/control.py` | Mouse control: millisecond-precision long-press, randomized press point and duration jitter (anti-detection) |
| `jump/winutil.py` | Window utilities: DPI awareness, find window by title keywords, client-area cropping |
| `config.json` | All tunables (coefficient, axis angles, color ranges, thresholds); reloaded before every jump — edit while running |
| `test_offline.py` | Offline regression test against frozen samples in `samples/` |
| `samples/` | 13 real in-game screenshots (varied backgrounds and block shapes: boxes, round tables, cylinders, cubes, tall platforms) |
| `debug/` | Per-jump annotated screenshots generated at runtime for troubleshooting (git-ignored) |

## Requirements

- Windows 10/11 + PC WeChat (the mini-program panel can run Jump-Jump directly)
- Python 3.9+

```bash
pip install -r requirements.txt
```

## Usage

1. Open Jump-Jump in PC WeChat and enter a game (piece standing on a block);
   keep the window visible.
2. Run:

   ```bash
   python main.py          # jump continuously, Ctrl+C to stop
   python main.py --once   # single jump, for tuning
   ```

Move the mouse to the top-left screen corner to emergency-stop
(pyautogui FailSafe). If landings are systematically long/short, tweak
`press_coefficient` in `config.json` (smaller if long, larger if short,
in ±0.02 steps).

## Configuration (config.json)

| Field | Meaning |
|---|---|
| `window_title_keywords` | Game window title keywords, matched in order |
| `title_bar_height` | Title bar height in pixels, used to crop the client area |
| `press_coefficient` | **Core parameter**: pixel distance → press milliseconds |
| `jump_axis_angles_deg` | Isometric axis angles `[30, 150]`: jump distance is the max projection of the displacement onto the two axes instead of the Euclidean length (delete to fall back to Euclidean) |
| `press_point` | Fixed press point `[x, y]`; randomized in the lower window half when `null` |
| `under_game_score_ratio` | Score-area height ratio (skipped when scanning for blocks) |
| `piece_color` | Piece color RGB ranges; adjust if detection is off |
| `bg_diff_threshold` | Color-difference threshold between blocks and background |
| `press_noise_ratio` | Random jitter ratio on press duration (anti-detection) |
| `jump_wait_seconds` | Wait interval for the animation after each jump |
| `max_score_stop` | Jump-count limit; stops proactively (anti-ban) |
| `debug_save_screenshots` | Save per-jump annotated images to `debug/` |

## How It Works

- **Piece**: anchored by its head ball (the most regular shape, never
  polluted by the base) — color mask → column clustering → vertical
  splitting → neck detection in the width profile; foot = bottom of the
  head+body chain.
- **Target block**: background gradient model → vertex scan → per-row
  width tracking with surge/shrink fuses → center row picked by a
  plateau stop-growth rule (dw8 ≤ 3 over 8 rows), robust for both
  box tops (diamond) and round tables (ellipse).
- **Distance**: displacement projected onto the two isometric axes
  (30°/150°), max projection is used as the jump distance.

## FAQ

- **Off clicks / wrong capture coordinates**: DPI awareness is built in;
  with 125%/150% Windows scaling, launch via `python main.py` directly.
- **Window not found**: adjust `window_title_keywords`.
- **Long/short jumps**: tune `press_coefficient` in ±0.02 steps.
- **Detection failures**: check the annotated images in `debug/`, adjust
  `piece_color` and `bg_diff_threshold`.
- **Anti-detection**: randomized press point and duration jitter are
  built in; keep `max_score_stop` ≤ 1000 to be safe.

## References

- Algorithm inspiration: [wangshub/wechat_jump_game](https://github.com/wangshub/wechat_jump_game)
- PC-side references: [B5DX/pc_wechat_jump_auto](https://github.com/B5DX/pc_wechat_jump_auto),
  [XDDXMT/AutoJump](https://github.com/XDDXMT/AutoJump)

## License

MIT
