import { motion } from 'framer-motion'
import { CheckCircle2, Users, ExternalLink, Verified } from 'lucide-react'

interface User {
  username: string
  full_name?: string
  follower_count: number
  is_verified: boolean
  profile_pic_url?: string
}

interface DataTableProps {
  users: User[]
}

export default function DataTable({ users }: DataTableProps) {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  }

  const rowVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        type: 'spring',
        stiffness: 100,
      },
    },
  }

  return (
    <div className="overflow-hidden rounded-2xl">
      <div className="overflow-x-auto">
        <motion.table 
          className="w-full"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          <thead>
            <tr className="bg-white/5 backdrop-blur-sm">
              <th className="px-6 py-4 text-left text-sm font-semibold text-white/80">Profile</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-white/80">Username</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-white/80">Followers</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-white/80">Status</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-white/80">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {users.map((user, index) => (
              <motion.tr
                key={user.username}
                variants={rowVariants}
                className="group hover:bg-white/5 transition-all duration-300"
                whileHover={{ scale: 1.01 }}
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      {user.profile_pic_url ? (
                        <img
                          src={user.profile_pic_url}
                          alt={user.username}
                          className="w-10 h-10 rounded-full object-cover ring-2 ring-primary-500/20"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-500 to-accent-500 flex items-center justify-center">
                          <Users className="w-5 h-5 text-white" />
                        </div>
                      )}
                      {user.is_verified && (
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                          <Verified className="w-2.5 h-2.5 text-white" />
                        </div>
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-white">{user.full_name || user.username}</p>
                      <p className="text-sm text-white/60">@{user.username}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className="font-mono text-primary-300">@{user.username}</span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-semibold">
                      {user.follower_count?.toLocaleString() || 0}
                    </span>
                    <Users className="w-4 h-4 text-white/40" />
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {user.is_verified && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-300 bg-blue-500/20 rounded-full">
                        <CheckCircle2 className="w-3 h-3" />
                        Verified
                      </span>
                    )}
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-green-300 bg-green-500/20 rounded-full">
                      Active
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <motion.button
                    className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-primary-300 hover:text-primary-200 transition-colors"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => window.open(`https://instagram.com/${user.username}`, '_blank')}
                  >
                    <ExternalLink className="w-4 h-4" />
                    View Profile
                  </motion.button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </motion.table>
      </div>
    </div>
  )
}