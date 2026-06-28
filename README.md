# Bing Weather 4.53 复现旧版动态磁贴

>安装包在dist里。

这是一个用于继续改造 Microsoft/Bing Weather 早期 UWP 客户端的项目。当前方案以 Bing Weather 4.53 作为可运行底包，通过4.53版本原生API提供天气数据和动态磁贴 XML。

项目重点不是完整复活旧版微软天气服务，而是保留 4.53 的可运行性，同时恢复用户最容易感知的旧版体验：

- 4.46 风格的动态磁贴小天气图标。
- 旧版蓝色天气背景图。
- 三列小时预报布局。
- 磁贴底部城市名显示。
- 不依赖已经失效的旧微软天气 API。

## 当前状态

- 修改版 AppX 已经打包在 `dist/` 目录。
- AppX 的动态磁贴地址已指向本地服务 `http://127.0.0.1:8765`。

- 本地适配器会输出兼容旧 MSN/Bing Weather 调用形态的天气、地点搜索和动态磁贴响应。
- 已包含安装、启动、健康检查、磁贴 XML 预览和重新打包脚本。

## 目录结构

```text
.
├─ adapter/
│  └─ OpenMeteoAdapter/
│     ├─ openmeteo_msn_adapter.py       本地天气与动态磁贴服务
│     ├─ Start-Adapter.ps1              启动本地服务
│     ├─ Enable-WeatherLoopback.ps1     启用 UWP loopback
│     ├─ WeatherIcons/30x30/            4.46 风格小天气图标
│     └─ WeatherImages/                 4.46 风格磁贴背景
├─ dist/
│  ├─ OpenMeteo.BingWeather453LocalTile_4.53.41681.0_x64.appx
│  ├─ OpenMeteo.BingWeather453LocalTile_Adapter.zip
│  └─ OpenMeteo.BingWeather453Visual.Local.cer
├─ docs/
│  ├─ PROJECT_HANDOFF.md                项目交接总结
│  └─ TECHNICAL_NOTES.md                技术说明
└─ scripts/
   ├─ install-localtile.bat             安装 AppX 并注册本地服务
   ├─ start-adapter.bat                 手动启动本地服务
   ├─ health-check.bat                  检查本地服务状态
   ├─ preview-tile-xml.bat              预览动态磁贴 XML
   ├─ repack-adapter-zip.bat            重打适配器 zip
   └─ build-github-zip.bat              打包项目 zip
```

## 使用方法

### 1. 安装

在 Windows 10/11 上运行：

```bat
scripts\install-localtile.bat
```

安装脚本会执行以下操作：

- 导入本地测试证书。
- 安装修改版 AppX。
- 为 UWP 应用启用 loopback。
- 注册开机启动的本地适配器计划任务。
- 启动本地天气适配器。

安装完成后，建议将天气磁贴从开始菜单取消固定，再重新固定一次，以避免 Windows 继续显示缓存的旧磁贴。

### 2. 手动启动适配器

如果动态磁贴没有更新，可以手动启动本地服务：

```bat
scripts\start-adapter.bat
```

### 3. 检查服务状态

```bat
scripts\health-check.bat
```

也可以直接访问：

```text
http://127.0.0.1:8765/health
```

### 4. 预览动态磁贴 XML

```bat
scripts\preview-tile-xml.bat
```

脚本会请求一个示例磁贴接口，并把结果保存为 `tile-preview.xml`。

## 开发说明

本地适配器主文件是：

```text
adapter/OpenMeteoAdapter/openmeteo_msn_adapter.py
```

它主要负责：

- 响应 `/weather/`、`/locations/search`、`/geo/AutoSuggest`、`/REST/v1/Locations` 等路径。
- 生成 Windows 动态磁贴 XML。
- 提供本地天气图标和背景图静态资源。

动态磁贴生成逻辑位于 `tile_xml()`。旧版图标和背景映射分别由 `OLD_TILE_ICON_BY_ICON` 与 `OLD_TILE_BACKGROUND_BY_ICON` 控制。

语法检查：

```bat
python -m py_compile adapter\OpenMeteoAdapter\openmeteo_msn_adapter.py
```

重打适配器 zip：

```bat
scripts\repack-adapter-zip.bat
```

## 已知问题

- Windows 开始菜单可能缓存旧磁贴，安装后需要取消固定并重新固定。
- 本地适配器必须保持运行，否则动态磁贴可能空白或回退到静态磁贴。
- 当前仓库包含已经打好的 AppX，没有完整自动重建 AppX 的流水线。
- 如果要继续修改 AppX 内部配置，需要回到解包目录重新签名打包。

## 后续方向

- 稳定动态磁贴在不同 Windows 版本上的显示效果。
- 优化中文地点名和反向地理编码。
- 如果 adaptive tile 布局仍不够接近 4.46，可考虑由服务端直接渲染整张 PNG 磁贴图。
- 改进安装器，把证书、AppX、本地服务和计划任务做成更完整的安装流程。

## 版权与分发提醒

本仓库包含修改后的 AppX 以及从旧版应用中提取的视觉资源，适合个人研究、迁移和继续开发。公开发布、二次分发或长期托管前，请自行确认相关版权、商标、许可和应用分发限制。
