import Head from 'next/head'
import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { ParticleBackground } from './ParticleBackground'

interface LayoutProps {
  children: ReactNode
  title?: string
}

export default function Layout({ children, title = 'Instagram Lead Generator' }: LayoutProps) {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="AI-Powered Instagram Lead Generation Platform" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div className="relative min-h-screen overflow-hidden">
        <ParticleBackground />
        
        {/* Animated gradient background */}
        <div className="fixed inset-0 -z-10">
          <motion.div
            className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-accent-900/20 to-secondary-900/20"
            animate={{
              backgroundPosition: ['0% 0%', '100% 100%', '0% 0%'],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        </div>

        {/* Main content */}
        <main className="relative z-10">
          {children}
        </main>

        {/* Floating orbs */}
        <div className="fixed inset-0 pointer-events-none -z-5">
          <motion.div
            className="absolute top-20 left-10 w-32 h-32 bg-primary-500/20 rounded-full blur-xl"
            animate={{
              x: [0, 100, 0],
              y: [0, -50, 0],
            }}
            transition={{
              duration: 15,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
          <motion.div
            className="absolute bottom-20 right-10 w-40 h-40 bg-accent-500/20 rounded-full blur-xl"
            animate={{
              x: [0, -80, 0],
              y: [0, 60, 0],
            }}
            transition={{
              duration: 12,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </div>
      </div>
    </>
  )
}