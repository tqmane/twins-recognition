"""顔埋め込み生成モジュール
検出済み顔領域から128次元の顔エンコーディングを取得。
"""
from typing import List, Tuple

try:
    import face_recognition  # type: ignore
except ImportError as e:
    raise ImportError("face_recognition がインストールされていません。requirements.txt を参照してください") from e

FaceLocation = Tuple[int, int, int, int]


def face_embeddings(image, face_locations: List[FaceLocation]) -> List[List[float]]:
    """face_recognition で顔埋め込みを取得"""
    encodings = face_recognition.face_encodings(image, face_locations)
    return [list(e) for e in encodings]
