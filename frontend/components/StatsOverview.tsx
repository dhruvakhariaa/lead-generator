import { motion } from 'framer-motion'
import { useQuery } from 'react-query'
import { TrendingUp, Users, Database, Activity, Zap, Target } from 'lucide-react'
import { fetchStats } from '../lib/api'

export default function StatsOverview() {
  const { data: stats, isLoading } = useQuery('stats', fetchStats)

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

  if (isLoading) {
    return (
      <div className="card-modern text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="inline-block"
        >
          <Activity className="w-8 h-8 text-primary-400" />
        </motion.div>
        <p className="text-white/60 mt-4">Loading analytics...</p>
      </div>
    )
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users?.toLocaleString() || '0',
      icon: Users,
      gradient: 'from-blue-500 to-purple-500',
      change: '+12%'
    },
    {
      title: 'Total Profiles',
      value: stats?.total_profiles?.toLocaleString() || '0',
      icon: Database,
      gradient: 'from-green-500 to-blue-500',
      change: '+8%'
    },
    {
      title: 'Success Rate',
      value: '98.5%',
      icon: Target,
      gradient: 'from-purple-500 to-pink-500',
      change: '+2%'
    },
    {
      title: 'Processing Speed',
      value: '2.3s',
      icon: Zap,
      gradient: 'from-orange-500 to-red-500',
      change: '-15%'
    }
  ]

  return (
    <motion.div
      className="space-y-8"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Main Stats Grid */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        variants={containerVariants}
      >
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            className="card-modern group"
            variants={itemVariants}
            whileHover={{ scale: 1.05, y: -5 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div className={`w-12 h-12 rounded-2xl bg-gradient-to-r ${stat.gradient} p-0.5 mb-4`}>
              <div className="w-full h-full bg-dark-50 rounded-2xl flex items-center justify-center">
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
            
            <h3 className="text-3xl font-bold text-white mb-1">{stat.value}</h3>
            <p className="text-white/60 text-sm mb-2">{stat.title}</p>
            
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${
                stat.change.startsWith('+') ? 'text-green-400' : 'text-red-400'
              }`}>
                {stat.change}
              </span>
              <span className="text-white/40 text-xs">vs last month</span>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Niche Distribution */}
      {stats?.users_by_niche && stats.users_by_niche.length > 0 && (
        <motion.div 
          className="card-modern"
          variants={itemVariants}
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 rounded-2xl bg-gradient-to-r from-primary-500 to-accent-500">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Niche Distribution</h2>
              <p className="text-white/60">Top performing niches in your database</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stats.users_by_niche.slice(0, 6).map((niche: any, index: number) => (
              <motion.div
                key={niche._id}
                className="group p-4 rounded-2xl bg-gradient-to-r from-white/5 to-white/10 hover:from-white/10 hover:to-white/15 transition-all duration-300"
                whileHover={{ scale: 1.02 }}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-white capitalize">
                    #{niche._id}
                  </h3>
                  <span className="text-2xl">{index < 3 ? '🏆' : '📈'}</span>
                </div>
                
                <p className="text-2xl font-bold text-primary-300 mb-1">
                  {niche.count}
                </p>
                <p className="text-white/60 text-sm">leads generated</p>
                
                <div className="mt-3 w-full bg-white/10 rounded-full h-2">
                  <motion.div
                    className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(niche.count / stats.users_by_niche[0].count) * 100}%` }}
                    transition={{ delay: index * 0.1 + 0.5, duration: 0.8 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Performance Chart Placeholder */}
      <motion.div 
        className="card-modern text-center"
        variants={itemVariants}
      >
        <h2 className="text-2xl font-bold text-white mb-4">Performance Analytics</h2>
        <div className="h-64 bg-gradient-to-r from-primary-500/10 to-accent-500/10 rounded-2xl flex items-center justify-center">
          <div className="text-center">
            <Activity className="w-12 h-12 text-primary-400 mx-auto mb-4" />
            <p className="text-white/60">Advanced analytics dashboard coming soon</p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}