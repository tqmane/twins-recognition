"""顔検出モジュール
face_recognition ライブラリを用いて画像中の顔位置(トップ,右,ボトム,左)を返す。
ローカルのみで動作。
"""
from typing import List, Tuple
import os

try:
    import face_recognition  # type: ignore
except ImportError as e:
    raise ImportError("face_recognition がインストールされていません。requirements.txt を参照してください") from e

FaceLocation = Tuple[int, int, int, int]


def load_image(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"画像が存在しません: {path}")
    return face_recognition.load_image_file(path)


def detect_faces(path: str) -> List[FaceLocation]:
    """画像パスから顔位置一覧を返す。"""
    img = load_image(path)
    # モデルを変えたい場合は face_recognition.face_locations(img, model="cnn") など
    locations = face_recognition.face_locations(img)
    return locations
