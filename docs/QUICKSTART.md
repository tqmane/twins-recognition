# クイックスタートガイド

学生発表向けに、最短で動かして見せる手順をまとめました。Linux環境（bash）を前提にしています。

## 0. リポジトリの取得

```
git clone https://github.com/tqmane/twins-recognition.git
cd twins-recognition
```

## 1. 推奨: 仮想環境 + 編集インストール

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

セットアップ後に使えるコマンド:
- CLI: `twins-cli`
- GUI: `twins-gui`
- Web: `twins-web`

## 2. すぐ動かす

- 単一画像の解析（簡潔出力）
```
twins-cli --image /path/to/photo.jpg --brief
```

- フォルダ内を一括解析（簡潔 + 集計）
```
twins-cli --folder /path/to/images --brief --summary
```

- GUI 起動（その場で画像/フォルダ選択）
```
twins-gui
```

- Web 起動（ブラウザで複数ファイルアップロード）
```
twins-web
# ブラウザで http://127.0.0.1:5000 を開く
```

## 3. Makefile でラクに

```
make install   # .venv 作成 + python3 -m pip install -e .
make cli       # CLIヘルプ動作確認
make gui       # GUI起動
make test      # テスト実行
```

## 4. Docker（ビルド済み環境で手堅く）

```
docker build -t twins-recognition .
docker run --rm -p 5000:5000 -v "$PWD":/work -w /work twins-recognition twins-cli --help
```

注: Web をコンテナから使う場合は、`ENTRYPOINT` をオーバーライドして `twins-web` を実行し、`-p 5000:5000` を付与してください。

## 5. 発表での見せ方の例

- CLI: `--brief --summary` を使うと、一覧とサマリーが端的に出せます。
- GUI: 画像を数枚用意して、ラベル/距離/検出顔数の表が埋まる様子をデモ。
- Web: 複数ファイルを同時にアップロードし、サムネイル（顔枠付き）とサマリー表示を解説。結果JSONのダウンロードも紹介。

## 6. トラブルシュート（よくある）

- `face_recognition_models` に関連するエラー（`pkg_resources` が無い等）
  - `python3 -m pip install -e .` で自動導入されますが、必要なら `python3 -m pip install setuptools` を追加してください。
- `tkinter` が無い（GUI起動で失敗）
  - 例: Ubuntu/Debian 系なら `sudo apt-get install python3-tk`。
- `dlib` のビルドが難しい
  - Docker利用を推奨。あるいは開発PCで `build-essential cmake` などのビルドツールを導入。
- HEIC/AVIF を扱いたい
  - 標準外です。`pillow-heif` を導入すると一部対応できます。

## 7. 注意・限界

- 本ツールは顔特徴の距離を用いたヒューリスティックであり、家族関係や双子であることを保証するものではありません。
- 照明・ポーズ・解像度で距離が揺れるため、`src/twins_recognition/classifier.py` の `THRESHOLDS` をデータに合わせて調整すると安定します。

---
質問や追加要望（例: 枠描画の強化、CSVエクスポート、ドラッグ&ドロップ対応）があればIssueにどうぞ。
