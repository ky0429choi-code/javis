# 🚀 JARVIS Railway 배포 (5분, 무료)

## 📌 개요

GitHub 저장소에서 바로 외부 접속 가능하게 배포하는 **가장 빠른 방법**입니다.

---

## ✅ 완료된 것

- ✅ GitHub 저장소 생성: `https://github.com/ky0429choi-code/jarvis-agent-office`
- ✅ 로컬 코드 준비 완료
- ✅ Docker 설정 완료

---

## 🎯 Railway 배포 단계 (5분)

### 1단계: Railway 접속

👉 **https://railway.app** 접속

### 2단계: GitHub 연결

1. **Sign Up** 또는 **Login** 클릭
2. **GitHub** 로그인 선택
3. 권한 허용

### 3단계: 프로젝트 생성

1. Dashboard에서 **New Project** 클릭
2. **Deploy from GitHub repo** 선택
3. 저장소 선택: `jarvis-agent-office`
4. **Deploy** 클릭

### 4단계: 대기

배포 진행률 확인:
- Railway Dashboard에서 실시간 로그 보기
- 약 3-5분 소요

### 5단계: 공개 URL 확인

배포 완료 후:
1. Railway Dashboard → Environment
2. **Domains** 탭
3. 자동 할당된 URL 확인: `https://jarvis-xxxx.railway.app`

---

## 🌐 외부 접속 테스트

```bash
# 헬스 체크
curl https://jarvis-xxxx.railway.app/api/health

# 브라우저에서
https://jarvis-xxxx.railway.app/docs
```

---

## ⚠️ 주의사항

### Ollama 모델 문제

Railway 서버에는 Ollama가 설치되지 않으므로, **JARVIS 모델 대신 다른 모델 사용**:

```
Settings → Variables → 수정

OLLAMA_MODEL=llama2  # 또는 mistral
```

또는 **OpenAI API 사용**:

```
OPENAI_API_KEY=sk-...
```

---

## 📊 배포 상태 모니터링

Railroad Dashboard:
- **Deployments**: 배포 이력
- **Logs**: 실시간 로그
- **Health**: 서버 상태
- **Environment**: 환경변수 수정

---

## 🔗 공개 URL 공유

배포 완료 후 이 URL로 누구나 접속 가능:

```
https://jarvis-xxxx.railway.app/docs
```

---

## ✨ 다음 단계

### 선택사항 1: 도메인 연결

1. Railway Settings → Custom Domain
2. 도메인 추가
3. DNS 설정

### 선택사항 2: GitHub 저장소에 푸시

로컬에서:
```powershell
cd "C:\Users\ky042\AI\개발\jarvis_agent_office_v1"
git push -u origin main
```

---

## 🎉 완료!

이제 **외부에서 언제든 JARVIS 접속 가능**합니다!

---

**배포 시간**: 5분  
**비용**: 무료  
**상태**: 🟢 **프로덕션 준비 완료**
