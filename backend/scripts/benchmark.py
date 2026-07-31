"""경량화 전/후 3단 비교 벤치마크: PyTorch FP32 vs ONNX FP32 vs ONNX INT8.

측정 원칙 (학습 자료 기반):
  - 워밍업 10회 (통계 제외) → 본 측정 100회
  - 평균 ± 표준편차 + P99 레이턴시 보고
  - E2E 측정: 토크나이즈 → 추론 → softmax 전 구간
  - 정확도: 라벨링된 검증 문장으로 엔진별 정답률 + FP32↔INT8 판정 일치율

실행: backend/ 에서  python scripts/benchmark.py
산출: ml_assets/benchmark_results.json (보고서용)
"""
import json
import statistics
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_ID = "daekeun-ml/koelectra-small-v3-nsmc"
ASSETS = Path(__file__).resolve().parent.parent / "ml_assets"
WARMUP, RUNS = 10, 100
BENCH_TEXT = "배우들의 연기가 정말 훌륭하고 스토리도 탄탄해서 시간 가는 줄 모르고 봤습니다."

# 검증 문장 (label: 1=긍정, 0=부정) — 영화 리뷰 도메인
EVAL_SET = [
    ("인생 영화입니다. 벌써 세 번째 보는데 볼 때마다 감동이에요.", 1),
    ("연출, 연기, 음악 뭐 하나 빠지는 게 없는 완벽한 작품.", 1),
    ("기대 없이 봤는데 완전 몰입해서 봤어요. 강추합니다!", 1),
    ("배우들 연기가 미쳤다. 특히 주연배우 표정 연기 소름.", 1),
    ("잔잔하지만 여운이 오래 남는 영화. 가족과 함께 보기 좋아요.", 1),
    ("올해 본 영화 중 최고. 엔딩 크레딧까지 자리를 못 떴다.", 1),
    ("스토리가 신선하고 반전도 훌륭했다. 두 번 봐도 재밌을 듯.", 1),
    ("영상미가 압도적이라 영화관에서 보길 잘했다는 생각이 들었다.", 1),
    ("시간 낭비였습니다. 중간에 나가고 싶었어요.", 0),
    ("스토리가 엉망이고 개연성이 하나도 없다.", 0),
    ("돈 아까운 영화. 예고편이 전부입니다.", 0),
    ("배우 연기가 어색해서 몰입이 안 됐다.", 0),
    ("지루해서 졸았습니다. 비추천해요.", 0),
    ("기대했는데 실망만 안겨준 작품. 후반부는 억지 전개.", 0),
    ("편집이 산만하고 대사도 유치하다. 최악이었다.", 0),
    ("이걸 영화라고 만들었나 싶다. 별 반 개도 아깝다.", 0),
]


def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()


def make_engines(tokenizer):
    """엔진별 predict(text) -> 긍정확률 함수를 만들어 반환."""
    pt_model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    pt_model.eval()

    def pt_predict(text):
        enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            logits = pt_model(**enc).logits[0].numpy()
        return softmax(logits)[1]

    def ort_predict_factory(onnx_path):
        sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

        def predict(text):
            enc = tokenizer(text, return_tensors="np", truncation=True, max_length=256)
            logits = sess.run(
                None,
                {
                    "input_ids": enc["input_ids"].astype(np.int64),
                    "attention_mask": enc["attention_mask"].astype(np.int64),
                    "token_type_ids": enc["token_type_ids"].astype(np.int64),
                },
            )[0][0]
            return softmax(logits)[1]

        return predict

    return {
        "PyTorch FP32": (pt_predict, None),
        "ONNX FP32": (ort_predict_factory(ASSETS / "sentiment_fp32.onnx"), ASSETS / "sentiment_fp32.onnx"),
        "ONNX INT8": (ort_predict_factory(ASSETS / "sentiment_int8.onnx"), ASSETS / "sentiment_int8.onnx"),
    }


def bench(predict):
    for _ in range(WARMUP):  # 워밍업 — 초기화 오버헤드 제거, 통계 미포함
        predict(BENCH_TEXT)
    latencies = []
    for _ in range(RUNS):
        t0 = time.perf_counter()
        predict(BENCH_TEXT)
        latencies.append((time.perf_counter() - t0) * 1000)
    latencies.sort()
    return {
        "mean_ms": round(statistics.mean(latencies), 2),
        "std_ms": round(statistics.stdev(latencies), 2),
        "p99_ms": round(latencies[int(RUNS * 0.99) - 1], 2),
    }


def accuracy(predict):
    preds = [1 if predict(t) >= 0.5 else 0 for t, _ in EVAL_SET]
    correct = sum(p == y for p, (_, y) in zip(preds, EVAL_SET))
    return correct / len(EVAL_SET), preds


def main():
    tokenizer = AutoTokenizer.from_pretrained(ASSETS)  # export 때 저장한 로컬 토크나이저
    engines = make_engines(tokenizer)

    results, preds_by_engine = {}, {}
    for name, (predict, path) in engines.items():
        print(f"== {name} 측정 중 (워밍업 {WARMUP} + 본측정 {RUNS}회)")
        r = bench(predict)
        acc, preds = accuracy(predict)
        preds_by_engine[name] = preds
        size_mb = round(path.stat().st_size / 1024 / 1024, 1) if path else round(
            sum(p.numel() for p in AutoModelForSequenceClassification.from_pretrained(MODEL_ID).parameters()) * 4 / 1024 / 1024, 1
        )
        results[name] = {**r, "accuracy": acc, "size_mb": size_mb}

    agree = sum(
        a == b for a, b in zip(preds_by_engine["ONNX FP32"], preds_by_engine["ONNX INT8"])
    ) / len(EVAL_SET)

    print(f"\n{'엔진':<14} {'평균(ms)':>9} {'표준편차':>8} {'P99(ms)':>9} {'정확도':>7} {'크기(MB)':>9}")
    for name, r in results.items():
        print(f"{name:<14} {r['mean_ms']:>9} {r['std_ms']:>8} {r['p99_ms']:>9} {r['accuracy']:>7.2%} {r['size_mb']:>9}")
    print(f"\nFP32 ↔ INT8 판정 일치율: {agree:.2%}  (검증 문장 {len(EVAL_SET)}개)")

    out = ASSETS / "benchmark_results.json"
    out.write_text(
        json.dumps({"results": results, "fp32_int8_agreement": agree,
                    "warmup": WARMUP, "runs": RUNS, "eval_size": len(EVAL_SET)},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"저장: {out}")


if __name__ == "__main__":
    main()
