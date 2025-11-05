export interface StockPrice {
  timestamp: string
  open_price?: number
  close_price?: number
  high_price?: number
  low_price?: number
  volume?: number
  amount?: number
  price?: number
}

export interface StockData {
  日期: string
  开盘: number | null
  收盘: number | null
  最高: number | null
  最低: number | null
  成交量: number | null
  成交额: number | null
}

export interface StockAnalysisResult {
  analysis_text: string
  data_table: StockData[]
  chart_data?: {
    dates: string[]
    stocks: {
      code: string
      returns: number[]
    }[]
  }
}

export interface StockInfo {
  [key: string]: string | number
}

