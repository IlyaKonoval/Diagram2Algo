from dataclasses import dataclass
from typing import Optional

import numpy as np

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model


@dataclass
class MetricsResult:
    semantic_precision: float
    semantic_recall: float
    semantic_f1: float

    sequence_lcs: float
    sequence_edit_distance: float

    role_accuracy: float

    step_count_accuracy: float

    composite_score: float

    matched_pairs: list
    gt_count: int
    extracted_count: int


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_semantic_similarity_matrix(
    texts1: list[str],
    texts2: list[str]
) -> np.ndarray:
    if not texts1 or not texts2:
        return np.array([])

    model = get_embedding_model()

    emb1 = model.encode(texts1, convert_to_numpy=True)
    emb2 = model.encode(texts2, convert_to_numpy=True)

    emb1_norm = emb1 / np.linalg.norm(emb1, axis=1, keepdims=True)
    emb2_norm = emb2 / np.linalg.norm(emb2, axis=1, keepdims=True)

    similarity_matrix = np.dot(emb1_norm, emb2_norm.T)

    return similarity_matrix


def bipartite_match(
    similarity_matrix: np.ndarray,
    threshold: float = 0.5
) -> list[tuple[int, int, float]]:
    if similarity_matrix.size == 0:
        return []

    matches = []
    used_rows = set()
    used_cols = set()

    rows, cols = similarity_matrix.shape
    cells = []
    for i in range(rows):
        for j in range(cols):
            cells.append((similarity_matrix[i, j], i, j))

    cells.sort(reverse=True)

    for sim, i, j in cells:
        if sim < threshold:
            break
        if i not in used_rows and j not in used_cols:
            matches.append((i, j, sim))
            used_rows.add(i)
            used_cols.add(j)

    return matches


def compute_lcs_ratio(seq1: list, seq2: list) -> float:
    if not seq1 or not seq2:
        return 0.0

    m, n = len(seq1), len(seq2)

    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i-1] == seq2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    lcs_length = dp[m][n]
    return lcs_length / max(m, n)


def compute_edit_distance_ratio(seq1: list, seq2: list) -> float:
    if not seq1 and not seq2:
        return 1.0
    if not seq1 or not seq2:
        return 0.0

    m, n = len(seq1), len(seq2)

    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i-1] == seq2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],
                    dp[i][j-1],
                    dp[i-1][j-1]
                )

    edit_distance = dp[m][n]
    max_len = max(m, n)

    return 1 - (edit_distance / max_len)


def calculate_metrics(
    extracted_steps: list[dict],
    gt_steps: list[dict],
    semantic_threshold: float = 0.5,
    weights: Optional[dict] = None
) -> MetricsResult:
    if weights is None:
        weights = {
            'semantic': 0.4,
            'sequence': 0.3,
            'role': 0.2,
            'count': 0.1
        }

    gt_count = len(gt_steps)
    ex_count = len(extracted_steps)

    if gt_count == 0 and ex_count == 0:
        return MetricsResult(
            semantic_precision=1.0, semantic_recall=1.0, semantic_f1=1.0,
            sequence_lcs=1.0, sequence_edit_distance=1.0,
            role_accuracy=1.0, step_count_accuracy=1.0,
            composite_score=1.0, matched_pairs=[], gt_count=0, extracted_count=0
        )

    if gt_count == 0:
        return MetricsResult(
            semantic_precision=0.0, semantic_recall=1.0, semantic_f1=0.0,
            sequence_lcs=0.0, sequence_edit_distance=0.0,
            role_accuracy=0.0, step_count_accuracy=0.0,
            composite_score=0.0, matched_pairs=[], gt_count=0, extracted_count=ex_count
        )

    if ex_count == 0:
        return MetricsResult(
            semantic_precision=0.0, semantic_recall=0.0, semantic_f1=0.0,
            sequence_lcs=0.0, sequence_edit_distance=0.0,
            role_accuracy=0.0, step_count_accuracy=0.0,
            composite_score=0.0, matched_pairs=[], gt_count=gt_count, extracted_count=0
        )

    gt_actions = [s.get('action', '') for s in gt_steps]
    ex_actions = [s.get('action', '') for s in extracted_steps]

    sim_matrix = compute_semantic_similarity_matrix(ex_actions, gt_actions)
    matched_pairs = bipartite_match(sim_matrix, threshold=semantic_threshold)

    num_matched = len(matched_pairs)
    semantic_precision = num_matched / ex_count if ex_count > 0 else 0
    semantic_recall = num_matched / gt_count if gt_count > 0 else 0
    semantic_f1 = (
        2 * semantic_precision * semantic_recall / (semantic_precision + semantic_recall)
        if (semantic_precision + semantic_recall) > 0 else 0
    )

    gt_to_ex = {gt_idx: ex_idx for ex_idx, gt_idx, _ in matched_pairs}

    matched_ex_sequence = [gt_to_ex[i] for i in range(gt_count) if i in gt_to_ex]
    expected_sequence = list(range(len(matched_ex_sequence)))

    if matched_ex_sequence:
        sorted_indices = sorted(range(len(matched_ex_sequence)), key=lambda i: matched_ex_sequence[i])
        normalized_sequence = [0] * len(matched_ex_sequence)
        for rank, idx in enumerate(sorted_indices):
            normalized_sequence[idx] = rank

        sequence_lcs = compute_lcs_ratio(expected_sequence, normalized_sequence)
        sequence_edit = compute_edit_distance_ratio(expected_sequence, normalized_sequence)
    else:
        sequence_lcs = 0.0
        sequence_edit = 0.0

    role_correct = 0
    role_total = 0

    for ex_idx, gt_idx, _ in matched_pairs:
        gt_role = gt_steps[gt_idx].get('role') or gt_steps[gt_idx].get('actor')
        ex_role = extracted_steps[ex_idx].get('role') or extracted_steps[ex_idx].get('actor')

        if gt_role:
            role_total += 1
            if ex_role and gt_role.lower().strip() == ex_role.lower().strip():
                role_correct += 1

    role_accuracy = role_correct / role_total if role_total > 0 else 1.0

    count_error = abs(ex_count - gt_count) / gt_count
    step_count_accuracy = max(0, 1 - count_error)

    composite_score = (
        weights['semantic'] * semantic_f1 +
        weights['sequence'] * ((sequence_lcs + sequence_edit) / 2) +
        weights['role'] * role_accuracy +
        weights['count'] * step_count_accuracy
    )

    return MetricsResult(
        semantic_precision=semantic_precision,
        semantic_recall=semantic_recall,
        semantic_f1=semantic_f1,
        sequence_lcs=sequence_lcs,
        sequence_edit_distance=sequence_edit,
        role_accuracy=role_accuracy,
        step_count_accuracy=step_count_accuracy,
        composite_score=composite_score,
        matched_pairs=[(ex_idx, gt_idx, sim) for ex_idx, gt_idx, sim in matched_pairs],
        gt_count=gt_count,
        extracted_count=ex_count
    )


def warmup_metrics():
    get_embedding_model()
