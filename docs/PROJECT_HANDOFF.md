# 项目交接总结

## 初衷

目标不是完全复活 4.46 旧版微软天气客户端，而是保留 4.53 早期版本可运行、API 相对可用的底层，同时把用户能看到的视觉部分尽量恢复成 4.46：

- 旧版应用图标和磁贴图标。
- 旧版动态磁贴三列小时预报样式。
- 旧版蓝色天气背景。
- 磁贴底部城市名，例如“南山区”。

## 已尝试过的路线

1. 直接修改 4.46 的 API。
   - 旧版依赖 `service.weather.microsoft.com` 等历史接口。
   - 搜索和天气接口基本不可用，应用容易卡在启动界面。
   - 这条路线暂时放弃。

2. 把 4.53 的 API 配置移植到 4.46。
   - 4.53 使用较新的 MSN/OneService 天气接口。
   - 4.46 客户端内部结构太旧，直接替换配置后仍不稳定。
   - 这条路线不作为当前主线。

3. 以 4.53 为底包，替换视觉资源。
   - 应用能打开。
   - 但远程动态磁贴仍可能显示新版图标、灰底或错误布局。
   - 因此继续加入本地动态磁贴服务。

4. 当前主线：4.53 底包 + 本地动态磁贴服务 + 4.46 资源。
   - AppX 内的动态磁贴 URL 指向 `http://127.0.0.1:8765`。
   - 本地服务调用 Open-Meteo 数据。
   - 本地服务输出 Windows 磁贴 XML。
   - 本地服务同时提供 4.46 小图标和背景图。

## 当前核心文件

- `dist/OpenMeteo.BingWeather453LocalTile_4.53.41681.0_x64.appx`
  - 当前推荐安装的修改版 4.53 AppX。
  - 包名为 `OpenMeteo.BingWeather453LocalTile`。
  - 发布者改为本地测试证书，避免伪装微软签名。

- `dist/OpenMeteo.BingWeather453Visual.Local.cer`
  - 用于安装 AppX 的本地测试证书。

- `adapter/OpenMeteoAdapter/openmeteo_msn_adapter.py`
  - 本地适配器主程序。
  - 监听 `http://127.0.0.1:8765`。
  - 处理天气、搜索、动态磁贴、徽章、图标和背景请求。

- `adapter/OpenMeteoAdapter/WeatherIcons/30x30`
  - 从 4.46 中提取的旧版小天气图标。

- `adapter/OpenMeteoAdapter/WeatherImages/210x173`
  - 4.46 中等磁贴背景。

- `adapter/OpenMeteoAdapter/WeatherImages/423x173`
  - 4.46 宽磁贴背景。

- `scripts/Install-BingWeather453LocalTile.ps1`
  - 安装证书、安装 AppX、启用 loopback、注册开机启动任务、启动本地服务。

## 动态磁贴当前实现

本地服务的 `tile_xml()` 会输出如下内容：

- `TileMedium`、`TileWide`、`TileLarge` 三种 binding。
- 每个 binding 先放一张 4.46 天气背景图作为 `placement="background"`。
- 主体为三列小时预报：
  - 时间，例如 `00:00`。
  - 4.46 `30x30` 天气图标。
  - 温度，例如 `27°`。
- 底部放城市名。

图标映射由 `OLD_TILE_ICON_BY_ICON` 控制，背景映射由 `OLD_TILE_BACKGROUND_BY_ICON` 控制。

## 当前已知问题

- Windows 开始菜单可能缓存旧磁贴。安装新版本后建议取消固定再重新固定。
- 本地服务必须运行，否则动态磁贴可能空白或回落为静态磁贴。
- Open-Meteo 搜索结果和微软原版地名格式不完全一样，后续可以继续优化中文地名。
- 当前 AppX 是已经打好的产物，本项目没有完整自动重建 AppX 的脚本。后续若继续修改包内配置，需要回到 `_work/x64_453_localtile` 这一类解包目录重新签名打包。

## 继续开发建议

1. 优先稳定动态磁贴：
   - 确认 Windows 是否接受背景图、三列布局和城市名。
   - 如果 adaptive tile 仍不够像 4.46，可以改成服务端直接渲染整张 PNG 磁贴图。

2. 优化地名：
   - 当前 `locationName` 会优先显示。
   - 若应用没有传城市名，可考虑根据经纬度做反向地理编码。

3. 改进安装体验：
   - 可以把 AppX、证书、适配器服务和计划任务做成一个更完整的安装器。

4. 如果要公开到 GitHub：
   - 建议补充版权说明。
   - 公开二进制 AppX 和微软旧版视觉资源前，需要自行确认分发限制。
