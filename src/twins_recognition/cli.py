"""コマンドラインインターフェース
使い方:
    python3 -m twins_recognition.cli --image path/to/img.jpg
    python3 -m twins_recognition.cli --folder path/to/images
"""
import argparse
import json
import os
from typing import List

from .processor import analyze_image
from typing import Dict

try:
    from PIL import Image  # Pillow がサポートする拡張を利用
except ImportError:
    Image = None  # Pillow未インストールでも最低限動く（face_recognition内部でPIL必要）

# Pillow標準対応 + よく使われる形式を追加 (HEIC/AVIF は別途プラグインが必要なので除外)
SUPPORTED_EXT = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".gif",
    ".jp2", ".ppm", ".pnm", ".pbm", ".pgm"
}


def is_image_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    if ext in SUPPORTED_EXT:
        return True
    # 拡張子で弾かれたが Pillow が開ける可能性を一応確認（パフォーマンス目的で例外は握りつぶす）
    if Image is not None:
        try:
            with Image.open(path):
                return True
        except Exception:
            return False
    return False


def collect_images(folder: str) -> List[str]:
    paths: List[str] = []
    for root, _, files in os.walk(folder):
        for f in files:
            full = os.path.join(root, f)
            if is_image_file(full):
                paths.append(full)
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description="双子識別 (ローカル) CLI")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--image", type=str, help="単一画像パス")
    g.add_argument("--folder", type=str, help="フォルダ内画像を一括処理")
    parser.add_argument("--output", type=str, help="結果JSON保存パス", default=None)
    parser.add_argument("--pretty", action="store_true", help="整形して表示")
    parser.add_argument("--brief", action="store_true", help="結果を1行/画像で要約 (label 距離 顔数 パス)")
    parser.add_argument("--summary", action="store_true", help="全体集計 (各ラベル件数と割合) を表示")
    args = parser.parse_args()

    if args.image:
        analyses = [analyze_image(args.image)]
    else:
        imgs = collect_images(args.folder)
        analyses = [analyze_image(p) for p in imgs]

    # 通常JSON（日本語ラベルも付与）
    def ja_label(label: str) -> str:
        return {
            'twins': '双子',
            'siblings': '兄弟/姉妹/兄妹/姉弟',
            'similar': '類似',
            'different': '異なる',
            'single_person': '単一人物',
            'no_face': '顔未検出',
        }.get(label, label)

    out = [a.to_dict() for a in analyses]
    for item in out:
        cls = item.get('classification', {})
        if 'label' in cls:
            cls['label_ja'] = ja_label(cls['label'])

    if args.brief:
        # label 距離(3桁) faces path
        def ja_label_brief(label: str) -> str:
            return {
                'twins': '双子',
                'siblings': '兄弟/姉妹/兄妹/姉弟',
                'similar': '類似',
                'different': '異なる',
                'single_person': '単一人物',
                'no_face': '顔未検出',
            }.get(label, label)
        for a in analyses:
            cls = a.classification
            dist = cls.distance
            dist_str = f"{dist:.3f}" if dist is not None else "-"
            print(f"{ja_label_brief(cls.label)}\t{dist_str}\t{len(a.faces)}\t{a.path}")
    else:
        text = json.dumps(out, ensure_ascii=False, indent=2 if args.pretty else None)
        print(text)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)

    if args.summary:
        from collections import Counter
        labels = [a.classification.label for a in analyses]
        c = Counter(labels)
        total = sum(c.values()) or 1
        print("\n# summary")
        for label, cnt in c.items():
            shown = {
                'twins': '双子',
                'siblings': '兄弟/姉妹/兄妹/姉弟',
                'similar': '類似',
                'different': '異なる',
                'single_person': '単一人物',
                'no_face': '顔未検出',
            }.get(label, label)
            print(f"{shown}: {cnt} ({cnt/total*100:.1f}%)")
        # 平均距離 (twins/siblings/similar/different のみ)
        dists = [a.classification.distance for a in analyses if a.classification.distance is not None]
        if dists:
            import statistics
            print(f"mean_distance: {statistics.mean(dists):.3f}")
            print(f"median_distance: {statistics.median(dists):.3f}")

if __name__ == "__main__":
    main()
