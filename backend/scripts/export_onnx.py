"""감성 분석 모델을 ONNX로 변환하고 동적 양자화(INT8)한다.

산출물 (ml_assets/):
  - sentiment_fp32.onnx : ONNX 변환본 (그래프 최적화, 정확도 손실 0)
  - sentiment_int8.onnx : 동적 양자화본 (가중치 INT8, 크기 ~1/4)
  - tokenizer 파일들    : 서빙 시 오프라인 로드용

실행: backend/ 에서  python scripts/export_onnx.py
"""
import shutil
import tempfile
from pathlib import Path

import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_ID = "daekeun-ml/koelectra-small-v3-nsmc"
ASSETS = Path(__file__).resolve().parent.parent / "ml_assets"


class LogitsOnly(torch.nn.Module):
    """HF 모델의 dict 출력 대신 logits 텐서만 반환 — ONNX 추적을 단순하게."""

    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, input_ids, attention_mask, token_type_ids):
        return self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        ).logits


def main():
    ASSETS.mkdir(exist_ok=True)

    print(f"[1/4] 모델 다운로드: {MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.eval()  # Dropout 등 학습 전용 레이어 고정 — 변환 전 필수
    tokenizer.save_pretrained(ASSETS)

    print("[2/4] ONNX 변환 (FP32)")
    # 실제 입력과 동일한 구조의 더미 입력 — 연산 흐름을 추적해 그래프로 기록
    dummy = tokenizer("이 영화 정말 재미있어요", return_tensors="pt")
    fp32_path = ASSETS / "sentiment_fp32.onnx"
    torch.onnx.export(
        LogitsOnly(model),
        (dummy["input_ids"], dummy["attention_mask"], dummy["token_type_ids"]),
        str(fp32_path),
        input_names=["input_ids", "attention_mask", "token_type_ids"],
        output_names=["logits"],
        # 배치 크기·문장 길이를 가변 축으로 — 어떤 길이의 리뷰든 처리 가능
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq"},
            "attention_mask": {0: "batch", 1: "seq"},
            "token_type_ids": {0: "batch", 1: "seq"},
            "logits": {0: "batch"},
        },
        opset_version=17,  # 안정적 연산 지원 버전 명시
        dynamo=False,
    )

    print("[3/4] 동적 양자화 (INT8)")
    int8_path = ASSETS / "sentiment_int8.onnx"
    # onnx 내부 C++ 파일 IO가 한글 경로를 처리 못하므로 ASCII 임시 폴더에서 양자화
    with tempfile.TemporaryDirectory() as tmp:
        tmp_fp32 = Path(tmp) / "fp32.onnx"
        tmp_int8 = Path(tmp) / "int8.onnx"
        shutil.copy(fp32_path, tmp_fp32)
        quantize_dynamic(str(tmp_fp32), str(tmp_int8), weight_type=QuantType.QInt8)
        shutil.copy(tmp_int8, int8_path)

    print("[4/4] 크기 비교")
    for p in (fp32_path, int8_path):
        print(f"  {p.name}: {p.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
