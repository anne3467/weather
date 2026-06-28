# 技术说明

## 本地服务端口

默认端口为：

```text
http://127.0.0.1:8765
```

健康检查：

```text
http://127.0.0.1:8765/health
```

动态磁贴测试：

```text
http://127.0.0.1:8765/zh-cn/livetile/back/22.5,113.9?locationName=%E5%8D%97%E5%B1%B1%E5%8C%BA&units=C
```

## AppX 身份

当前推荐包：

```text
OpenMeteo.BingWeather453LocalTile
```

证书发布者：

```text
CN=OpenMeteo BingWeather Local
```

## 关键资源

旧版动态磁贴小图标：

```text
adapter/OpenMeteoAdapter/WeatherIcons/30x30/*.png
```

旧版动态磁贴背景：

```text
adapter/OpenMeteoAdapter/WeatherImages/210x173/*.jpg
adapter/OpenMeteoAdapter/WeatherImages/423x173/*.jpg
```

## 关键脚本

安装：

```text
scripts/install-localtile.bat
```

启动本地服务：

```text
scripts/start-adapter.bat
```

重打适配器 zip：

```text
scripts/repack-adapter-zip.bat
```

重打 GitHub 项目 zip：

```text
scripts/build-github-zip.bat
```

## 当前依赖

- Windows 10/11。
- Python 可从命令行以 `python` 调用。
- PowerShell。
- Windows AppX 安装能力。

本地天气数据来自 Open-Meteo。运行时需要网络访问 Open-Meteo，否则磁贴会进入服务端兜底内容。
