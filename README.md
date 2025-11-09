# twins-recognition
ローカルのみで動作する簡易「双子 / 兄弟 / 類似 / 異なる人物」識別ツール。

👉 最短で動かすには「クイックスタート」を参照: [`docs/QUICKSTART.md`](docs/QUICKSTART.md)

## 概要
1枚の画像、またはフォルダ内の複数画像を処理し、各画像について検出された顔のペアの距離から以下のラベルを推定します (括弧内は英語内部ラベル):
- `双子 (twins)` : 非常に近い（ほぼ同一の顔特徴）
- `兄弟/姉妹/兄妹/姉弟 (siblings)` : 双子ほどではないが近い特徴
- `類似 (similar)` : それなりに似ている
- `異なる (different)` : 類似度が低い
- `単一人物 (single_person)` : 顔が1つだけ検出された
- `顔未検出 (no_face)` : 顔が検出されない

> 注意: これはヒューリスティック（簡易距離閾値）による推定であり、厳密な遺伝的・家族的関係を保証するものではありません。

## インストール
Python 3.10+ を推奨。

```
python3 -m pip install -r requirements.txt
```

`dlib` のビルドが難しい環境では `face_recognition` のインストールが失敗する場合があります。その場合は Docker を使うか、別途ビルド手順を参照してください。

### もっと簡単に（推奨）
pyproject によりパッケージ化済みなので、以下だけでコマンドが使えます:

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .

# CLI
twins-cli --image path/to/photo.jpg --pretty

# GUI
twins-gui
```

### 簡潔表示オプション

大量の画像を扱うときに JSON 全体を見たくない場合は `--brief` で 1 行 / 画像 のタブ区切り出力、`--summary` で集計を表示できます。

例:
```
twins-cli --folder ./images --brief --summary
```
出力例:
```
twins	0.305	2	/path/to/img1.jpg
no_face	-	0	/path/to/img2.png

# summary
twins: 1 (50.0%)
no_face: 1 (50.0%)
mean_distance: 0.305
median_distance: 0.305
```

Makefile も用意しています:

```
make install    # .venv 作成 + python3 -m pip install -e .
make cli        # CLIのヘルプ
make gui        # GUI を起動
make dev        # pytest など開発ツール導入
make test       # テスト実行
```

Docker で試す場合 (ホスト側にビルド環境を入れたくない場合推奨):

```
docker build -t twins-recognition .
docker run --rm -v "$PWD":/work -w /work twins-recognition twins-cli --help

# Web をコンテナで起動したい場合:
docker run --rm -p 5000:5000 -v "$PWD":/work -w /work --entrypoint twins-web twins-recognition
```

## 使い方 (CLI)

単一画像:
```
python3 -m twins_recognition.cli --image path/to/photo.jpg --pretty
```

フォルダ一括:
```
python3 -m twins_recognition.cli --folder path/to/folder --pretty
```

結果をファイルへ保存:
```
python3 -m twins_recognition.cli --image sample.jpg --output result.json --pretty
```

## GUI

```
python3 -m twins_recognition.gui
```
ウィンドウが開いたら「画像を選択」または「フォルダを選択」で処理。結果はテーブル表示されます。

対応画像形式（拡張子）: jpg, jpeg, png, bmp, webp, tif, tiff, gif, jp2, ppm, pnm, pbm, pgm
（注: HEIC/AVIFは標準では未対応。Pillow用プラグイン導入で対応可能ですが、本ツールでは標準外です）

## Web (ローカルホスト)

ブラウザから複数ファイルをアップロードして解析できます。サマリーと個別一覧、サムネイル（顔枠表示）も表示されます。

起動:
```
twins-web
# ブラウザで http://127.0.0.1:5000 を開く
```

機能:
- 複数画像アップロード
- サマリー（件数・割合、距離の平均/中央値）
- 個別一覧（ラベル/距離/顔数、元画像リンク）
- サムネイル表示（顔枠のオーバーレイ）
- 結果JSONのダウンロード
- リセットボタン（結果画面から当該アップロードを削除してトップへ戻る）
- リアルタイム解析進捗 (SSE) : アップロード後は進捗バーと現在処理中ファイル・ラベルが逐次反映

補足:
- 一時アップロードは OS のテンポラリ配下に保存され、24時間以上経過したものは自動削除します。
- favicon は内蔵生成しており、追加設定は不要です。
 - 結果画面の「この結果をリセット」で対象バッチを即時削除できます。
 - 逐次進捗は EventSource (Server-Sent Events) を利用。長時間大量処理でもブラウザを開いたままで確認可。

## クレジット / Acknowledgements

このプロジェクトは以下の素晴らしいオープンソースに依存しています（敬称略）。

- face_recognition / face_recognition_models（Adam Geitgey）
- dlib（Davis E. King）
- Pillow（PIL Fork）
- OpenCV (opencv-python)
- NumPy
- Flask

ライブラリのライセンスは各プロジェクトの配布条件に従います。本リポジトリは学術・個人利用シナリオでのデモを想定しています。

## 判定ロジック
`src/twins_recognition/classifier.py` 内の `THRESHOLDS` 定数で距離境界を調整できます。

距離は `face_recognition` の 128 次元埋め込み間ユークリッド距離です:

| 日本語表示 | 英語内部 | 距離条件 (初期値) |
|------------|-----------|-------------------|
| 双子 | twins | <= 0.40 |
| 兄弟/姉妹/兄妹/姉弟 | siblings | <= 0.55 |
| 類似 | similar | <= 0.60 |
| 異なる | different | > 0.60 |

3人以上写っている場合は、最も距離の小さいペアを代表として分類し、`faces_count` として総顔数を detail に含めます。

## 制限事項 / 注意
- 照明・角度・表情差で距離は大きく変動します。
- 実際の双子かどうかの医学的判定は行えません。
- 顔検出失敗や誤検出があると結果が不正確になります。
- オフライン処理のため学習・微調整は行っていません。

## テスト
```
pytest -q
```
`tests/test_classifier.py` で閾値境界の単体テストを実施しています。

## 次の改善候補
- Embedding の正規化とコサイン距離併用
- 画像前処理 (明るさ補正, アライン)
- 閾値自動調整用スクリプト
- dlib 不要な軽量モード (mediapipe など)

