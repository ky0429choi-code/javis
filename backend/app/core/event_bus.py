import asyncio
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EventBus:
    """
    Singleton Event Bus for real-time internal event distribution.
    Allows Conductor and Agents to push logs to the Dashboard via SSE.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.subscribers: List[asyncio.Queue] = []
        return cls._instance

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """이벤트 발행: 모든 구독자 큐에 데이터 전달"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        logger.debug(f"EventBus Emit: {event_type}")
        
        # Dead subscriber cleanup and broadcast
        active_subscribers = []
        for queue in self.subscribers:
            try:
                queue.put_nowait(event)
                active_subscribers.append(queue)
            except asyncio.QueueFull:
                logger.warning("EventBus: Queue full, dropping event for one subscriber")
                active_subscribers.append(queue)
        self.subscribers = active_subscribers

    def subscribe(self) -> asyncio.Queue:
        """새로운 구독자 큐 생성 및 등록"""
        queue = asyncio.Queue(maxsize=100)
        self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """구독 해지"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)

event_bus = EventBus()
