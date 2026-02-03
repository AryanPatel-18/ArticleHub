import math


def cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """
    Computes cosine similarity between two sparse vectors.

    Expected format:
    {
        "indices": [int, int, ...],
        "values": [float, float, ...]
    }
    """

    if not vec_a or not vec_b:
        return 0.0

    indices_a = vec_a["indices"]
    values_a = vec_a["values"]
    indices_b = vec_b["indices"]
    values_b = vec_b["values"]

    dict_a = dict(zip(indices_a, values_a))
    dict_b = dict(zip(indices_b, values_b))

    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for idx, val in dict_a.items():
        norm_a += val * val
        if idx in dict_b:
            dot_product += val * dict_b[idx]

    for val in dict_b.values():
        norm_b += val * val

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))
