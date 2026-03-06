---
title: Magic Remover
emoji: 🪄
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: "5.0.0"
app_file: app.py
pinned: false
---

# 🪄 매직 워터마크 제거기 (Magic Remover)

동영상과 PDF 문서에서 워터마크를 손쉽게 제거해주는 AI 기반 웹 애플리케이션입니다.

## 기능

1. **동영상 워터마크 제거**
   - 좌표 지정 후 OpenCV 인페인팅으로 자동 복원

2. **PDF 워터마크 제거**
   - 좌표 지정 후 배경색 자동 감지하여 깔끔하게 제거

## 실행 방법 (로컬)

```bash
pip install -r requirements.txt
python app.py
```

## 배포 (Hugging Face Spaces)

이 프로젝트는 Hugging Face Spaces (Gradio)에 최적화되어 있습니다.
GitHub에 코드를 업로드하고 HF Spaces에 연결하면 바로 웹사이트로 사용할 수 있습니다.
