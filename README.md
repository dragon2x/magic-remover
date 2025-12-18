# 🪄 Magic Watermark Remover

동영상과 PDF 문서에서 워터마크를 손쉽게 제거해주는 AI 기반 웹 애플리케이션입니다.

## 기능

1.  **동영상 워터마크 제거**
    *   원하는 구간/영역을 드래그하여 마스킹
    *   워터마크 자동 제거 및 복원 (Inpainting)

2.  **PDF 워터마크 제거**
    *   워터마크 영역 선택
    *   **자동 감지** 모드로 페이지별 배경색을 분석하여 깔끔하게 제거

## 실행 방법 (로컬)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 배포 (Streamlit Cloud)

이 프로젝트는 Streamlit Cloud에 최적화되어 있습니다.
GitHub에 코드를 업로드하고 Streamlit Cloud에 연결하면 바로 웹사이트로 사용할 수 있습니다.
