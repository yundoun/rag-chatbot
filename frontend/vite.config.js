/**
 * Vite 설정 파일
 *
 * FSD(Feature-Sliced Design) 아키텍처를 위한 경로 별칭(alias) 설정
 *
 * FSD 레이어 구조:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  @app      - 앱 초기화, 프로바이더, 전역 스타일              │
 * │  @pages    - 라우트 단위 페이지 컴포넌트                    │
 * │  @widgets  - 독립적인 UI 블록 (헤더, 사이드바, 채팅패널)    │
 * │  @features - 비즈니스 로직 기능 (메시지 전송, 세션 관리)    │
 * │  @entities - 비즈니스 엔티티 (세션, 메시지)                 │
 * │  @shared   - 공유 유틸리티, UI 컴포넌트, API 클라이언트     │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 의존성 규칙: 상위 레이어 → 하위 레이어만 import 가능
 * app → pages → widgets → features → entities → shared
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      // 루트 경로
      '@': path.resolve(__dirname, './src'),

      // FSD 레이어 별칭
      '@app': path.resolve(__dirname, './src/app'),           // 앱 설정/초기화
      '@pages': path.resolve(__dirname, './src/pages'),       // 페이지 컴포넌트
      '@widgets': path.resolve(__dirname, './src/widgets'),   // 독립 UI 블록
      '@features': path.resolve(__dirname, './src/features'), // 비즈니스 기능
      '@entities': path.resolve(__dirname, './src/entities'), // 도메인 엔티티
      '@shared': path.resolve(__dirname, './src/shared'),     // 공유 리소스
    },
  },

  server: {
    port: 5173,
    // 개발 환경에서 백엔드 API 프록시 설정
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // FastAPI 백엔드 주소
        changeOrigin: true,
      },
    },
  },
})
