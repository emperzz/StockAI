import { useMemo } from 'react'
import type { StockData } from '@/types/stock'

interface StockDataTableProps {
  data: StockData[]
}

export default function StockDataTable({ data }: StockDataTableProps) {
  const tableData = useMemo(() => {
    return data.map((row) => ({
      日期: row.日期,
      开盘: row.开盘?.toFixed(2) ?? 'N/A',
      收盘: row.收盘?.toFixed(2) ?? 'N/A',
      最高: row.最高?.toFixed(2) ?? 'N/A',
      最低: row.最低?.toFixed(2) ?? 'N/A',
      成交量: row.成交量 ? (row.成交量 / 10000).toFixed(2) + '万' : 'N/A',
      成交额: row.成交额 ? (row.成交额 / 100000000).toFixed(2) + '亿' : 'N/A',
    }))
  }, [data])

  if (tableData.length === 0) {
    return <p className="text-muted-foreground">暂无数据</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b">
            {Object.keys(tableData[0]).map((key) => (
              <th
                key={key}
                className="px-4 py-2 text-left font-semibold text-sm"
              >
                {key}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.map((row, index) => (
            <tr key={index} className="border-b hover:bg-muted/50">
              {Object.values(row).map((value, cellIndex) => (
                <td key={cellIndex} className="px-4 py-2 text-sm">
                  {value}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

