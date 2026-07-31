"""ONNX 세션·토크나이저 로더 — lifespan에서 서버 기동 시 딱 1회 호출된다.

토크나이저는 transformers(AutoTokenizer)가 아니라 경량 tokenizers 라이브러리로 로드한다.
실측: transformers 임포트+로드 ~15초 vs tokenizers ~0.1초 (토큰 ID는 완전 동일).
서빙 의존성에서 transformers를 제거해 기동 시간과 Docker 이미지를 함께 줄인다.
"""
from pathlib import Path

import onnxruntime as ort
from tokenizers import Tokenizer

MAX_LENGTH = 256


class ModelManager:
    """상태(세션·토크나이저)를 갖는 모델 관리자. 앱 전체에서 인스턴스 하나만 쓴다."""

    def __init__(self):
        self.session: ort.InferenceSession | None = None
        self.tokenizer: Tokenizer | None = None

    def load(self, model_path: str) -> None:
        assets_dir = Path(model_path).parent  # 토크나이저는 모델과 같은 폴더에 저장돼 있음
        self.tokenizer = Tokenizer.from_file(str(assets_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=MAX_LENGTH)
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])

    def unload(self) -> None:
        self.session = None
        self.tokenizer = None

    @property
    def loaded(self) -> bool:
        return self.session is not None


model_manager = ModelManager()
