/**
 * JARVIS Mobile Bridge
 * 
 * 모바일 앱과 웹 서버 간의 통신을 중개합니다.
 * - JavaScript Bridge for WebView (React Native, Flutter)
 * - Cross-platform API abstraction
 * - Real-time communication support
 */

export interface MobileConfig {
  serverUrl: string
  sharedKey: string
  enableLogging: boolean
}

export interface ChatMessage {
  id: string
  from: 'user' | 'jarvis'
  text: string
  timestamp: number
  metadata?: Record<string, any>
}

export interface JarvisResponse {
  ok: boolean
  data: {
    status: string
    message: string
    execution_steps?: any[]
    suggested_actions?: any[]
  }
}

class JarvisMobileBridge {
  private config: MobileConfig
  private baseUrl: string
  private headers: Record<string, string>
  private messageQueue: ChatMessage[] = []

  constructor(config: Partial<MobileConfig> = {}) {
    this.config = {
      serverUrl: config.serverUrl || 'http://localhost:8000',
      sharedKey: config.sharedKey || 'AIN_PAPA_SHARED_KEY',
      enableLogging: config.enableLogging ?? true,
    }

    this.baseUrl = `${this.config.serverUrl}/api`
    this.headers = {
      'Content-Type': 'application/json',
      'x-shared-key': this.config.sharedKey,
    }

    this.log('🚀 JARVIS Mobile Bridge initialized')
  }

  private log(message: string, data?: any) {
    if (this.config.enableLogging) {
      console.log(`[JARVIS Bridge] ${message}`, data || '')
    }
  }

  /**
   * 건강 체크 - 서버 연결 확인
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: this.headers,
      })
      const result = await response.json()
      this.log('✅ Health check passed', result)
      return result.ok === true
    } catch (error) {
      this.log('❌ Health check failed', error)
      return false
    }
  }

  /**
   * 채팅 메시지 전송
   */
  async sendMessage(message: string): Promise<JarvisResponse> {
    try {
      const userMsg: ChatMessage = {
        id: `msg_${Date.now()}`,
        from: 'user',
        text: message,
        timestamp: Date.now(),
      }

      // 로컬 큐에 저장
      this.messageQueue.push(userMsg)

      this.log('📤 Sending message', message)

      const response = await fetch(`${this.baseUrl}/jarvis/chat`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          message,
          mode: 'chat',
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      this.log('📥 Response received', data)

      return data
    } catch (error: any) {
      this.log('❌ Chat error', error)
      throw error
    }
  }

  /**
   * 작업 목록 조회
   */
  async getTasks() {
    try {
      const response = await fetch(`${this.baseUrl}/tasks`, {
        method: 'GET',
        headers: this.headers,
      })
      const result = await response.json()
      return result.data || []
    } catch (error) {
      this.log('❌ Get tasks error', error)
      return []
    }
  }

  /**
   * 승인 요청 목록 조회
   */
  async getApprovals() {
    try {
      const response = await fetch(`${this.baseUrl}/approvals`, {
        method: 'GET',
        headers: this.headers,
      })
      const result = await response.json()
      return result.data || []
    } catch (error) {
      this.log('❌ Get approvals error', error)
      return []
    }
  }

  /**
   * 승인 요청 승인
   */
  async approveRequest(requestId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/approvals/${requestId}/approve`, {
        method: 'POST',
        headers: this.headers,
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return await response.json()
    } catch (error) {
      this.log('❌ Approve error', error)
      throw error
    }
  }

  /**
   * 승인 요청 반려
   */
  async rejectRequest(requestId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/approvals/${requestId}/reject`, {
        method: 'POST',
        headers: this.headers,
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return await response.json()
    } catch (error) {
      this.log('❌ Reject error', error)
      throw error
    }
  }

  /**
   * 로컬 메시지 큐 조회
   */
  getLocalMessages(): ChatMessage[] {
    return [...this.messageQueue]
  }

  /**
   * 메시지 큐 초기화
   */
  clearMessageQueue() {
    this.messageQueue = []
  }

  /**
   * 설정 업데이트
   */
  updateConfig(newConfig: Partial<MobileConfig>) {
    this.config = { ...this.config, ...newConfig }
    this.baseUrl = `${this.config.serverUrl}/api`
    this.headers['x-shared-key'] = this.config.sharedKey
    this.log('⚙️ Config updated', this.config)
  }
}

// 전역 인스턴스 생성
const jarvisBridge = new JarvisMobileBridge()

// 모바일 WebView용 전역 객체
if (typeof window !== 'undefined') {
  ;(window as any).JarvisBridge = jarvisBridge
}

export default jarvisBridge
