from __future__ import annotations
from flask import Flask, request, render_template, send_from_directory, Response, redirect, url_for, stream_with_context
import os
import tempfile
import shutil
import io
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .processor import analyze_image
import csv

app = Flask(__name__)

UPLOAD_ROOT = os.path.join(tempfile.gettempdir(), "twins_uploads")
THUMB_DIRNAME = "thumbs"

os.makedirs(UPLOAD_ROOT, exist_ok=True)


# 日本語表示用ラベルフィルタ（siblings を 兄弟/姉妹/兄妹/姉弟 として表示）
def ja_label(label: str) -> str:
    return {
        'twins': '双子',
        'siblings': '兄弟/姉妹/兄妹/姉弟',
        'similar': '類似',
        'different': '異なる',
        'single_person': '単一人物',
        'no_face': '顔未検出',
    }.get(label, label)

app.jinja_env.filters['ja_label'] = ja_label


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def make_thumb(src_path: str, dst_path: str, faces: List[List[int]] | None = None, size=(320, 320)):
    try:
        from PIL import Image
        from PIL import ImageDraw
        with Image.open(src_path) as im:
            im.thumbnail(size)
            # 顔枠を描画 (faces は [top, right, bottom, left])
            if faces:
                draw = ImageDraw.Draw(im)
                for (t, r, b, l) in faces:
                    # Pillowは (left, top, right, bottom)
                    draw.rectangle([(l, t), (r, b)], outline=(255, 0, 0), width=2)
            im.save(dst_path)
    except Exception:
        # サムネイル生成に失敗しても致命的ではない
        pass


@app.route("/")
def index():
    cleanup_old_batches(hours=24)
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    # 一時ディレクトリを作成してアップロードを保管
    tmpdir = tempfile.mkdtemp(prefix="twins_", dir=UPLOAD_ROOT)
    thumbs = os.path.join(tmpdir, THUMB_DIRNAME)
    ensure_dir(thumbs)

    files = request.files.getlist("files")
    results: List[Dict[str, Any]] = []
    for f in files:
        if not f.filename:
            continue
        save_path = os.path.join(tmpdir, f.filename)
        ensure_dir(os.path.dirname(save_path))
        f.save(save_path)
        # 解析実行
        a = analyze_image(save_path)
        d = a.to_dict()
        # 日本語ラベル付与
        try:
            raw = d.get("classification", {}).get("label")
            d["classification"]["label_ja"] = ja_label(raw)
        except Exception:
            pass
        # サムネイル
        thumb_name = f"{os.path.basename(save_path)}.thumb.jpg"
        thumb_path = os.path.join(thumbs, thumb_name)
        make_thumb(save_path, thumb_path, faces=d.get("faces"))
        d["thumb_url"] = f"/static_tmp/{os.path.basename(tmpdir)}/{THUMB_DIRNAME}/{thumb_name}"
        d["relpath"] = f"/static_tmp/{os.path.basename(tmpdir)}/{os.path.basename(save_path)}"
        results.append(d)

    # サマリー
    from collections import Counter
    labels = [r["classification"]["label"] for r in results]
    c = Counter(labels)
    total = sum(c.values()) or 1
    summary = {
        "counts": dict(c),
        "total": total,
    }
    dists = [r["classification"]["distance"] for r in results if r["classification"]["distance"] is not None]
    if dists:
        import statistics
        summary["mean_distance"] = round(statistics.mean(dists), 3)
        summary["median_distance"] = round(statistics.median(dists), 3)

    # 結果JSONを保存してダウンロード可能に
    results_json_path = os.path.join(tmpdir, "results.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": summary}, f, ensure_ascii=False, indent=2)

    # CSV も保存（ラベルは日本語で出力）
    results_csv_path = os.path.join(tmpdir, "results.csv")
    with open(results_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "label", "distance", "faces", "abs_path"])
        for r in results:
            label = ja_label(r.get("classification", {}).get("label"))
            dist = r.get("classification", {}).get("distance")
            faces_cnt = len(r.get("faces", []))
            writer.writerow([
                os.path.basename(r.get("path", "")),
                label,
                ("" if dist is None else round(dist, 3)),
                faces_cnt,
                r.get("path", ""),
            ])

    return render_template("result.html", results=results, summary=summary, batch=os.path.basename(tmpdir))


@app.route("/static_tmp/<batch>/<path:filename>")
def static_tmp(batch: str, filename: str):
    root = os.path.join(UPLOAD_ROOT, batch)
    # thumbs または元画像の配送
    if filename.startswith(THUMB_DIRNAME + "/"):
        return send_from_directory(os.path.join(root, THUMB_DIRNAME), filename.split("/",1)[1])
    return send_from_directory(root, filename)


@app.route('/download/<batch>.json')
def download_json(batch: str):
    root = os.path.join(UPLOAD_ROOT, batch)
    return send_from_directory(root, 'results.json', as_attachment=True)


@app.route('/download/<batch>.csv')
def download_csv(batch: str):
    root = os.path.join(UPLOAD_ROOT, batch)
    return send_from_directory(root, 'results.csv', as_attachment=True, mimetype='text/csv')


@app.route('/favicon.ico')
def favicon():
    # 動的に小さなアイコンを生成
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([(6, 6), (26, 26)], outline=(0, 122, 204), width=3)
        buf = io.BytesIO()
        img.save(buf, format='ICO')
        buf.seek(0)
        return Response(buf.getvalue(), mimetype='image/x-icon')
    except Exception:
        return Response(status=404)


def cleanup_old_batches(hours: int = 24):
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        for name in os.listdir(UPLOAD_ROOT):
            p = os.path.join(UPLOAD_ROOT, name)
            try:
                st = os.stat(p)
                mtime = datetime.fromtimestamp(st.st_mtime)
                if mtime < cutoff:
                    shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass
    except Exception:
        pass


@app.route('/reset/<batch>', methods=['POST'])
def reset(batch: str):
    # 指定バッチを削除してトップへ
    try:
        root = os.path.join(UPLOAD_ROOT, batch)
        if os.path.isdir(root):
            shutil.rmtree(root, ignore_errors=True)
    except Exception:
        pass
    return redirect(url_for('index'))


def run():
    # Flask 起動（0.0.0.0:5000で待ち受け、外部アクセスを許可）
    app.run(host="0.0.0.0", port=5000, debug=False)


# --- 新規: アップロードと逐次処理（SSE） ---

@app.post('/upload')
def upload():
    tmpdir = tempfile.mkdtemp(prefix="twins_", dir=UPLOAD_ROOT)
    ensure_dir(os.path.join(tmpdir, THUMB_DIRNAME))
    files = request.files.getlist('files')
    saved = []
    for f in files:
        if not f.filename:
            continue
        save_path = os.path.join(tmpdir, f.filename)
        ensure_dir(os.path.dirname(save_path))
        f.save(save_path)
        saved.append(os.path.basename(save_path))
    resp = {"batch": os.path.basename(tmpdir), "files": saved}
    return Response(json.dumps(resp), mimetype='application/json')


@app.get('/process/<batch>/stream')
def process_stream(batch: str):
    root = os.path.join(UPLOAD_ROOT, batch)
    thumbs = os.path.join(root, THUMB_DIRNAME)
    ensure_dir(thumbs)

    # 処理対象ファイルを列挙（thumbs/や生成物は除外）
    files = [f for f in os.listdir(root)
             if os.path.isfile(os.path.join(root, f)) and not f.endswith('.json') and not f.endswith('.csv')]
    files = [f for f in files if f != 'results.json' and f != 'results.csv']
    total = len(files)

    def gen():
        results: List[Dict[str, Any]] = []
        for idx, name in enumerate(sorted(files), start=1):
            path = os.path.join(root, name)
            try:
                a = analyze_image(path)
                d = a.to_dict()
                # サムネイル生成
                thumb_name = f"{name}.thumb.jpg"
                thumb_path = os.path.join(thumbs, thumb_name)
                make_thumb(path, thumb_path, faces=d.get('faces'))
                d["thumb_url"] = f"/static_tmp/{batch}/{THUMB_DIRNAME}/{thumb_name}"
                d["relpath"] = f"/static_tmp/{batch}/{name}"
                try:
                    raw = d.get("classification", {}).get("label")
                    d["classification"]["label_ja"] = ja_label(raw)
                except Exception:
                    pass
                results.append(d)
                # 進捗通知
                pct = int(idx / max(total, 1) * 100)
                payload = {
                    "index": idx,
                    "total": total,
                    "pct": pct,
                    "filename": name,
                    "label": d.get("classification", {}).get("label"),
                    "distance": d.get("classification", {}).get("distance"),
                }
                yield f"event: progress\n" + f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            except Exception as e:
                payload = {"index": idx, "total": total, "pct": int(idx/max(total,1)*100), "filename": name, "error": str(e)}
                yield f"event: progress\n" + f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # サマリーと結果保存
        from collections import Counter
        labels = [r["classification"]["label"] for r in results]
        c = Counter(labels)
        summary: Dict[str, Any] = {"counts": dict(c), "total": len(results)}
        dists = [r["classification"]["distance"] for r in results if r["classification"]["distance"] is not None]
        if dists:
            import statistics
            summary["mean_distance"] = round(statistics.mean(dists), 3)
            summary["median_distance"] = round(statistics.median(dists), 3)

        with open(os.path.join(root, 'results.json'), 'w', encoding='utf-8') as f:
            json.dump({"results": results, "summary": summary}, f, ensure_ascii=False, indent=2)
        with open(os.path.join(root, 'results.csv'), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["file", "label", "distance", "faces", "abs_path"])
            for r in results:
                label = ja_label(r.get("classification", {}).get("label"))
                dist = r.get("classification", {}).get("distance")
                faces_cnt = len(r.get("faces", []))
                writer.writerow([os.path.basename(r.get("path", "")), label, ("" if dist is None else round(dist, 3)), faces_cnt, r.get("path", "")])

        done_payload = {"url": f"/batch/{batch}"}
        yield f"event: done\n" + f"data: {json.dumps(done_payload)}\n\n"

    return Response(stream_with_context(gen()), mimetype='text/event-stream')


@app.get('/batch/<batch>')
def view_batch(batch: str):
    root = os.path.join(UPLOAD_ROOT, batch)
    try:
        with open(os.path.join(root, 'results.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        return render_template('result.html', results=data.get('results', []), summary=data.get('summary', {}), batch=batch)
    except Exception:
        # 結果がまだ無い/壊れている場合はトップへ
        return redirect(url_for('index'))
