# Bing Weather 4.53 with 4.46-style live tiles

这个项目用于继承当前的改包工作：以 Microsoft/Bing Weather 4.53 作为可运行底包，尽量恢复 4.46 旧版界面观感，重点是旧版动态磁贴的图标、蓝色天气背景、三列小时预报和底部城市名。

## 当前状态

- 4.53 AppX 已经改成使用本地动态磁贴服务。
- 本地服务使用 Open-Meteo 免费天气数据，不依赖旧版微软天气 API。
- 动态磁贴资源改用 4.46 的 `30x30` 小天气图标。
- 动态磁贴背景改用 4.46 的 `WeatherImages` 蓝色天气背景。
- 已包含安装脚本、验证脚本、适配器重打包脚本和项目 zip 打包脚本。

## 目录结构

```text
.
├─ adapter/
│  └─ OpenMeteoAdapter/          本地天气与动态磁贴服务
├─ dist/
│  ├─ OpenMeteo.BingWeather453LocalTile_4.53.41681.0_x64.appx
│  ├─ OpenMeteo.BingWeather453LocalTile_Adapter.zip
│  └─ OpenMeteo.BingWeather453Visual.Local.cer
├─ docs/
│  ├─ PROJECT_HANDOFF.md         项目交接总结
│  └─ TECHNICAL_NOTES.md         技术细节和后续方向
└─ scripts/
   ├─ install-localtile.bat
   ├─ start-adapter.bat
   ├─ health-check.bat
   ├─ preview-tile-xml.bat
   ├─ repack-adapter-zip.bat
   └─ build-github-zip.bat
```

## 快速使用

1. 右键或双击运行 `scripts/install-localtile.bat`。
2. 安装完成后，将天气磁贴从开始菜单取消固定，再重新固定一次。
3. 如需确认本地服务是否工作，运行 `scripts/health-check.bat`。
4. 如需查看动态磁贴 XML，运行 `scripts/preview-tile-xml.bat`。

## 注意

这个仓库包含从旧版应用中提取的视觉资源和一个修改后的 AppX，适合个人研究、迁移和继续开发。公开发布前请自行确认相关版权、商标和分发限制。
