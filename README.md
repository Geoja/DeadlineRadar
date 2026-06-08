# 📅 DeadlineRadar (과제 마감기한 자동 정리 프로그램)

LMS 공지나 흩어진 PDF 강의계획서 파일에서 AI를 활용하여 과제 및 시험 마감기한 정보를 자동으로 추출하고, 이를 한눈에 관리하며 구글/애플 캘린더로 내보낼 수 있는 파이썬(Streamlit) 웹 애플리케이션입니다.

---

## 🔑 Gemini API 무료 발급 안내
본 서비스는 AI 일정 분석을 위해 **Gemini API**를 사용합니다. 개인 사용은 **무료**로 발급받아 사용하실 수 있습니다.

1. **[Google AI Studio](https://aistudio.google.com/)**에 접속하여 구글 계정으로 로그인합니다.
2. 화면 상단의 **"Get API key"** 버튼을 클릭합니다.
3. **"Create API key"** 버튼을 누른 뒤, 약관에 동의하고 새 키를 생성합니다.
4. 발급된 키(예: `AIzaSy...`)를 복사하여 DeadlineRadar 웹 화면 좌측 사이드바에 입력합니다.

---

## 💻 로컬에서 실행하는 방법

### 1. 필수 프로그램 설치
* **Python 3.8 이상** 버젼이 컴퓨터에 설치되어 있어야 합니다.

### 2. 프로젝트 파일 다운로드 및 가상환경 준비 (선택사항)
터미널(PowerShell 또는 CMD)을 열고 해당 프로젝트 폴더로 이동합니다.

### 3. 필요한 패키지 설치
아래 명령어를 실행하여 필요한 라이브러리를 한 번에 설치합니다.
```bash
pip install -r requirements.txt
```

### 4. 어플리케이션 실행
설치가 완료되면 아래 명령어로 Streamlit 웹 앱을 실행합니다.
```bash
streamlit run app.py
```
* 명령어가 실행되면 브라우저에 `http://localhost:8501` 페이지가 자동으로 열립니다.

---

## 🚀 Streamlit Community Cloud에 무료로 배포하고 공유하기
기말 대체 과제 제출을 위해 완성된 웹 어플리케이션을 인터넷에 무료로 배포하여 작동하는 링크를 만드는 방법입니다.

1. **GitHub 리포지토리 생성 및 업로드**
   * 본인의 GitHub 계정에 새 저장소(Public)를 생성합니다.
   * `app.py`, `requirements.txt`, `README.md` 파일을 해당 저장소에 업로드(Push)합니다.

2. **Streamlit Community Cloud 가입 및 연동**
   * **[Streamlit Share](https://share.streamlit.io/)**에 접속하여 **"Sign in with GitHub"**를 선택하고 가입합니다.

3. **애플리케이션 배포**
   * 로그인 후 우측 상단의 **"New app"** 버튼을 누릅니다.
   * **Repository**: 생성한 GitHub 저장소를 선택합니다.
   * **Branch**: `main` 또는 `master`를 선택합니다.
   * **Main file path**: `app.py`로 입력합니다.
   * **Deploy** 버튼을 클릭합니다.

4. **링크 제출**
   * 배포가 완료되면 `https://[앱이름].streamlit.app/` 형식의 고유 주소가 생성됩니다.
   * 이 작동하는 웹 주소(또는 GitHub 리포지토리 주소)를 기말 과제 링크로 제출하시면 됩니다!
