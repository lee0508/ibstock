# IBStock Handoff

## 프로젝트 경로

`C:\xampp\htdocs\ibstock`

## 현재 상태

- 초기 계획 문서 작성 완료
- 로컬 시연용 FastAPI + 정적 프론트 구조 준비 완료
- YouTube Shorts 50건 수집 완료
- 정규화 -> SQLite 적재 -> FAISS 인덱스 빌드 동작 확인 완료
- `/api/health`
- `/api/stock/search`
- `/api/stock/query`
- `/api/stock/index-info`
  위 엔드포인트 구현 완료
- 검색은 `SQLite exact match + FAISS` 하이브리드
- `query` 는 Ollama 연결 시 생성형 응답, 실패 시 fallback 응답

## 우선 확인 파일

- `2026-05-10_ibstock_실행계획_v1.md`
- `LOCAL_DEMO_RUNBOOK.md`
- `backend/app/main.py`
- `backend/app/api/stocks.py`
- `backend/app/services/db.py`
- `backend/app/services/faiss_store.py`
- `backend/app/services/stock_answer.py`
- `scripts/preprocess.py`
- `scripts/init_db.py`
- `scripts/build_index.py`
- `scripts/run_local_demo.ps1`
- `scripts/run_ollama_local.ps1`

## 데이터/인덱스 산출물

- `data/raw/shorts_latest.json`
- `data/processed/shorts_normalized.json`
- `data/db/ibstock.db`
- `faiss_index/index.faiss`
- `faiss_index/metadata.json`
- `faiss_index/build_info.json`

## 로컬 실행 방법

PowerShell 창 1:

```powershell
cd C:\xampp\htdocs\ibstock
powershell -ExecutionPolicy Bypass -File .\scripts\run_ollama_local.ps1
```

PowerShell 창 2:

```powershell
cd C:\xampp\htdocs\ibstock
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_demo.ps1
```

브라우저:

```text
http://127.0.0.1:8081/frontend/index.html
```

## 현재 남은 핵심 이슈

1. 이 실행 환경에서는 백그라운드 웹서버 유지가 불안정해서, 로컬 PowerShell에서 직접 실행하는 방식으로 시연해야 함
2. Ollama 클라이언트는 설치되어 있으나, 실제 시연 시에는 `run_ollama_local.ps1` 로 서버를 먼저 띄워야 함
3. 검색 품질은 아직 규칙 기반 추출 한계가 있어 추가 정교화 필요

## 다음 우선 작업

1. 로컬 노트북에서 Ollama + 웹서버 실제 기동 검증
2. `/api/stock/query` 생성형 응답 실검증
3. 검색 품질 개선
4. 프론트 시연 UX 보강

## 새 Codex 세션 시작 프롬프트 예시

```text
프로젝트 폴더는 C:\xampp\htdocs\ibstock 입니다.
먼저 HANDOFF.md, LOCAL_DEMO_RUNBOOK.md, 2026-05-10_ibstock_실행계획_v1.md 를 읽고 현재 상태를 파악한 뒤 이어서 작업하세요.

현재 상태:
- Shorts 50건 수집 완료
- preprocess -> init_db -> build_index 동작 확인
- SQLite + FAISS 하이브리드 검색 구현 완료
- /api/stock/search, /api/stock/query, /api/stock/index-info 구현 완료
- 로컬 시연은 run_local_demo.ps1 / run_ollama_local.ps1 기준
- Ollama가 실행 중이면 query 생성형 응답, 아니면 fallback 응답

다음 우선 작업:
1. 로컬 웹서버와 Ollama 실제 기동 검증
2. query 생성형 응답 확인
3. 검색 품질 개선
4. 프론트 시연 UX 보강
```
