"""감성 분석 추론 — 순수 Python(동기). 라우터에서 run_in_threadpool로 호출한다."""
import numpy as np

from app.ml.loader import model_manager


def predict(text: str) -> float:
    """리뷰 텍스트 → 긍정 확률(0.0~1.0). 토크나이즈 → ONNX 추론 → softmax."""
    enc = model_manager.tokenizer.encode(text)  # truncation은 로더에서 설정됨
    logits = model_manager.session.run(
        None,
        {
            "input_ids": np.array([enc.ids], dtype=np.int64),
            "attention_mask": np.array([enc.attention_mask], dtype=np.int64),
            "token_type_ids": np.array([enc.type_ids], dtype=np.int64),
        },
    )[0][0]
    exp = np.exp(logits - logits.max())  # 오버플로 방지 softmax
    return float((exp / exp.sum())[1])
