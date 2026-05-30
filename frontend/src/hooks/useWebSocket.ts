import { useEffect, useRef } from 'react';
import { WsProgressEvent, WsCompleteEvent } from '@/types/index';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useCheckProgress(
  checkId: string | null,
  onProgress: (data: WsProgressEvent) => void,
  onComplete: (data: WsCompleteEvent) => void
) {
  const onProgressRef = useRef(onProgress);
  const onCompleteRef = useRef(onComplete);
  onProgressRef.current = onProgress;
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (!checkId) return;

    // Backend: /ws/{connection_type}/{identifier}
    // connection_type = "check" for check progress
    const wsUrl = `${WS_BASE}/ws/check/${checkId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsProgressEvent | WsCompleteEvent;
        if (data.type === 'progress') {
          onProgressRef.current?.(data);
        } else if (data.type === 'complete') {
          onCompleteRef.current?.(data);
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    ws.onerror = () => console.warn('WebSocket connection error');
    ws.onclose = () => console.log('WebSocket closed');

    return () => {
      ws.close();
    };
  }, [checkId]);
}

export function useUserNotifications(
  userId: string | null,
  onNotification: (data: any) => void
) {
  const onNotificationRef = useRef(onNotification);
  onNotificationRef.current = onNotification;

  useEffect(() => {
    if (!userId) return;

    const wsUrl = `${WS_BASE}/ws/user/${userId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          onNotificationRef.current?.(data.notification);
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    ws.onerror = () => console.warn('User WS error');

    return () => ws.close();
  }, [userId]);
}