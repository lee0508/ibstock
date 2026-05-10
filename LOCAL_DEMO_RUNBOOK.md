# IBStock Local Demo Runbook

## 1. Ollama 실행

PowerShell 창 1:

```powershell
cd C:\xampp\htdocs\ibstock
powershell -ExecutionPolicy Bypass -File .\scripts\run_ollama_local.ps1
```

확인:

```powershell
ollama list
curl http://127.0.0.1:11434/api/tags
```

## 2. 웹서버 실행

PowerShell 창 2:

```powershell
cd C:\xampp\htdocs\ibstock
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_demo.ps1
```

접속:

```text
http://127.0.0.1:8081/frontend/index.html
```

## 3. 시연 순서

1. `상태 확인` 버튼으로 `/api/health`, `/api/stock/index-info` 확인
2. `대한전선` 검색
3. `JP모건` 검색
4. `질의 응답` 버튼으로 생성형 답변 또는 fallback 답변 확인

## 4. 현재 로컬 기준 상태

- 검색: SQLite exact match + FAISS 하이브리드
- 인덱스: `faiss_index/`
- 데이터 원본: `data/raw/shorts_latest.json`
- 정규화 결과: `data/processed/shorts_normalized.json`
- 생성형 답변: Ollama가 살아 있으면 `/api/stock/query` 에서 사용

## 5. 문제 발생 시

### Ollama 연결 실패

```powershell
curl http://127.0.0.1:11434/api/tags
```

응답이 없으면 `run_ollama_local.ps1` 창이 살아 있는지 확인한다.

### 웹페이지 접속 실패

`run_local_demo.ps1` 창에서 아래 문구가 보여야 한다.

```text
Uvicorn running on http://127.0.0.1:8081
```

### 검색 결과가 이상할 때

아래 순서로 재실행한다.

```powershell
python -X utf8 scripts\preprocess.py
python -X utf8 scripts\init_db.py
python -X utf8 scripts\build_index.py
```
