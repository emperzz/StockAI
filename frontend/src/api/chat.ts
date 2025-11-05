import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import type { ChatMessage, ChatResponse } from '@/types/chat'

export interface ChatRequest {
  message: string
  history?: ChatMessage[]
}

export const useChatWithAgent = () => {
  return useMutation({
    mutationFn: async (params: ChatRequest) => {
      const response = await apiClient.post<ChatResponse>(
        '/chat',
        params
      )
      return response.data
    },
  })
}

