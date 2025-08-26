import { useState } from 'react'
import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { 
  Users, 
  Zap, 
  Target, 
  TrendingUp,
  Sparkles,
  Download,
  Eye,
  ArrowRight
} from 'lucide-react'
import Layout from '../components/Layout'
import ScrapingDashboard from '../components/ScrapingDashboard'
import StatsOverview from '../components/StatsOverview'
import { Toaster } from 'react-hot-toast'

export default function Home() {
  const [activeSection, setActiveSection] = useState('dashboard')
  const [ref, inView] = useInView({ threshold: 0.1 })

  const sections = [
    { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
    { id: 'scraping', label: 'Lead Generation', icon: Target },
    { id: 'analytics', label: 'Analytics', icon: Eye },
    { id: 'export', label: 'Export Data', icon: Download },
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 50, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 100,
        damping: 15,
      },
    },
  }

  return (
    <Layout>
      <div className="min-h-screen">
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(20px)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '16px',
            },
            success: {
              iconTheme: {
                primary: '#9d58ff',
                secondary: 'white',
              },
            },
          }}
        />

        {/* Hero Section */}
        <motion.section
          className="relative px-4 pt-20 pb-16 sm:px-6 lg:px-8"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          <div className="mx-auto max-w-7xl">
            <motion.div 
              className="text-center"
              variants={itemVariants}
            >
              <motion.h1 
                className="text-5xl font-bold font-display sm:text-7xl lg:text-8xl"
                variants={itemVariants}
              >
                <span className="gradient-text">Instagram</span>
                <br />
                <span className="text-white">Lead Generator</span>
              </motion.h1>
              
              <motion.p 
                className="mx-auto mt-6 max-w-2xl text-xl text-white/80 sm:text-2xl"
                variants={itemVariants}
              >
                AI-powered platform to discover, analyze, and export Instagram leads 
                with precision targeting and intelligent filtering.
              </motion.p>

              <motion.div 
                className="mt-10 flex flex-col sm:flex-row gap-4 justify-center"
                variants={itemVariants}
              >
                <button className="btn-primary group">
                  <Sparkles className="w-5 h-5 mr-2 group-hover:animate-spin" />
                  Start Generating Leads
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </button>
                <button className="btn-secondary">
                  <Eye className="w-5 h-5 mr-2" />
                  View Demo
                </button>
              </motion.div>
            </motion.div>

            {/* Stats Cards */}
            <motion.div 
              className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8"
              variants={itemVariants}
            >
              {[
                { icon: Users, label: 'Leads Generated', value: '50K+' },
                { icon: Zap, label: 'Processing Speed', value: '99.9%' },
                { icon: Target, label: 'Accuracy Rate', value: '95%' },
              ].map((stat, index) => (
                <motion.div
                  key={stat.label}
                  className="card-modern text-center group"
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  <stat.icon className="w-12 h-12 mx-auto mb-4 text-primary-400 group-hover:text-primary-300 transition-colors" />
                  <h3 className="text-3xl font-bold text-white mb-2">{stat.value}</h3>
                  <p className="text-white/60">{stat.label}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </motion.section>

        {/* Navigation */}
        <motion.section 
          className="px-4 sm:px-6 lg:px-8 mb-12"
          ref={ref}
          initial={{ opacity: 0, y: 50 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mx-auto max-w-7xl">
            <nav className="glass-morphism rounded-3xl p-2">
              <div className="flex flex-wrap justify-center gap-2">
                {sections.map((section) => (
                  <motion.button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`relative flex items-center gap-3 rounded-2xl px-6 py-4 font-medium transition-all duration-300 ${
                      activeSection === section.id
                        ? 'bg-primary-500 text-white shadow-lg'
                        : 'text-white/70 hover:text-white hover:bg-white/10'
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <section.icon className="w-5 h-5" />
                    <span>{section.label}</span>
                    {activeSection === section.id && (
                      <motion.div
                        className="absolute inset-0 rounded-2xl bg-primary-500"
                        layoutId="activeSection"
                        initial={false}
                        transition={{
                          type: 'spring',
                          stiffness: 500,
                          damping: 30,
                        }}
                        style={{ zIndex: -1 }}
                      />
                    )}
                  </motion.button>
                ))}
              </div>
            </nav>
          </div>
        </motion.section>

        {/* Content */}
        <motion.section
          className="px-4 sm:px-6 lg:px-8 pb-20"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mx-auto max-w-7xl">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.4 }}
            >
              {activeSection === 'dashboard' && <StatsOverview />}
              {activeSection === 'scraping' && <ScrapingDashboard />}
              {activeSection === 'analytics' && (
                <div className="card-modern text-center">
                  <h2 className="text-3xl font-bold text-white mb-4">Analytics Coming Soon</h2>
                  <p className="text-white/60">Advanced analytics and insights dashboard</p>
                </div>
              )}
              {activeSection === 'export' && (
                <div className="card-modern text-center">
                  <h2 className="text-3xl font-bold text-white mb-4">Export Data</h2>
                  <p className="text-white/60">Export your leads in various formats</p>
                </div>
              )}
            </motion.div>
          </div>
        </motion.section>
      </div>
    </Layout>
  )
}