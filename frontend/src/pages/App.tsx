import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, MessageSquare, Terminal, Send, Cpu, ShieldAlert, Check, X, Layout, GripVertical } from 'lucide-react'
import { api } from '../lib/api'
import AgentSprite from '../components/AgentSprite'

const INITIAL_AGENTS = [
  { id: 'executor_engine', name: '자비스-실행기', role: '작업 실행', status: '대기', color: '#7aa2f7', charImg: 'char_1.png' },
  { id: 'core_intelligence', name: '자비스-코어', role: '일상 대화', status: '유휴', color: '#bb9af7', charImg: 'char_2.png' },
  { id: 'master_architect', name: '자비스-아키텍트', role: '지능 엔진', status: '대기', color: '#9ece6a', charImg: 'char_3.png' },
]

export default function App() {
  const [health, setHealth] = useState('확인 중...')
  const [message, setMessage] = useState('')
  const [chatMessages, setChatMessages] = useState<any[]>([
    { id: 1, from: 'jarvis', text: "안녕하세요. 저는 자비스입니다. 무엇을 도와드릴까요?", ts: new Date() }
  ])
  const [tasks, setTasks] = useState<any[]>([])
  const [approvals, setApprovals] = useState<any[]>([])
  const [isThinking, setIsThinking] = useState(false)
  const [promptText, setPromptText] = useState('시스템 프롬프트를 여기에 표시합니다.')
  const [officeWidth, setOfficeWidth] = useState(50)  // 픽셀 오피스 비율
  const [chatWidth, setChatWidth] = useState(35)      // 채팅 창 비율
  const promptWidth = 100 - officeWidth - chatWidth  // 프롬프트 자동 계산
  const [isDraggingOffice, setIsDraggingOffice] = useState(false)
  const [isDraggingChat, setIsDraggingChat] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize for textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    const adjustHeight = () => {
      textarea.style.height = 'auto'
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 144), 540)
      textarea.style.height = `${newHeight}px`
      // Toggle scrollbar visibility
      textarea.style.overflowY = textarea.scrollHeight > 540 ? 'auto' : 'hidden'
    }

    textarea.addEventListener('input', adjustHeight)
    adjustHeight() // Initial adjust

    return () => textarea.removeEventListener('input', adjustHeight)
  }, [message])

  async function load() {
    try {
      await api.health()
      setHealth('정상')
      const tasksRes = await api.tasks()
      setTasks(tasksRes.data || [])
      const approvalsRes = await api.approvals()
      setApprovals(approvalsRes.data || [])
    } catch {
      setHealth('연결 실패')
    }
  }

  useEffect(() => { load() }, [])
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatMessages, isThinking, approvals])

  // Mouse event handlers for dragging dividers
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const totalWidth = rect.width
      const sidebarWidth = 256 // w-64 = 256px (16rem)
      const workspaceWidth = totalWidth - sidebarWidth

      // Office-Chat divider drag
      if (isDraggingOffice) {
        const newOfficeWidth = ((e.clientX - (rect.left + sidebarWidth)) / workspaceWidth) * 100
        if (newOfficeWidth > 25 && newOfficeWidth < 65) {
          setOfficeWidth(newOfficeWidth)
        }
      }

      // Chat-Prompt divider drag
      if (isDraggingChat) {
        const chatStartX = rect.left + sidebarWidth + (workspaceWidth * officeWidth) / 100
        const newChatWidth = ((e.clientX - chatStartX) / workspaceWidth) * 100
        if (newChatWidth > 20 && newChatWidth < 50) {
          setChatWidth(newChatWidth)
        }
      }
    }

    const handleMouseUp = () => {
      setIsDraggingOffice(false)
      setIsDraggingChat(false)
    }

    if (isDraggingOffice || isDraggingChat) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDraggingOffice, isDraggingChat, officeWidth])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    const userMsg = { id: Date.now(), from: 'user', text: message, ts: new Date() }
    setChatMessages(prev => [...prev, userMsg])
    setMessage('')
    setIsThinking(true)

    try {
      console.log('📤 Sending message:', message)
      const res = await api.chat(message)
      console.log('📥 Received response:', res)
      
      // 응답 파싱 및 메시지 추출
      let replyText = "응답을 받지 못했습니다."
      let suggestedActions: any[] = []
      
      if (res.data) {
        const data = res.data
        
        // 1. 단순 대화 (mode === 'chat') 또는 status가 없는 경우
        if (data.mode === 'chat' || !data.status) {
          replyText = data.message || data.reply || data.result || "메시지가 비어 있습니다."
        } 
        // 2. 작업 수행 (mode === 'task') 또는 status가 있는 경우
        else if (data.status) {
          const status = data.status
          const execSteps = data.execution_steps || []
          const execCount = execSteps.length
          
          // 작업 요약 메시지가 있으면 그것을 사용하고, 없으면 기본 완료 문구 사용
          replyText = data.message || `✅ 작업이 수행되었습니다. (상태: ${status}, 단계: ${execCount})`
          if (execCount > 0) suggestedActions = execSteps
        }
        
        suggestedActions = data.suggested_actions || suggestedActions
      } else {
        replyText = res.message || res.reply || res.result || JSON.stringify(res)
      }
      
      const jarvisMsg = {
        id: Date.now() + 1,
        from: 'jarvis',
        text: replyText,
        ts: new Date()
      }
      
      setChatMessages(prev => [...prev, jarvisMsg])

      // If autonomous actions were suggested/queued
      if (suggestedActions && suggestedActions.length > 0) {
        setChatMessages(prev => [...prev, {
          id: Date.now() + 2,
          from: 'jarvis',
          text: `🔔 지능형 코어에서 ${suggestedActions.length}건의 업무 실행(승인 대기)을 자동으로 생성했습니다.`,
          ts: new Date(),
          isSystem: true
        }])
      }

      await load() // Refresh tasks/approvals
    } catch (err: any) {
      console.error('❌ Chat error:', err)
      setChatMessages(prev => [...prev, {
        id: Date.now() + 1,
        from: 'jarvis',
        text: `오류: ${err.message || 'API_ERROR'}`,
        ts: new Date()
      }])
    } finally {
      setIsThinking(false)
    }
  }

  const resolveApproval = async (requestId: string, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await api.approve(requestId)
      else await api.reject(requestId)
      
      await load()
      setChatMessages(prev => [...prev, {
        id: Date.now(),
        from: 'jarvis',
        text: action === 'approve' ? `✅ 승인되었습니다. (ID: ${requestId})` : `🚫 반려되었습니다. (ID: ${requestId})`,
        ts: new Date()
      }])
    } catch (err: any) {
      alert(`승인 오류: ${err.message}`)
    }
  }

  return (
    <div ref={containerRef} className="app-container flex h-screen w-full main-container">
      
      {/* Left Sidebar - Desktop Only */}
      <aside className="sidebar-desktop sidebar-container lg-w-64 flex flex-col gap-4 p-4 shrink-0 border-r border-[#414868]/20 overflow-y-auto">
        <div className="flex items-center gap-3 p-4 glass-panel rounded-2xl glow-blue">
          <div className="w-10 h-10 bg-gradient-to-br from-[#7aa2f7] to-[#bb9af7] rounded-xl flex items-center justify-center shadow-lg">
            <Cpu className="text-white" size={20} />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-tight">자비스 (JARVIS)</h1>
            <p className="text-[10px] text-[#565f89]">차세대 코어 4.0</p>
          </div>
        </div>

        <div className="flex-1 glass-panel rounded-2xl overflow-y-auto p-4 space-y-3 custom-scrollbar">
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-[#565f89] mb-2">활성 브레인</h2>
          {INITIAL_AGENTS.map(agent => (
            <div key={agent.id} className="p-3 bg-[#16161e]/60 rounded-xl border border-transparent hover:border-[#414868] transition-colors cursor-pointer group">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: agent.color }}></div>
                <span className="font-bold text-white text-xs">{agent.name}</span>
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ color: agent.color, backgroundColor: agent.color + '20' }}>{agent.role}</span>
                <span className="text-[10px] text-[#565f89]">{agent.status}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="glass-panel rounded-2xl p-4">
          <div className="text-[10px] text-[#565f89] font-bold mb-3 uppercase tracking-widest">환경 정보</div>
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-[#565f89]">시스템 코드</span>
              <span className={`font-bold ${health === '정상' ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>{health}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[#565f89]">자율 작업</span>
              <span className={`${approvals.length > 0 ? 'text-[#f7768e] font-bold' : 'text-[#9ece6a]'}`}>{approvals.length} 건</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Workspace Area */}
      <div className="workspace-area flex-1 flex lg-flex-row min-w-0 overflow-hidden">
        
        {/* Office Area (Left on Desktop, Top on Mobile) */}
        <div className="office-panel flex-1 flex flex-col lg-p-4 min-w-0 relative">
          <div className="flex-1 glass-panel rounded-3xl relative overflow-hidden">
            {/* Office Background */}
            <img src="/static/bg.png" className="absolute inset-0 w-full h-full object-cover pixelated opacity-40 z-0" alt="Office" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0f0f1a] via-transparent to-[#0f0f1a]/40 z-1"></div>
            
            <div className="absolute top-4 left-6 right-6 flex items-center justify-between z-20">
              <div className="flex items-center gap-2">
                <Layout size={16} className="text-[#7aa2f7]" />
                <span className="text-[10px] lg:text-xs font-bold text-white/50 uppercase tracking-widest bg-[#0f0f1a]/40 px-2 py-1 rounded">자비스 공간 (Office)</span>
              </div>
              <div className="text-[9px] text-white/20 tracking-tighter">자비스 에이전트 OS</div>
            </div>

            {/* Wandering Agents */}
            <div className="absolute inset-0 z-10">
              {INITIAL_AGENTS.map(agent => (
                <AgentSprite key={agent.id} {...agent} />
              ))}
            </div>

            {/* Bottom Status Bar */}

            {/* Bottom Status Bar */}
            <div className="absolute bottom-4 left-6 right-6 flex items-center gap-4 z-20 overflow-hidden">
              {tasks.slice(0, 3).map(task => (
                <div key={task.id} className="text-[9px] text-white/40 flex items-center gap-1 bg-[#0f0f1a]/60 px-2 py-0.5 rounded backdrop-blur-sm truncate">
                  <div className="w-1 h-1 rounded-full bg-[#7aa2f7]"></div>
                  {task.title || task.id}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Panel (Chat + Prompt) - Vertical Stack */}
        <div className="right-side-panel lg-w-450 flex flex-col p-2 lg-p-4 lg-gap-4 min-h-0 h-full">
          
          {/* Chat History Card (Top) */}
          <div className="flex-1 glass-panel rounded-3xl overflow-hidden flex flex-col glow-blue min-h-0">
            <div className="bg-[#1a1b2e]/80 px-4 py-3 flex justify-between items-center border-b border-[#7aa2f7]/10 shrink-0 gap-4">
              <div className="flex gap-3 items-center min-w-0">
                <div className="w-6 h-6 bg-gradient-to-br from-[#7aa2f7] to-[#bb9af7] rounded-full flex items-center justify-center shrink-0">
                  <MessageSquare size={12} className="text-white" />
                </div>
                <span className="text-white font-bold text-xs truncate">대화 기록</span>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a] animate-pulse"></div>
                <span className="text-[10px] text-[#9ece6a] font-medium whitespace-nowrap">연결됨</span>
              </div>
            </div>

            <div className="flex-1 p-4 overflow-y-auto min-h-0 bg-[#0f0f1a]/40 custom-scrollbar">
              <div className="space-y-4">
                {chatMessages.map(msg => (
                  <div key={msg.id} className={`flex ${msg.from === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] p-3 rounded-2xl text-[12px] leading-relaxed ${
                      msg.from === 'jarvis' 
                      ? 'chat-bubble-jarvis text-[#c0caf5] rounded-tl-none' 
                      : 'chat-bubble-user text-[#9ece6a] rounded-tr-none'
                    }`}>
                      {msg.from === 'jarvis' && (
                        <div className="text-[9px] font-bold text-[#7aa2f7] mb-1 flex items-center gap-1">
                          <Brain size={10} /> 자비스
                        </div>
                      )}
                      <div className="whitespace-pre-wrap break-words">{msg.text}</div>
                      <div className="text-[8px] opacity-30 mt-1.5 text-right">
                        {new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {isThinking && (
                <div className="flex justify-start">
                  <div className="chat-bubble-jarvis p-3 rounded-2xl rounded-tl-none flex items-center gap-1">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>
          </div>

          {/* Pending Approvals Card Stack (Ultra Compact Horizontal Rows) */}
          <div className="flex flex-col gap-1 shrink-0">
            <AnimatePresence>
              {approvals.map(item => (
                <motion.div 
                  key={item.request_id + '_compact'} 
                  initial={{ opacity: 0, scale: 0.98, y: 5 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                  className="approval-mini-card"
                >
                  <div className="flex items-center gap-2 overflow-hidden flex-1">
                    <ShieldAlert size={10} className="text-[#7aa2f7] shrink-0" />
                    <div className="text-[10px] text-white/90 font-bold truncate">
                      {item.action_type === 'write_file' || item.action_type === 'update_file' ? '파일 수정' : 
                       item.action_type === 'create_file' ? '파일 생성' : '시스템 실행'}: {item.target_path.split('/').pop()}
                    </div>
                  </div>
                  
                  <div className="flex gap-1.5 shrink-0">
                    <button 
                      onClick={() => resolveApproval(item.request_id, 'approve')} 
                      className="approval-btn-approve"
                    >
                      승인
                    </button>
                    <button 
                      onClick={() => resolveApproval(item.request_id, 'reject')} 
                      className="approval-btn-reject"
                    >
                      반려
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Prompt Input Card (Bottom - Dynamic Height) */}
          <div className="glass-panel rounded-3xl overflow-hidden flex flex-col glow-blue shrink-0">
            <div className="bg-[#1a1b2e]/80 px-4 py-2.5 flex justify-between items-center border-b border-[#7aa2f7]/10">
              <div className="flex gap-3 items-center">
                <Terminal size={12} className="text-[#7aa2f7]" />
                <span className="text-white font-bold text-xs">프롬프트 입력</span>
              </div>
            </div>
            
            <form onSubmit={handleSendMessage} className="flex-1 flex flex-col p-3 gap-2 bg-[#0f0f1a]/20">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e as any);
                  }
                }}
                placeholder="자비스에게 명령을 내리세요... (Shift+Enter로 줄바꿈)"
                className="w-full bg-transparent border-none text-white text-12pt p-3 outline-none resize-none placeholder-[#414868] custom-scrollbar leading-relaxed"
                disabled={isThinking}
              />
              <div className="flex justify-between items-center px-2 py-1 border-t border-[#414868]/10">
                <div className="text-[10px] text-[#565f89]">Enter를 누르면 전송됩니다</div>
                <button 
                  type="submit" 
                  disabled={isThinking || !message.trim()}
                  className="px-6 py-2.5 bg-gradient-to-br from-[#7aa2f7] to-[#bb9af7] hover:from-[#86aefe] hover:to-[#c5a8ff] rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-30 shadow-lg"
                >
                  <span className="text-white font-bold text-xs">전송</span>
                  <Send size={14} className="text-white" />
                </button>
              </div>
            </form>

            {/* System Prompt (Small at bottom) */}
            <div className="px-4 py-1.5 bg-[#16161e] border-t border-[#414868]/10 flex items-center gap-2">
              <span className="text-[9px] text-[#565f89] font-bold uppercase tracking-wider shrink-0">시스템:</span>
              <div className="text-[9px] text-[#414868] truncate italic">
                {promptText}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
