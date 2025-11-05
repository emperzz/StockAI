import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'

interface StockChartProps {
  data: {
    dates: string[]
    stocks: {
      code: string
      returns: number[]
    }[]
  }
}

export default function StockChart({ data }: StockChartProps) {
  const option = useMemo(() => {
    const isDark = document.documentElement.classList.contains('dark') || 
                   window.matchMedia('(prefers-color-scheme: dark)').matches
    
    const textColor = isDark ? '#e5e7eb' : '#1f2937'
    const mutedColor = isDark ? '#9ca3af' : '#6b7280'
    
    const colors = [
      '#3b82f6', // blue
      '#10b981', // green
      '#f59e0b', // amber
      '#ef4444', // red
      '#8b5cf6', // purple
      '#ec4899', // pink
    ]
    
    const series = data.stocks.map((stock, index) => ({
      name: stock.code,
      type: 'line',
      data: stock.returns,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        width: 2,
      },
      itemStyle: {
        color: colors[index % colors.length],
      },
    }))

    return {
      title: {
        text: '多股票相对涨跌幅（首日=0%）',
        left: 'center',
        textStyle: {
          color: textColor,
          fontSize: 16,
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        backgroundColor: isDark ? 'rgba(31, 41, 55, 0.9)' : 'rgba(255, 255, 255, 0.9)',
        borderColor: isDark ? '#374151' : '#e5e7eb',
        textStyle: {
          color: textColor,
        },
      },
      legend: {
        data: data.stocks.map((s) => s.code),
        top: 30,
        textStyle: {
          color: textColor,
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.dates,
        axisLabel: {
          color: mutedColor,
          rotate: 45,
        },
        axisLine: {
          lineStyle: {
            color: mutedColor,
          },
        },
      },
      yAxis: {
        type: 'value',
        name: '涨跌幅（%）',
        axisLabel: {
          formatter: '{value}%',
          color: mutedColor,
        },
        nameTextStyle: {
          color: textColor,
        },
        axisLine: {
          lineStyle: {
            color: mutedColor,
          },
        },
        splitLine: {
          lineStyle: {
            color: isDark ? '#374151' : '#e5e7eb',
            type: 'dashed',
          },
        },
      },
      series,
      backgroundColor: 'transparent',
    }
  }, [data])

  return (
    <div className="w-full h-[400px]">
      <ReactECharts
        option={option}
        style={{ height: '100%', width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  )
}

