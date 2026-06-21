# OMRON 2JCIE-BU Prometheus Exporter

OMRON USB環境センサ [2JCIE-BU](https://www.omron.co.jp/ecb/product-detail?partId=73063)から取得した値を、Prometheusに投入するExporterです。

Dockerコンテナで動作します。

# 準備

## 用意するもの
- [OMRON 2JCIE-BU](https://www.omron.co.jp/ecb/product-detail?partId=73063)

![73063](https://user-images.githubusercontent.com/5038337/78334071-0d940400-75c6-11ea-9939-7b618b511d24.gif)

- 常時稼働させられる端末

![raspi](https://user-images.githubusercontent.com/5038337/78334741-4680a880-75c7-11ea-874d-331919984a66.png)

![friendryelec](https://user-images.githubusercontent.com/5038337/78334816-6617d100-75c7-11ea-8137-955a85d6252c.png)

など

# 手順
## udevルール作成
/etc/udev/rules.d/10-2JCIE-BU.rules
```
ACTION=="add", \
ATTRS{idVendor}=="0590", \
ATTRS{idProduct}=="00d4", \
RUN+="/sbin/modprobe ftdi_sio" \
RUN+="/bin/sh -c 'echo 0590 00d4 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id'", \
SYMLINK+="2JCIE-BU"
```
udevd restart
```
systemctl udevd restart
```

## 2JCIE-BU取付

## リポジトリクローン
```
git clone https://github.com/yasu-hide/2jciebu-exporter
```

## 設定編集
詳細は 設定ファイル (.envファイル) を参照
```
cd 2jciebu-exporter
cat <<'EOF' > .env
SENSOR_SERIAL_DEVICE=/dev/ttyUSB0
SERVER_HTTP_PORT=8000
EOF
```

## Dockerコンテナ起動
```
docker-compose up -d
```

## Enjoy!

# 設定ファイル (.envファイル)
## SENSOR_SERIAL_DEVICE
シリアルポートのデバイスファイルを指定

/dev/ttyUSB0以外を指定する場合、docker-compose.ymlの _devices_ も見直すこと

無指定の場合は __/dev/ttyUSB0__

## SERVER_HTTP_PORT
exporter用HTTPサーバの待ち受けポート番号を指定

無指定の場合は __8000__

# 参考情報
- 形2JCIE-BU　環境センサ USB型 | OMRON - Japan - https://www.omron.co.jp/ecb/product-detail?partNumber=2JCIE-BU
- omron-devhub/2jciebu-usb-raspberrypi - https://github.com/omron-devhub/2jciebu-usb-raspberrypi
- OMRON USB型環境センサー 2JCIE-BUをLinux(debian9/OpenBlocks IoT)からUSB接続して使用する - Qiita - https://qiita.com/goto2048/items/d2706088af90503dd4c8
- OMRON USB型環境センサーをLinux(debian9)にUSB接続する | ぷらっとブログ - https://blog.plathome.co.jp/omron-usb-environment-sensor-2jcie-bu-debian-9-openblocks-iot/
