# 🚀 Streamlit Cloud 배포 가이드

이 가이드는 Magic Watermark Remover를 Streamlit Cloud에 배포하는 방법을 설명합니다.

## 📋 사전 준비

- [x] GitHub 계정
- [x] Streamlit Cloud 계정 (무료)
- [x] Git이 설치되어 있어야 함

## 🔧 최적화 완료 사항

이미 Streamlit Cloud 배포를 위한 최적화가 완료되었습니다:

### 1. ✅ 의존성 최적화
- `requirements.txt`: 모든 패키지 버전 명시 및 호환성 확인
- `packages.txt`: 시스템 패키지 (ffmpeg 등) 설정

### 2. ✅ 메모리 최적화
- 비디오 처리 시 메모리 사용량 감소
- `preset='ultrafast'`: 빠른 인코딩
- `threads=2`: 제한된 스레드 사용
- `bitrate='2000k'`: 낮은 비트레이트

### 3. ✅ 설정 파일
- `.streamlit/config.toml`: 최대 업로드 크기 200MB
- `.gitignore`: 불필요한 파일 제외

## 🚀 배포 단계

### 1단계: GitHub 저장소 푸시

먼저 변경사항을 Git에 커밋하고 푸시합니다:

```bash
cd f:\Antigravity\video-watermark-remover

# 변경사항 확인
git status

# 모든 변경사항 추가
git add .

# 커밋
git commit -m "Optimize for Streamlit Cloud deployment"

# GitHub에 푸시
git push origin main
```

만약 GitHub 원격 저장소가 설정되지 않았다면:

```bash
# GitHub에서 새 저장소 생성 후
git remote add origin https://github.com/YOUR_USERNAME/video-watermark-remover.git
git branch -M main
git push -u origin main
```

### 2단계: Streamlit Cloud 계정 생성

1. [Streamlit Cloud](https://share.streamlit.io/) 접속
2. **GitHub 계정으로 로그인** (Sign in with GitHub)
3. Streamlit이 GitHub 저장소에 접근할 수 있도록 권한 승인

### 3단계: 새 앱 배포

1. **"New app"** 버튼 클릭
2. 다음 정보 입력:
   - **Repository**: `YOUR_USERNAME/video-watermark-remover` 선택
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: 원하는 URL 입력 (예: `magic-watermark-remover`)

3. **"Advanced settings"** (선택사항)
   - **Python version**: `3.11` (권장)
   - **Secrets**: 필요 없음 (이 앱은 API 키 등을 사용하지 않음)

4. **"Deploy!"** 클릭

### 4단계: 배포 진행 확인

- 배포가 시작되면 로그가 실시간으로 표시됩니다
- 의존성 설치 → 앱 시작 → 완료 순서로 진행
- 보통 **5-10분** 정도 소요

### 5단계: 앱 테스트

배포가 완료되면:
1. 자동으로 앱 URL이 생성됩니다 (예: `https://magic-watermark-remover.streamlit.app`)
2. 브라우저에서 앱 접속
3. 동영상 및 PDF 업로드 테스트

## ⚠️ 주의사항 및 제한사항

### Streamlit Cloud 무료 플랜 제한

1. **리소스 제한**
   - **RAM**: 1GB (제한적)
   - **CPU**: 0.078 cores (약 8%)
   - **처리 시간**: 대용량 동영상은 시간이 오래 걸릴 수 있음

2. **파일 크기 제한**
   - **업로드**: 최대 200MB (설정됨)
   - **저장 공간**: 제한적 (임시 파일만 사용)

3. **사용 제한**
   - 앱이 **7일 동안 사용되지 않으면 자동 슬립**
   - 슬립된 앱은 첫 접속 시 재시작 (약 1분 소요)

### 권장 사항

**작은 파일 테스트:**
- 동영상: 10-30초, 720p 이하
- PDF: 10페이지 이하

**대용량 파일:**
- ngrok (로컬 터널) 사용 권장
- 또는 유료 클라우드 서비스 사용

## 🔍 문제 해결

### 배포 실패 시

1. **"Module not found" 에러**
   ```
   해결: requirements.txt에 모든 의존성이 포함되어 있는지 확인
   ```

2. **"ffmpeg not found" 에러**
   ```
   해결: packages.txt에 'ffmpeg'가 있는지 확인
   ```

3. **메모리 부족 에러**
   ```
   해결:
   - 더 작은 테스트 파일 사용
   - processor.py의 threads와 bitrate 더 낮추기
   - 유료 플랜으로 업그레이드 고려
   ```

4. **앱이 계속 재시작됨**
   ```
   해결:
   - Streamlit Cloud 로그 확인
   - app.py에서 무한 루프나 메모리 누수 확인
   ```

### 로그 확인 방법

1. Streamlit Cloud 대시보드 접속
2. 앱 선택
3. **"Manage app"** → **"Logs"** 클릭
4. 실시간 로그 및 에러 메시지 확인

## 🎯 배포 후 할 일

### 1. URL 공유
배포 완료 후 생성된 URL을 친구들에게 공유:
```
https://your-app-name.streamlit.app
```

### 2. 앱 설정 관리
- **Settings**: 앱 이름, URL 변경
- **Secrets**: API 키 등 (이 앱은 불필요)
- **Reboot**: 앱 재시작
- **Delete**: 앱 삭제

### 3. 업데이트 배포
코드를 수정한 후:
```bash
git add .
git commit -m "Update features"
git push origin main
```
- GitHub에 푸시하면 **자동으로 재배포**됩니다!

## 📊 대안 배포 옵션

Streamlit Cloud에서 계속 문제가 발생한다면:

### 1. **Render.com** (무료)
- 더 많은 리소스 (512MB RAM)
- Docker 지원
- 복잡한 설정

### 2. **Railway.app** (무료 크레딧)
- $5 무료 크레딧/월
- 더 강력한 성능
- 간단한 배포

### 3. **Hugging Face Spaces** (무료)
- Gradio 전환 필요
- GPU 옵션 (유료)
- AI/ML 앱에 최적화

### 4. **ngrok (로컬)** ⭐ 가장 확실
- 무제한 리소스 (로컬 PC 성능)
- PC만 켜두면 됨
- 이미 설정 완료됨!

## ✅ 체크리스트

배포 전 확인:

- [ ] Git 저장소가 GitHub에 푸시되었는가?
- [ ] `requirements.txt`에 모든 패키지가 있는가?
- [ ] `packages.txt`에 시스템 패키지가 있는가?
- [ ] `.streamlit/config.toml`이 생성되었는가?
- [ ] 로컬에서 `streamlit run app.py`가 잘 작동하는가?

## 💡 최종 권장사항

**친구들과만 공유하려면:**
1. **ngrok 사용** (이미 설정됨) - 가장 간단하고 확실
   - 장점: PC 성능 전부 사용, 무료, 설정 완료
   - 단점: PC 켜야 함

2. **Streamlit Cloud** - 24/7 작동
   - 장점: 항상 켜짐, 무료
   - 단점: 리소스 제한, 큰 파일 처리 어려움

**최선의 조합:**
- **일상적 사용**: ngrok (빠르고 안정적)
- **24/7 공개**: Streamlit Cloud (작은 파일 테스트용)

---

문제가 발생하면 Streamlit Cloud 로그를 확인하고, 필요시 GitHub Issues에 질문을 올려주세요!
