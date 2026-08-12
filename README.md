# Streamlit AI Engineering 실습 1
 
AI 엔지니어 과정을 위한 Streamlit 실습 프로젝트입니다.
기초적인 대시보드 구현부터 상태 관리, AI 모델 서빙, 그리고 FastAPI 연동을 위한 구조화 패턴까지 단계별로 학습합니다.

## 📂 폴더 구조

- **src/**: 모든 실습 소스 코드가 포함되어 있습니다.
  - `1_dashboard.py`: 레이아웃 및 데이터 시각화 기초
  - `2_tuning.py`: Form 및 Session State를 활용한 상태 관리
  - `3_model_serving.py`: 캐싱(@st.cache_resource)을 활용한 AI 모델 최적화
  - `4_app_structure.py`: 비즈니스 로직 분리 (Frontend)
    - `model_4.py`: 분리된 AI 로직 모듈 (Backend/Logic)

## ⚙️ 설치 방법

파이썬 가상환경을 생성한 후, 필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt

# 프로젝트 루트 경로에서 실행
streamlit run src/main.py
```

## 💡 참고

- docs : https://docs.streamlit.io/
- gallery : https://streamlit.io/gallery?category=favorites
- 직접 타이핑 하며 연습하기 위하여
   vscode에서 command(ctrl) + shift + p -> copilot completions disable 설정하기

- vscode에 인터넷창 띄우기
   command(ctrl) + shift + p -> simple browser:show

- 환경설정

   - 설치 : `pip install streamlit`
   - 실행 :
     - `streamlit run app.py` # 작성한 코드확인

   - 실행 코드 종료 : command + c
   
   - 파이썬 환경 관련 (별도 설치해야하는 경우)
     - venv 이용
     - python -m venv .venv
     - source .venv/bin/activate (윈도우 : myenv\Scripts\activate)
     - (.venv) pip install -r requirements
     - (.venv) python -m streamlit run streamlit_app.py
     - deactivate (비활성화)
   
   - 포트 관련 (linux/mac):
     - 실행시킬 떄 마다 포트가 누적됨
     - 포트확인 `lsof -i:{port}`
     - 포트종료 'kill -9 {pid}`
     - stream 관련 모든 pid 종료
       - `pkill -f "streamlit run"`
       - `kill -9 $(lsof -t -i :{Port})`

   - 포트 관련 (window)
     - 포트 확인 `netstat -aon | findstr :{port}`
     - 마지막 숫자 pid `Stop-Process -Id {pid} -Force`
     - `$pid = (netstat -aon | findstr :{port} | Select-String "LISTENING" | ForEach-Object { $_ -split "\s+" } | Select-Object -Last 1); if ($pid) { Stop-Process -Id $pid -Force }`

   - 포트관련 실행시 포트 고정
     - 불필요하게 포트 늘리지 말고 고정해서 사용하기
     - streamlit run app.py --server.port 8502
