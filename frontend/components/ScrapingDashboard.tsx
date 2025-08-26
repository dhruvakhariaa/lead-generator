import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation, useQuery } from 'react-query'
import { 
  Search, 
  Users, 
  Download, 
  Loader2, 
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Target,
  Zap
} from 'lucide-react'
import toast from 'react-hot-toast'
import { scrapeUsers, fetchUsersByNiche } from '../lib/api'
import DataTable from './DataTable'
import ProgressIndicator from './ProgressIndicator'

export default function ScrapingDashboard() {
  const [searchParams, setSearchParams] = useState({
    niche: '',
    min_followers: 1000,
    max_results: 50
  })
  const [selectedNiche, setSelectedNiche] = useState('')

  const { data: users, refetch: refetchUsers, isLoading: usersLoading } = useQuery(
    ['users', selectedNiche],
    () => fetchUsersByNiche(selectedNiche),
    { enabled: !!selectedNiche }
  )

  const scrapeUsersMutation = useMutation(scrapeUsers, {
    onSuccess: (data) => {
      toast.success(`Successfully scraped ${data.users_count} users!`)
      setSelectedNiche(searchParams.niche)
      refetchUsers()
    },
    onError: (error: any) => {
      toast.error(`Scraping failed: ${error.response?.data?.detail || error.message}`)
    }
  })

  const handleScrapeUsers = () => {
    if (!searchParams.niche.trim()) {
      toast.error('Please enter a niche')
      return
    }
    
    scrapeUsersMutation.mutate({
      niche: searchParams.niche.trim(),
      min_follower_count: searchParams.min_followers,
      max_results: searchParams.max_results
    })
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 100,
      },
    },
  }

  return (
    <motion.div
      className="space-y-8"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Search Form */}
      <motion.div 
        className="card-modern"
        variants={itemVariants}
      >
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 rounded-2xl bg-primary-500/20">
            <Search className="w-6 h-6 text-primary-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Lead Discovery</h2>
            <p className="text-white/60">Search for Instagram influencers in your target niche</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-white/80 mb-3">
              Target Niche
            </label>
            <input
              type="text"
              value={searchParams.niche}
              onChange={(e) => setSearchParams(prev => ({ ...prev, niche: e.target.value }))}
              placeholder="e.g., fitness, travel, food, tech"
              className="input-modern"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-3">
              Min Followers
            </label>
            <input
              type="number"
              value={searchParams.min_followers}
              onChange={(e) => setSearchParams(prev => ({ ...prev, min_followers: parseInt(e.target.value) }))}
              className="input-modern"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-3">
              Max Results
            </label>
            <input
              type="number"
              value={searchParams.max_results}
              onChange={(e) => setSearchParams(prev => ({ ...prev, max_results: parseInt(e.target.value) }))}
              className="input-modern"
              max="100"
            />
          </div>
        </div>

        <motion.button
          onClick={handleScrapeUsers}
          disabled={scrapeUsersMutation.isLoading}
          className="btn-primary w-full md:w-auto group"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {scrapeUsersMutation.isLoading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Target className="w-5 h-5 mr-2 group-hover:rotate-12 transition-transform" />
              Start Lead Discovery
              <Zap className="w-5 h-5 ml-2 group-hover:scale-110 transition-transform" />
            </>
          )}
        </motion.button>

        {/* Progress Indicator */}
        <AnimatePresence>
          {scrapeUsersMutation.isLoading && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6"
            >
              <ProgressIndicator 
                progress={60} 
                status="Analyzing Instagram profiles..."
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Results Section */}
      <AnimatePresence>
        {users && users.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="card-modern"
            variants={itemVariants}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-2xl bg-green-500/20">
                  <CheckCircle2 className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">
                    Found {users.length} Quality Leads
                  </h3>
                  <p className="text-white/60">
                    Niche: {selectedNiche} • Ready for export
                  </p>
                </div>
              </div>
              
              <motion.button
                className="btn-secondary"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Download className="w-5 h-5 mr-2" />
                Export JSON
              </motion.button>
            </div>

            <DataTable users={users} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Stats */}
      {users && users.length > 0 && (
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
          variants={itemVariants}
        >
          {[
            {
              label: 'Total Followers',
              value: users.reduce((sum, user) => sum + (user.follower_count || 0), 0).toLocaleString(),
              icon: Users,
              color: 'text-blue-400'
            },
            {
              label: 'Avg. Followers',
              value: Math.round(users.reduce((sum, user) => sum + (user.follower_count || 0), 0) / users.length).toLocaleString(),
              icon: TrendingUp,
              color: 'text-green-400'
            },
            {
              label: 'Verified Accounts',
              value: users.filter(user => user.is_verified).length.toString(),
              icon: CheckCircle2,
              color: 'text-purple-400'
            }
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              className="card-modern text-center group"
              whileHover={{ scale: 1.05 }}
              transition={{ type: 'spring', stiffness: 300 }}
            >
              <stat.icon className={`w-8 h-8 mx-auto mb-3 ${stat.color} group-hover:scale-110 transition-transform`} />
              <h4 className="text-2xl font-bold text-white mb-1">{stat.value}</h4>
              <p className="text-white/60 text-sm">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}