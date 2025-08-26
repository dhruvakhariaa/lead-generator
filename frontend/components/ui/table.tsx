import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronUp, ChevronDown, ArrowUpDown } from 'lucide-react'
import { cn } from '../../lib/utils'

interface Column<T> {
  key: keyof T
  header: string
  sortable?: boolean
  render?: (value: any, row: T, index: number) => React.ReactNode
  className?: string
  headerClassName?: string
}

interface TableProps<T> {
  data: T[]
  columns: Column<T>[]
  className?: string
  loading?: boolean
  emptyMessage?: string
  sortable?: boolean
  onSort?: (key: keyof T, direction: 'asc' | 'desc') => void
  sortKey?: keyof T
  sortDirection?: 'asc' | 'desc'
}

interface SortState<T> {
  key: keyof T | null
  direction: 'asc' | 'desc'
}

export default function Table<T extends Record<string, any>>({
  data,
  columns,
  className,
  loading = false,
  emptyMessage = "No data available",
  sortable = true,
  onSort,
  sortKey,
  sortDirection
}: TableProps<T>) {
  const [internalSort, setInternalSort] = React.useState<SortState<T>>({
    key: null,
    direction: 'asc'
  })

  const currentSortKey = sortKey ?? internalSort.key
  const currentSortDirection = sortDirection ?? internalSort.direction

  const handleSort = (key: keyof T) => {
    if (!sortable) return

    const newDirection = 
      currentSortKey === key && currentSortDirection === 'asc' ? 'desc' : 'asc'
    
    if (onSort) {
      onSort(key, newDirection)
    } else {
      setInternalSort({ key, direction: newDirection })
    }
  }

  const sortedData = React.useMemo(() => {
    if (!currentSortKey || onSort) return data

    return [...data].sort((a, b) => {
      const aVal = a[currentSortKey]
      const bVal = b[currentSortKey]
      
      if (aVal < bVal) return currentSortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return currentSortDirection === 'asc' ? 1 : -1
      return 0
    })
  }, [data, currentSortKey, currentSortDirection, onSort])

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  }

  const rowVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        type: 'spring',
        stiffness: 100
      }
    }
  }

  if (loading) {
    return (
      <div className={cn('overflow-hidden rounded-2xl', className)}>
        <div className="glass-morphism">
          <table className="w-full">
            <thead>
              <tr className="bg-white/5">
                {columns.map((column) => (
                  <th 
                    key={String(column.key)} 
                    className="px-6 py-4 text-left text-sm font-semibold text-white/80"
                  >
                    {column.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-t border-white/10">
                  {columns.map((column) => (
                    <td key={String(column.key)} className="px-6 py-4">
                      <div className="h-4 bg-white/10 rounded-lg animate-pulse shimmer-loading" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('overflow-hidden rounded-2xl', className)}>
      <div className="glass-morphism overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-white/5 backdrop-blur-sm">
              {columns.map((column) => (
                <th 
                  key={String(column.key)}
                  className={cn(
                    'px-6 py-4 text-left text-sm font-semibold text-white/80 transition-colors',
                    column.headerClassName,
                    sortable && column.sortable !== false && 'cursor-pointer hover:text-white'
                  )}
                  onClick={() => column.sortable !== false && handleSort(column.key)}
                >
                  <div className="flex items-center gap-2">
                    <span>{column.header}</span>
                    {sortable && column.sortable !== false && (
                      <div className="flex flex-col">
                        {currentSortKey === column.key ? (
                          currentSortDirection === 'asc' ? (
                            <ChevronUp className="w-4 h-4 text-primary-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-primary-400" />
                          )
                        ) : (
                          <ArrowUpDown className="w-4 h-4 text-white/40 group-hover:text-white/60" />
                        )}
                      </div>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            <AnimatePresence mode="wait">
              {sortedData.length === 0 ? (
                <motion.tr
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <td 
                    colSpan={columns.length} 
                    className="px-6 py-12 text-center text-white/60"
                  >
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center">
                        <span className="text-2xl">📋</span>
                      </div>
                      <p>{emptyMessage}</p>
                    </div>
                  </td>
                </motion.tr>
              ) : (
                <motion.tbody
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                >
                  {sortedData.map((row, index) => (
                    <motion.tr
                      key={index}
                      variants={rowVariants}
                      className="group hover:bg-white/5 transition-all duration-300"
                      whileHover={{ scale: 1.01 }}
                    >
                      {columns.map((column) => (
                        <td 
                          key={String(column.key)}
                          className={cn(
                            'px-6 py-4 transition-colors',
                            column.className
                          )}
                        >
                          {column.render 
                            ? column.render(row[column.key], row, index)
                            : String(row[column.key] ?? '')
                          }
                        </td>
                      ))}
                    </motion.tr>
                  ))}
                </motion.tbody>
              )}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Export additional table components
export function SimpleTable({ 
  children, 
  className 
}: { 
  children: React.ReactNode
  className?: string 
}) {
  return (
    <div className={cn('overflow-hidden rounded-2xl glass-morphism', className)}>
      <table className="w-full">
        {children}
      </table>
    </div>
  )
}

export function TableHeader({ 
  children, 
  className 
}: { 
  children: React.ReactNode
  className?: string 
}) {
  return (
    <thead className={cn('bg-white/5 backdrop-blur-sm', className)}>
      {children}
    </thead>
  )
}

export function TableBody({ 
  children, 
  className 
}: { 
  children: React.ReactNode
  className?: string 
}) {
  return (
    <tbody className={cn('divide-y divide-white/10', className)}>
      {children}
    </tbody>
  )
}

export function TableRow({ 
  children, 
  className,
  ...props 
}: { 
  children: React.ReactNode
  className?: string 
} & React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <motion.tr
      className={cn(
        'group hover:bg-white/5 transition-all duration-300',
        className
      )}
      whileHover={{ scale: 1.005 }}
      {...props}
    >
      {children}
    </motion.tr>
  )
}

export function TableCell({ 
  children, 
  className,
  ...props 
}: { 
  children: React.ReactNode
  className?: string 
} & React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td 
      className={cn('px-6 py-4 transition-colors', className)}
      {...props}
    >
      {children}
    </td>
  )
}