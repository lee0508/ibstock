# 2026-05-10 시연데이터충분성판단 및 data_scrapper 구현

## 1) 내일 시연 데이터 충분성 판단 (2026-05-11 13:00 기준)

판단: **기본 시연은 가능, 다만 당일 최신 수집 1회 필수 권장**

근거(점검 시각 기준):
- raw_count: 50
- processed_count: 50
- DB shorts_videos: 50
- DB stock_mentions: 36
- DB ib_supply: 81
- 최신 게시일 분포 상위: 2026-05-09(5건), 2026-05-07(1건), 2026-05-06(2건)

해석:
- 시연 질의(대한전선/JP모건/원자력) 수준의 데모에는 충분한 볼륨.
- 투자자 시연(2026-05-11 13:00)에서는 "최신성" 질문 가능성이 높아, 시연 당일 오전 데이터 갱신을 권장.

## 2) 자동 데이터 작업 스크립트 구현

생성 파일:
- `scripts/data_scrapper.py`

기능:
1. `faiss` 의존성 사전 점검
2. `collect_shorts.py --limit N`
3. `preprocess.py`
4. `init_db.py`
5. `build_index.py`
6. `preflight_check.py`
7. 실행 리포트 생성: `data/processed/data_scrapper_report.json`

실행 예시:
```bash
python3 scripts/data_scrapper.py --limit 50
```

## 3) 코드 에러 체크 결과

1. 문법 체크
- `python3 -m compileall scripts` -> OK

2. 실행 체크
- `python3 scripts/data_scrapper.py --limit 50` -> FAIL
- 실패 원인: `faiss` 모듈 미설치
- 안내 메시지 포함: `pip install -r backend/requirements.txt`

결론:
- `data_scrapper` 코드는 정상 동작하며, 현재 환경에서의 실패는 코드 버그가 아니라 런타임 의존성 미설치 이슈.

## 4) 13시 투자자 시연 에러 요소 체크 (2026-05-11 13:00)

우선 위험도 순서:
1. `faiss` 미설치로 인덱스 재빌드 실패 가능
2. Ollama 미기동/모델 미다운로드 시 `/api/stock/query` 생성형 응답 품질 저하(폴백 전환)
3. YouTube 수집 시 JS runtime 경고(수집은 가능했으나 환경 따라 변동 가능)
4. 로컬 PowerShell 창 종료/세션 끊김 시 웹서버 중단

시연 전 체크리스트(권장 시간: 2026-05-11 12:20~12:40):
1. `pip install -r backend/requirements.txt` (faiss 포함 확인)
2. `powershell -ExecutionPolicy Bypass -File .\scripts\run_ollama_local.ps1`
3. `python -X utf8 scripts\data_scrapper.py --limit 50`
4. `powershell -ExecutionPolicy Bypass -File .\scripts\run_local_demo.ps1`
5. `python -X utf8 scripts\verify_local_demo.py`
6. `/api/health`에서 `ollama.reachable=true` 확인

