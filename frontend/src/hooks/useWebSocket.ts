import { useEffect, useRef } from 'react';

export function useCheckProgress(
  checkId: string | null,
  onProgress: (data: any) => void,
  onComplete: (data: any) => void
) {
  const onProgressRef = useRef(onProgress);
  const onCompleteRef = useRef(onComplete);
  onProgressRef.current = onProgress;
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (!checkId) return;

    const wsUrl = `ws://localhost:8000/ws/${checkId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'progress') {
        onProgressRef.current?.(data);
      } else if (data.type === 'complete') {
        onCompleteRef.current?.(data);
      }
    };

    ws.onerror = (err) => console.error('WebSocket error:', err);

    return () => ws.close();
  }, [checkId]);
}