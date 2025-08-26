import React, { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Search, X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  variant?: 'default' | 'search' | 'modern'
  clearable?: boolean
  onClear?: () => void
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  className,
  type,
  label,
  error,
  leftIcon,
  rightIcon,
  variant = 'default',
  clearable = false,
  onClear,
  value,
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = React.useState(false)
  const [isFocused, setIsFocused] = React.useState(false)

  const inputVariants = {
    default: 'input-modern',
    search: 'input-modern pl-12',
    modern: 'w-full rounded-2xl border-0 bg-white/5 px-6 py-4 text-white placeholder-white/40 backdrop-blur-20 transition-all duration-300 border border-white/10 focus:border-primary-500 focus:bg-white/10 focus:outline-none focus:ring-2 focus:ring-primary-500/20'
  }

  return (
    <div className="space-y-2">
      {label && (
        <motion.label 
          className="block text-sm font-medium text-white/80"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {label}
        </motion.label>
      )}
      
      <div className="relative">
        {/* Left Icon */}
        {leftIcon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40">
            {leftIcon}
          </div>
        )}
        
        {/* Search Icon for search variant */}
        {variant === 'search' && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40">
            <Search className="w-5 h-5" />
          </div>
        )}

        <motion.input
          ref={ref}
          type={type === 'password' && showPassword ? 'text' : type}
          className={cn(
            inputVariants[variant],
            leftIcon && 'pl-12',
            (rightIcon || type === 'password' || clearable) && 'pr-12',
            error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
            className
          )}
          value={value}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          whileFocus={{ scale: 1.02 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          {...props}
        />

        {/* Right Icons */}
        <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {/* Clear button */}
          {clearable && value && (
            <motion.button
              type="button"
              onClick={onClear}
              className="text-white/40 hover:text-white/80 transition-colors"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <X className="w-4 h-4" />
            </motion.button>
          )}

          {/* Password toggle */}
          {type === 'password' && (
            <motion.button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-white/40 hover:text-white/80 transition-colors"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
            </motion.button>
          )}

          {/* Custom right icon */}
          {rightIcon && !clearable && type !== 'password' && (
            <div className="text-white/40">
              {rightIcon}
            </div>
          )}
        </div>

        {/* Focus ring animation */}
        {isFocused && (
          <motion.div
            className="absolute inset-0 rounded-2xl ring-2 ring-primary-500/30 pointer-events-none"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
        )}
      </div>

      {/* Error message */}
      {error && (
        <motion.p
          className="text-sm text-red-400"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {error}
        </motion.p>
      )}
    </div>
  )
})

Input.displayName = 'Input'

// Export additional input components
export function SearchInput({ 
  onSearch, 
  placeholder = "Search...", 
  ...props 
}: InputProps & { onSearch?: (value: string) => void }) {
  const [value, setValue] = React.useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch?.(value)
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <Input
        variant="search"
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        clearable
        onClear={() => setValue('')}
        {...props}
      />
    </form>
  )
}

export function NumberInput({ 
  min, 
  max, 
  step = 1, 
  ...props 
}: InputProps & { min?: number; max?: number; step?: number }) {
  return (
    <Input
      type="number"
      min={min}
      max={max}
      step={step}
      {...props}
    />
  )
}

export default Input