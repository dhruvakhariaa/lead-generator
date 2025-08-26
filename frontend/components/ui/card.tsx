import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { cn } from '../../lib/utils'

interface CardProps extends HTMLMotionProps<"div"> {
  variant?: 'default' | 'modern' | 'glass' | 'gradient' | 'floating'
  hover?: boolean
  glow?: boolean
  children: React.ReactNode
}

const cardVariants = {
  default: 'bg-white/10 rounded-2xl p-6 border border-white/20 backdrop-blur-sm',
  modern: 'card-modern',
  glass: 'glass-morphism rounded-3xl p-8',
  gradient: 'bg-gradient-to-br from-primary-500/20 to-accent-500/20 rounded-3xl p-8 border border-primary-500/30',
  floating: 'card-modern floating-element shadow-2xl'
}

export default function Card({ 
  variant = 'default', 
  hover = true,
  glow = false,
  children, 
  className,
  ...props 
}: CardProps) {
  return (
    <motion.div
      className={cn(
        cardVariants[variant],
        glow && 'animate-pulse-glow',
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hover ? { 
        scale: 1.02, 
        y: -5,
        transition: { type: 'spring', stiffness: 300, damping: 30 }
      } : undefined}
      transition={{ 
        type: 'spring', 
        stiffness: 100, 
        damping: 15 
      }}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Card Header Component
export function CardHeader({ 
  children, 
  className,
  ...props 
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div 
      className={cn('mb-6', className)}
      {...props}
    >
      {children}
    </div>
  )
}

// Card Title Component
export function CardTitle({ 
  children, 
  className,
  ...props 
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 
      className={cn('text-2xl font-bold text-white mb-2', className)}
      {...props}
    >
      {children}
    </h3>
  )
}

// Card Description Component
export function CardDescription({ 
  children, 
  className,
  ...props 
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p 
      className={cn('text-white/60', className)}
      {...props}
    >
      {children}
    </p>
  )
}

// Card Content Component
export function CardContent({ 
  children, 
  className,
  ...props 
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div 
      className={cn('', className)}
      {...props}
    >
      {children}
    </div>
  )
}

// Card Footer Component
export function CardFooter({ 
  children, 
  className,
  ...props 
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div 
      className={cn('mt-6 pt-6 border-t border-white/10', className)}
      {...props}
    >
      {children}
    </div>
  )
}

// Specialized Card Components
export function StatsCard({ 
  title, 
  value, 
  icon: Icon, 
  change, 
  className,
  ...props 
}: {
  title: string
  value: string | number
  icon?: React.ElementType
  change?: string
  className?: string
} & Omit<CardProps, 'children'>) {
  return (
    <Card 
      variant="modern" 
      className={cn('group', className)}
      {...props}
    >
      <div className="flex items-center justify-between mb-4">
        {Icon && (
          <div className="p-3 rounded-2xl bg-primary-500/20 group-hover:bg-primary-500/30 transition-colors">
            <Icon className="w-6 h-6 text-primary-400" />
          </div>
        )}
        {change && (
          <span className={cn(
            'text-sm font-medium px-2 py-1 rounded-full',
            change.startsWith('+') ? 'text-green-400 bg-green-500/20' : 'text-red-400 bg-red-500/20'
          )}>
            {change}
          </span>
        )}
      </div>
      
      <h3 className="text-3xl font-bold text-white mb-1 group-hover:text-primary-300 transition-colors">
        {value}
      </h3>
      <p className="text-white/60 text-sm">{title}</p>
    </Card>
  )
}

export function FeatureCard({ 
  title, 
  description, 
  icon: Icon, 
  className,
  ...props 
}: {
  title: string
  description: string
  icon?: React.ElementType
  className?: string
} & Omit<CardProps, 'children'>) {
  return (
    <Card 
      variant="glass" 
      className={cn('text-center group', className)}
      {...props}
    >
      {Icon && (
        <div className="w-16 h-16 mx-auto mb-6 rounded-3xl bg-gradient-to-r from-primary-500 to-accent-500 p-0.5">
          <div className="w-full h-full bg-dark-50 rounded-3xl flex items-center justify-center">
            <Icon className="w-8 h-8 text-white group-hover:scale-110 transition-transform" />
          </div>
        </div>
      )}
      
      <CardTitle className="mb-4 group-hover:text-primary-300 transition-colors">
        {title}
      </CardTitle>
      <CardDescription className="leading-relaxed">
        {description}
      </CardDescription>
    </Card>
  )
}

export function LoadingCard({ 
  className,
  ...props 
}: Omit<CardProps, 'children'>) {
  return (
    <Card 
      variant="modern" 
      hover={false}
      className={cn('animate-pulse', className)}
      {...props}
    >
      <div className="space-y-4">
        <div className="h-4 bg-white/10 rounded-lg shimmer-loading" />
        <div className="h-4 bg-white/10 rounded-lg shimmer-loading w-3/4" />
        <div className="h-8 bg-white/10 rounded-lg shimmer-loading w-1/2" />
      </div>
    </Card>
  )
}

export function GradientCard({ 
  children, 
  gradient = 'from-primary-500/20 to-accent-500/20',
  className,
  ...props 
}: CardProps & { gradient?: string }) {
  return (
    <motion.div
      className={cn(
        'relative overflow-hidden rounded-3xl p-8 border border-primary-500/30',
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        scale: 1.02, 
        y: -5,
        transition: { type: 'spring', stiffness: 300, damping: 30 }
      }}
      {...props}
    >
      <div className={cn('absolute inset-0 bg-gradient-to-br', gradient)} />
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  )
}