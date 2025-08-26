import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'

interface ProgressIndicatorProps {
  progress: number
  status: string
}

export default function ProgressIndicator({ progress, status }: ProgressIndicatorProps) {
  return (
    <motion.div
      className="glass-morphism rounded-2xl p-6"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
    >
      <div className="flex items-center gap-4 mb-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        >
          <Loader2 className="w-6 h-6 text-primary-400" />
        </motion.div>
        <div>
          <h3 className="text-white font-semibold">Processing...</h3>
          <p className="text-white/60 text-sm">{status}</p>
        </div>
      </div>
      
      <div className="relative">
        <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
        <motion.div
          className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent"
          animate={{ x: ['0%', '100%'] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          style={{ width: '30%' }}
        />
      </div>
      
      <div className="flex justify-between items-center mt-3">
        <span className="text-white/80 text-sm">Progress</span>
        <span className="text-primary-300 font-semibold">{progress}%</span>
      </div>
    </motion.div>
  )
}