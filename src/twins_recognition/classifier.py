"""双子/兄弟/類似/非類似分類ロジック
距離に基づくヒューリスティック。閾値は暫定で調整可能。
"""
from dataclasses import dataclass
from typing import Literal, List, Dict
import math

# 類似度閾値設定（ユーザが後で調整可能）
THRESHOLDS = {
    "twins": 0.40,       # これ以下ならほぼ同一 -> 双子候補
    "siblings": 0.55,    # twinsより大きく siblings 以下なら兄弟候補
    "similar": 0.60      # siblingsより大きく similar 以下なら単なる似ている人
}

ClassificationLabel = Literal["twins", "siblings", "similar", "different", "single_person", "no_face"]


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


@dataclass
class TwinClassificationResult:
    label: ClassificationLabel
    distance: float | None
    detail: Dict[str, float]


def classify_pair(embedding1: List[float], embedding2: List[float]) -> TwinClassificationResult:
    dist = euclidean_distance(embedding1, embedding2)
    if dist <= THRESHOLDS["twins"]:
        label: ClassificationLabel = "twins"
    elif dist <= THRESHOLDS["siblings"]:
        label = "siblings"
    elif dist <= THRESHOLDS["similar"]:
        label = "similar"
    else:
        label = "different"
    return TwinClassificationResult(label=label, distance=dist, detail={"distance": dist})


def classify_embeddings(embeddings: List[List[float]]) -> TwinClassificationResult:
    if len(embeddings) == 0:
        return TwinClassificationResult(label="no_face", distance=None, detail={})
    if len(embeddings) == 1:
        return TwinClassificationResult(label="single_person", distance=None, detail={})
    # 2つだけ比較（>2 の場合は最も距離が小さいペアを採用して代表分類）
    if len(embeddings) == 2:
        return classify_pair(embeddings[0], embeddings[1])
    # 3人以上: 全組合せから最小距離ペア
    min_dist = float("inf")
    best = None
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            d = euclidean_distance(embeddings[i], embeddings[j])
            if d < min_dist:
                min_dist = d
                best = (embeddings[i], embeddings[j])
    result = classify_pair(best[0], best[1])  # type: ignore
    result.detail["faces_count"] = len(embeddings)
    result.detail["min_pair_distance"] = min_dist
    return result
