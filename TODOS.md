# TODOS

このリポジトリで見つかった、今後対応を検討すべき項目。優先度順ではない。

## 1. main.py起動直後の`sen.open()`失敗クラッシュ

**What:** main.py起動直後、センサ未接続だと`sen.open()`が`SensorSerialError`を投げてプロセスが即時終了する（リトライなし）。

**Why:** ループ内の読み取り失敗には10秒後リトライがあるのに、起動時の接続失敗にはリトライがなく非対称。

**Context:** `if __name__=="__main__":`内`sen.open()`をtry/exceptで囲むか、`docker-compose.yml`のrestartポリシーで十分かを確認するところから始める。

**Depends on:** なし。

## 2. `Sensor.close()`の無限再帰リトライ

**What:** `sensor.py` `Sensor.close()`は`except serial.SerialException: self.close()`で自己再帰するが上限がない。恒久障害時に`RecursionError`でクラッシュしうる。

**Why:** 一時的障害（1回失敗→2回目成功）は問題ないが、ポート切断等の恒久障害では危険。

**Context:** `while`ループ+回数上限（例: 3回）に書き換え、上限到達時の振る舞いを決める。`tests/conftest.py`の`mock_port`フィクスチャをそのまま流用可能。

**Depends on:** なし（`tests/conftest.py`があると実装が楽になる、という順序メリットのみ）。

## 3. `sensor.py`のデッドコード削除

**What:** `sensor.py` 5行目 `TO_INT = lambda s: int(s.encode('hex'), 16)`（Python2専用・未使用デッドコード）の削除。

**Why:** 実害はないが読む人を惑わせる。

**Context:** 1行削除するだけ。

**Depends on:** なし。
