import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

interface AgentSpriteProps {
  id: string
  name: string
  status: string
  color: string
  charImg: string
}

const randomPos = () => ({
  left: 15 + Math.random() * 70 + '%',
  top: 20 + Math.random() * 55 + '%'
})

export default function AgentSprite({ name, status, color, charImg }: AgentSpriteProps) {
  const [pos, setPos] = useState(randomPos())

  useEffect(() => {
    const interval = setInterval(() => {
      setPos(randomPos())
    }, 4000 + Math.random() * 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <motion.div
      animate={{ left: pos.left, top: pos.top }}
      transition={{ type: 'spring', stiffness: 15, damping: 10, mass: 1.5 }}
      style={{ position: 'absolute', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center' }}
      className="group cursor-pointer"
    >
      {/* Status Tooltip - Moved higher to avoid overlap */}
      <div className="absolute -top-14 opacity-0 group-hover:opacity-100 transition-opacity bg-black/90 text-[10px] px-2.5 py-1.5 rounded-lg border border-[#7aa2f7]/30 text-white whitespace-nowrap font-medium z-30 shadow-xl">
        {status}
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-black/90 border-r border-b border-[#7aa2f7]/30 rotate-45"></div>
      </div>

      {/* Character Sprite */}
      <div className="w-[80px] h-[100px] lg:w-[100px] lg:h-[120px] relative pixelated group-hover:scale-110 transition-transform origin-bottom float-anim">
        <img 
            src={`/static/assets/characters/single/${charImg}`} 
            className="w-full h-full object-contain filter drop-shadow(0 4px 8px rgba(0,0,0,0.5))" 
            alt={name} 
        />
        <div className="absolute top-0 right-2 w-2 h-2 rounded-full animate-pulse shadow-[0_0_8px_rgba(255,255,255,0.5)]" style={{ backgroundColor: color }}></div>
      </div>

      {/* Name Tag - More compact and clearer */}
      <div 
        className="text-[10px] font-bold mt-1.5 px-3 py-1 rounded-md border border-white/10 backdrop-blur-md shadow-lg"
        style={{ color, backgroundColor: 'rgba(26, 27, 46, 0.9)' }}
      >
        {name}
      </div>
    </motion.div>
  )
}
