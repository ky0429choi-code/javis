# JARVIS v5 모바일 연동 가이드

## 📱 개요

JARVIS Agent Office는 모바일 앱과의 완전한 통합을 지원합니다.

- **웹 접근**: 브라우저에서 `http://당신의IP:8000` 으로 접속
- **API 통합**: 모바일 앱에서 REST API로 연동
- **실시간 동기화**: 작업 상태와 승인 요청 실시간 반영

---

## 🚀 빠른 시작

### 1. 서버 실행

```bash
# Windows
JARVIS.bat

# macOS/Linux
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 모바일 앱 설정

모바일 앱에서 다음 설정:
- **API Server**: `http://당신의IP:8000/api`
- **Shared Key**: `AIN_PAPA_SHARED_KEY` (또는 .env의 APP_SHARED_KEY)
- **Enable TLS**: Production에서는 HTTPS 사용

---

## 🔌 API 엔드포인트

### 기본 헤더

모든 모바일 API 요청에 다음 헤더 포함:

```http
Content-Type: application/json
x-shared-key: AIN_PAPA_SHARED_KEY
```

### 1. 모바일 정보 조회

```http
GET /api/mobile/info
```

**응답:**
```json
{
  "ok": true,
  "data": {
    "app_name": "JARVIS Agent Office",
    "version": "5.0.0",
    "status": "online",
    "endpoints": {
      "chat": "/api/jarvis/chat",
      "tasks": "/api/tasks",
      "approvals": "/api/approvals"
    }
  }
}
```

### 2. 채팅 메시지 전송

```http
POST /api/mobile/chat
Content-Type: application/json

{
  "message": "자비스, 파일을 만들어줘",
  "mode": "chat"
}
```

**응답:**
```json
{
  "ok": true,
  "data": {
    "status": "completed",
    "message": "작업이 완료되었습니다",
    "execution_steps": [
      {"step": 1, "action": "create_file", "path": "/path/to/file"},
      {"step": 2, "action": "save", "result": "success"}
    ],
    "suggested_actions": []
  }
}
```

### 3. 작업 목록 조회

```http
GET /api/tasks
```

**응답:**
```json
{
  "ok": true,
  "data": [
    {
      "id": "task_001",
      "title": "파일 생성",
      "status": "completed",
      "created_at": "2026-04-17T10:30:00Z"
    }
  ]
}
```

### 4. 승인 요청 목록

```http
GET /api/approvals
```

**응답:**
```json
{
  "ok": true,
  "data": [
    {
      "id": "apr_001",
      "title": "파일 삭제 승인",
      "description": "/data/old_file.txt 삭제",
      "status": "pending",
      "created_at": "2026-04-17T10:31:00Z"
    }
  ]
}
```

### 5. 승인 요청 승인

```http
POST /api/approvals/{requestId}/approve
```

### 6. 승인 요청 반려

```http
POST /api/approvals/{requestId}/reject
```

### 7. 상태 조회

```http
GET /api/mobile/status
```

**응답:**
```json
{
  "ok": true,
  "data": {
    "timestamp": 1713348600.0,
    "active_tasks": 2,
    "pending_approvals": 1,
    "system_ready": true
  }
}
```

---

## 💻 모바일 브릿지 라이브러리

### TypeScript/JavaScript 사용

모바일 WebView에서 JavaScript Bridge 사용:

```javascript
// 1. 헬스 체크
const isHealthy = await JarvisBridge.checkHealth()

// 2. 채팅 전송
const response = await JarvisBridge.sendMessage("자비스, 안녕하세요")

// 3. 작업 조회
const tasks = await JarvisBridge.getTasks()

// 4. 승인 요청 조회
const approvals = await JarvisBridge.getApprovals()

// 5. 승인 처리
await JarvisBridge.approveRequest('apr_001')
```

### 설정

```javascript
// 커스텀 서버 설정
JarvisBridge.updateConfig({
  serverUrl: 'http://192.168.1.100:8000',
  sharedKey: 'your-shared-key',
  enableLogging: true
})
```

---

## 📲 모바일 앱 구현 예시

### React Native

```tsx
import { useEffect, useState } from 'react'
import { View, Text, TextInput, Button, FlatList } from 'react-native'

export default function ChatScreen() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')

  const sendMessage = async () => {
    try {
      const response = await fetch('http://SERVER_IP:8000/api/mobile/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-shared-key': 'AIN_PAPA_SHARED_KEY'
        },
        body: JSON.stringify({ message: input, mode: 'chat' })
      })
      
      const data = await response.json()
      if (data.ok) {
        setMessages([...messages, {
          id: Date.now(),
          from: 'jarvis',
          text: data.data.message
        }])
      }
    } catch (err) {
      console.error('Chat error:', err)
    }
    setInput('')
  }

  return (
    <View>
      <FlatList 
        data={messages}
        renderItem={({item}) => <Text>{item.text}</Text>}
      />
      <TextInput value={input} onChangeText={setInput} />
      <Button title="Send" onPress={sendMessage} />
    </View>
  )
}
```

### Flutter

```dart
import 'package:http/http.dart' as http;

class JarvisService {
  static const String baseUrl = 'http://YOUR_SERVER_IP:8000/api';
  static const String sharedKey = 'AIN_PAPA_SHARED_KEY';

  static Future<void> sendMessage(String message) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/mobile/chat'),
        headers: {
          'Content-Type': 'application/json',
          'x-shared-key': sharedKey,
        },
        body: jsonEncode({
          'message': message,
          'mode': 'chat',
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('Response: ${data['data']['message']}');
      }
    } catch (e) {
      print('Error: $e');
    }
  }
}
```

---

## 🔒 보안

### 프로덕션 배포

```bash
# HTTPS 필수
# .env에서 설정
APP_ENV=production
APP_SHARED_KEY=change-me-to-secure-key
```

### 모바일 앱 서명

- Android: Keystore로 앱 서명
- iOS: Apple Developer Certificate로 서명

---

## 🌐 네트워크 설정

### 로컬 네트워크

모바일과 PC가 같은 WiFi에 연결된 경우:

```bash
# PC IP 주소 확인 (Windows)
ipconfig

# 모바일에서 접속
http://192.168.x.x:8000
```

### 원격 접속

공인 IP 또는 도메인 필요:

```bash
# ngrok 사용 (개발용)
ngrok http 8000
# https://xxxx-xx-xxx-xxx-xx.ngrok.io
```

---

## 📊 실시간 동기화

### WebSocket (곧 지원)

```javascript
// 예정된 기능
const ws = new WebSocket('wss://localhost:8000/ws/mobile')

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log('Real-time update:', data)
}
```

---

## 🐛 디버깅

### 로깅 활성화

```javascript
JarvisBridge.updateConfig({ enableLogging: true })
```

### API 문서 확인

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

---

## 📝 문제 해결

### 연결 실패

1. 방화벽 확인: 포트 8000 열려있는지 확인
2. 서버 상태: `http://SERVER_IP:8000/api/health` 확인
3. 공유 키: APP_SHARED_KEY 일치하는지 확인

### 응답 오류

```json
{
  "ok": false,
  "data": {
    "error": "Shared key not provided or invalid"
  }
}
```

→ 요청 헤더의 `x-shared-key` 확인

---

## 📚 추가 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [React Native 문서](https://reactnative.dev/)
- [Flutter 문서](https://flutter.dev/)

---

마지막 업데이트: 2026-04-17
