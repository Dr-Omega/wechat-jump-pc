# 微信跳一跳 PC 端自动辅助

[English](README_EN.md) | 中文

通过截取 PC 微信「跳一跳」小程序窗口画面，OpenCV 识别棋子与目标方块，
计算像素距离换算按压时长，模拟鼠标长按完成自动跳跃。

## 项目结构

| 文件 / 目录 | 用途 |
|---|---|
| `main.py` | 主程序：定位窗口 → 截屏 → 识别 → 换算按压时长 → 模拟鼠标长按，循环跳跃 |
| `jump/vision.py` | 核心识别：头部小球锚定棋子位置；逐行段宽跟踪 + 平台停涨点（dw8 判据）定目标顶面中心；等距轴向投影距离计算 |
| `jump/control.py` | 鼠标控制：毫秒级精度的长按模拟，按压点随机化 + 时长抖动（防检测） |
| `jump/winutil.py` | 窗口工具：DPI 感知、按标题关键字找窗口、裁剪客户区坐标 |
| `config.json` | 全部可调参数（系数、轴向角、颜色范围、阈值等），运行中每跳重读、改完即生效 |
| `test_offline.py` | 离线回归测试：用 `samples/` 冻结样本验证识别算法不回归 |
| `samples/` | 13 张真实对局截图（覆盖粉/米/绿/灰/蓝背景，方盒/圆桌/圆柱/魔方/高台等形状） |
| `debug/` | 运行时生成的每跳标注图（棋子红圈、目标绿圈），排查识别问题用，不入库 |

## 环境

- Windows 10/11 + PC 微信（小程序面板可直接玩跳一跳）
- Python 3.9+

```bash
pip install -r requirements.txt
```

## 使用

1. PC 微信打开跳一跳小程序，进入对局（棋子站在方块上），窗口保持可见。
2. 运行：

   ```bash
   python main.py          # 连续跳，Ctrl+C 停止
   python main.py --once   # 只跳一步，调参时用
   ```

运行中把鼠标甩到屏幕左上角可紧急停止（pyautogui FailSafe）。
若落点系统性偏远/偏近，直接改 `config.json` 里的 `press_coefficient`
（偏远调小、偏近调大，每次 ±0.02 微调）。

## 配置说明（config.json）

| 字段 | 含义 |
|---|---|
| `window_title_keywords` | 游戏窗口标题关键字，按顺序匹配 |
| `title_bar_height` | 窗口标题栏像素高度，用于裁剪客户区 |
| `press_coefficient` | **核心参数**：像素距离 → 按压毫秒 的系数 |
| `jump_axis_angles_deg` | 等距轴向角度 `[30, 150]`：跳跃距离取位移在两轴上投影的最大值而非欧氏连线长（删掉该行则回退为欧氏距离） |
| `press_point` | 固定按压点 `[x, y]`；为 `null` 时在窗口下半部随机取点 |
| `under_game_score_ratio` | 分数区域高度占画面比例（扫描方块时跳过） |
| `piece_color` | 棋子颜色 RGB 范围，识别不准时调整 |
| `bg_diff_threshold` | 方块与背景色差阈值 |
| `press_noise_ratio` | 按压时长随机抖动比例（防检测） |
| `jump_wait_seconds` | 每跳后等待动画的时间区间 |
| `max_score_stop` | 跳跃步数上限，达到后主动停止（防封） |
| `debug_save_screenshots` | 是否保存每跳标记图到 `debug/` |

## 常见问题

- **点击位置偏 / 截图坐标不对**：确认程序已调用 DPI 感知（`main.py` 已内置）；
  若 Windows 缩放为 125%/150%，务必通过 `python main.py` 启动而不是其他宿主。
- **找不到窗口**：`跳一跳` 窗口标题可能不同，改 `window_title_keywords`。
- **跳远/跳近**：微调 `config.json` 的 `press_coefficient`（偏远调小、
  偏近调大，每次 ±0.02）；近距离普遍偏远的话需要分段系数（后续增强项）。
- **识别失败**：看 `debug/` 里的标记图，调 `piece_color` 和
  `bg_diff_threshold`。
- **防检测**：程序已内置按压点随机化和时长抖动；分数不要刷太高，
  `max_score_stop` 建议 ≤ 1000。

## 参考

- 算法思路：[wangshub/wechat_jump_game](https://github.com/wangshub/wechat_jump_game)
- PC 端参考：[B5DX/pc_wechat_jump_auto](https://github.com/B5DX/pc_wechat_jump_auto)、
  [XDDXMT/AutoJump](https://github.com/XDDXMT/AutoJump)
