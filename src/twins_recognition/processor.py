"""画像->分類結果 パイプライン"""
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any
import os

from .detector import load_image, detect_faces, FaceLocation
from .embedding import face_embeddings
from .classifier import classify_embeddings, TwinClassificationResult


@dataclass
class ImageAnalysis:
    path: str
    faces: List[FaceLocation]
    embeddings_count: int
    classification: TwinClassificationResult

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # face tuple をリストに
        d["faces"] = [list(f) for f in self.faces]
        return d


def analyze_image(path: str) -> ImageAnalysis:
    img = load_image(path)
    faces = detect_faces(path)
    embeddings = face_embeddings(img, faces) if len(faces) > 0 else []
    classification = classify_embeddings(embeddings)
    return ImageAnalysis(
        path=os.path.abspath(path),
        faces=faces,
        embeddings_count=len(embeddings),
        classification=classification,
    )
