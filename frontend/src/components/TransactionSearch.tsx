import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Search } from 'lucide-react'

interface TransactionSearchProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function TransactionSearch({ value, onChange, placeholder = 'Search payee or memo...' }: TransactionSearchProps) {
  const [localValue, setLocalValue] = useState(value)

  // Debounce effect
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue)
    }, 300)
    return () => clearTimeout(timer)
  }, [localValue, onChange])

  // Sync with external value
  useEffect(() => {
    setLocalValue(value)
  }, [value])

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        type="text"
        placeholder={placeholder}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        className="pl-9"
      />
    </div>
  )
}

export default TransactionSearch
