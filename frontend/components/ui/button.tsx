import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  isLoading?: boolean
  children: React.ReactNode
}

const buttonVariants = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  ghost: 'relative overflow-hidden rounded-2xl px-6 py-3 font-medium text-white/80 hover:text-white hover:bg-white/10 transition-all duration-300',
  destructive: 'relative overflow-hidden rounded-2xl px-6 py-3 font-medium text-white bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 transition-all duration-300'
}

const sizeVariants = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
  xl: 'px-10 py-5 text-xl'
}

export default function Button({ 
  variant = 'primary', 
  size = 'md', 
  isLoading = false, 
  children, 
  className,
  disabled,
  ...props 
}: ButtonProps) {
  return (
    <motion.button
      className={cn(
        buttonVariants[variant],
        size !== 'md' && sizeVariants[size],
        'relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      disabled={disabled || isLoading}
      whileHover={{ scale: disabled || isLoading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || isLoading ? 1 : 0.98 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      {...props}
    >
      {/* Shimmer effect */}
      {variant === 'primary' && !disabled && !isLoading && (
        <motion.div
          className="absolute inset-0 -top-2 -bottom-2 bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-12"
          initial={{ x: '-100%' }}
          whileHover={{ x: '100%' }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
        />
      )}
      
      <span className="relative z-10 flex items-center justify-center gap-2">
        {isLoading && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            <Loader2 className="w-5 h-5" />
          </motion.div>
        )}
        {children}
      </span>
    </motion.button>
  )
}

// Export additional button components
export function IconButton({ 
  children, 
  className, 
  ...props 
}: Omit<ButtonProps, 'variant' | 'size'>) {
  return (
    <motion.button
      className={cn(
        'p-3 rounded-2xl bg-white/10 hover:bg-white/20 text-white transition-all duration-300 backdrop-blur-sm border border-white/10',
        className
      )}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      {...props}
    >
      {children}
    </motion.button>
  )
}

export function FloatingActionButton({ 
  children, 
  className, 
  ...props 
}: Omit<ButtonProps, 'variant' | 'size'>) {
  return (
    <motion.button
      className={cn(
        'fixed bottom-8 right-8 p-4 rounded-full bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-2xl',
        className
      )}
      whileHover={{ scale: 1.1, y: -2 }}
      whileTap={{ scale: 0.9 }}
      animate={{ y: [0, -5, 0] }}
      transition={{
        y: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
        scale: { type: 'spring', stiffness: 400, damping: 25 }
      }}
      {...props}
    >
      {children}
    </motion.button>
  )
}