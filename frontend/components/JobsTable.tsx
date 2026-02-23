import { motion } from 'framer-motion'
import { ExternalLink, MapPin, Clock, DollarSign } from 'lucide-react'

interface Job {
  _id: string;
  title: string;
  company_name: string;
  location: string;
  platform: string;
  salary_range?: string;
  job_type: string;
  posted_date?: string;
}

interface JobsTableProps {
  jobs: Job[];
}

export default function JobsTable({ jobs }: JobsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/20">
            <th className="text-left py-4 px-4 text-white/80">Job Title</th>
            <th className="text-left py-4 px-4 text-white/80">Company</th>
            <th className="text-left py-4 px-4 text-white/80">Location</th>
            <th className="text-left py-4 px-4 text-white/80">Type</th>
            <th className="text-left py-4 px-4 text-white/80">Platform</th>
            <th className="text-left py-4 px-4 text-white/80">Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job, index) => (
            <motion.tr
              key={job._id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="border-b border-white/10 hover:bg-white/5"
            >
              <td className="py-4 px-4">
                <div className="font-semibold text-white">{job.title}</div>
              </td>
              <td className="py-4 px-4 text-white/80">{job.company_name}</td>
              <td className="py-4 px-4">
                <div className="flex items-center gap-1 text-white/80">
                  <MapPin className="w-4 h-4" />
                  {job.location}
                </div>
              </td>
              <td className="py-4 px-4">
                <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-xs">
                  {job.job_type}
                </span>
              </td>
              <td className="py-4 px-4 text-white/80 capitalize">{job.platform}</td>
              <td className="py-4 px-4">
                <button className="text-purple-400 hover:text-purple-300">
                  <ExternalLink className="w-4 h-4" />
                </button>
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}