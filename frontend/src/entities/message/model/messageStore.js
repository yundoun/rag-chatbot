import { create } from 'zustand'

export const useMessageStore = create((set, get) => ({
  isLoading: false,
  currentStep: null,
  completedSteps: [],
  pendingClarification: null,
  backendSessionId: null,

  setLoading: (isLoading) => set({ isLoading }),

  setCurrentStep: (step) => set({ currentStep: step }),

  addCompletedStep: (step) => set(state => ({
    completedSteps: [...state.completedSteps, step]
  })),

  resetSteps: () => set({
    currentStep: null,
    completedSteps: [],
  }),

  setPendingClarification: (clarification) => set({
    pendingClarification: clarification
  }),

  clearClarification: () => set({ pendingClarification: null }),

  setBackendSessionId: (sessionId) => set({ backendSessionId: sessionId }),

  reset: () => set({
    isLoading: false,
    currentStep: null,
    completedSteps: [],
    pendingClarification: null,
    backendSessionId: null,
  }),
}))
