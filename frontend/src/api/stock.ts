import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import type { StockAnalysisResult, StockData, StockInfo } from '@/types/stock'

export interface AnalyzeStockParams {
  stock_code: string
  interval: '1d' | '1m'
}

export const useAnalyzeStock = () => {
  return useMutation({
    mutationFn: async (params: AnalyzeStockParams) => {
      const response = await apiClient.post<StockAnalysisResult>(
        '/stock/analyze',
        params
      )
      return response.data
    },
  })
}

export const useGetStockInfo = (stockCode: string) => {
  return useQuery({
    queryKey: ['stock-info', stockCode],
    queryFn: async () => {
      const response = await apiClient.get<StockInfo>(`/stock/info/${stockCode}`)
      return response.data
    },
    enabled: !!stockCode,
  })
}

export const useGetStockData = (stockCode: string, interval: '1d' | '1m', days: number = 30) => {
  return useQuery({
    queryKey: ['stock-data', stockCode, interval, days],
    queryFn: async () => {
      const response = await apiClient.get<StockData[]>(
        `/stock/data/${stockCode}?interval=${interval}&days=${days}`
      )
      return response.data
    },
    enabled: !!stockCode,
  })
}

export interface MarketQuote {
  name: string
  code: string
  price: number
  change: number
  pct: number
}

// useGetIndices 已无意义，建议改用 useGetQuotes

export const useGetQuotes = (tickers: string[]) => {
  return useQuery({
    queryKey: ['market-quotes', ...tickers],
    queryFn: async () => {
      const query = encodeURIComponent(tickers.join(','))
      const response = await apiClient.get<MarketQuote[]>(`/market/quotes?tickers=${query}`)
      return response.data
    },
    enabled: Array.isArray(tickers) && tickers.length > 0,
  })
}

