/**
 * WebSocket hook for HITL communication
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

/**
 * Message types for WebSocket communication
 */
export const MessageType = {
  QUESTION: 'question',
  CLARIFICATION: 'clarification',
  RESPONSE: 'response',
  PROGRESS: 'progress',
  CLARIFICATION_REQUEST: 'clarification_request',
  ERROR: 'error',
};

/**
 * Connection states
 */
export const ConnectionState = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
};

/**
 * Custom hook for WebSocket communication with HITL support
 * @param {Object} options - Hook options
 * @param {string} options.sessionId - Optional session ID for reconnection
 * @param {Function} options.onMessage - Callback for received messages
 * @param {Function} options.onProgress - Callback for progress updates
 * @param {Function} options.onClarification - Callback for clarification requests
 * @param {Function} options.onResponse - Callback for final responses
 * @param {Function} options.onError - Callback for errors
 * @returns {Object} WebSocket state and methods
 */
export function useWebSocket({
  sessionId: initialSessionId = null,
  onMessage,
  onProgress,
  onClarification,
  onResponse,
  onError,
} = {}) {
  const [connectionState, setConnectionState] = useState(ConnectionState.DISCONNECTED);
  const [sessionId, setSessionId] = useState(initialSessionId);
  const [lastMessage, setLastMessage] = useState(null);
  const [progress, setProgress] = useState({ step: '', progress: 0 });
  const [pendingClarification, setPendingClarification] = useState(null);

  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState(ConnectionState.CONNECTING);

    const wsUrl = sessionId
      ? `${WS_BASE_URL}/ws/chat/${sessionId}`
      : `${WS_BASE_URL}/ws/chat`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState(ConnectionState.CONNECTED);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setLastMessage(message);
        handleMessage(message);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionState(ConnectionState.ERROR);
      onError?.('WebSocket 연결 오류가 발생했습니다.');
    };

    ws.onclose = () => {
      setConnectionState(ConnectionState.DISCONNECTED);
      wsRef.current = null;

      // Attempt reconnection
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current += 1;
        setTimeout(connect, 1000 * reconnectAttempts.current);
      }
    };
  }, [sessionId, onError]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionState(ConnectionState.DISCONNECTED);
    setPendingClarification(null);
    setProgress({ step: '', progress: 0 });
  }, []);

  /**
   * Handle incoming messages
   */
  const handleMessage = useCallback((message) => {
    onMessage?.(message);

    switch (message.type) {
      case MessageType.PROGRESS:
        const progressData = message.data;
        setProgress({
          step: progressData.step || '',
          progress: progressData.progress || 0,
        });
        // Extract session ID if provided
        if (progressData.session_id && !sessionId) {
          setSessionId(progressData.session_id);
        }
        onProgress?.(progressData);
        break;

      case MessageType.CLARIFICATION_REQUEST:
        setPendingClarification({
          question: message.data.question,
          options: message.data.options || [],
          allowCustomInput: message.data.allow_custom_input !== false,
        });
        onClarification?.(message.data);
        break;

      case MessageType.RESPONSE:
        setPendingClarification(null);
        setProgress({ step: '완료', progress: 1 });
        onResponse?.(message.data);
        break;

      case MessageType.ERROR:
        onError?.(message.data.error, message.data.detail);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [sessionId, onMessage, onProgress, onClarification, onResponse, onError]);

  /**
   * Send a question to the server
   * @param {string} query - The question to send
   */
  const sendQuestion = useCallback((query) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.('WebSocket이 연결되지 않았습니다.');
      return false;
    }

    const message = {
      type: MessageType.QUESTION,
      data: { query },
    };

    wsRef.current.send(JSON.stringify(message));
    setProgress({ step: '전송됨', progress: 0.05 });
    return true;
  }, [onError]);

  /**
   * Send a clarification response
   * @param {string} selectedOption - Selected option text
   * @param {string} customInput - Custom input text (if any)
   */
  const sendClarification = useCallback((selectedOption = null, customInput = null) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.('WebSocket이 연결되지 않았습니다.');
      return false;
    }

    const message = {
      type: MessageType.CLARIFICATION,
      data: {
        selected_option: selectedOption,
        custom_input: customInput,
      },
    };

    wsRef.current.send(JSON.stringify(message));
    setPendingClarification(null);
    setProgress({ step: '응답 처리 중', progress: 0.5 });
    return true;
  }, [onError]);

  /**
   * Check if connected
   */
  const isConnected = connectionState === ConnectionState.CONNECTED;

  /**
   * Check if clarification is pending
   */
  const hasPendingClarification = pendingClarification !== null;

  // Auto-connect on mount if sessionId provided
  useEffect(() => {
    if (initialSessionId) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, []);

  return {
    // State
    connectionState,
    isConnected,
    sessionId,
    lastMessage,
    progress,
    pendingClarification,
    hasPendingClarification,

    // Methods
    connect,
    disconnect,
    sendQuestion,
    sendClarification,
  };
}

export default useWebSocket;
