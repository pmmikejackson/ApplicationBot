import React, { useState, useEffect } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  StarIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { jobsApi, Job } from '../services/api.ts';
import { format } from 'date-fns';

const priorityColors = {
  must_apply: 'bg-red-100 text-red-800',
  good_fit: 'bg-yellow-100 text-yellow-800',
  stretch: 'bg-blue-100 text-blue-800',
  low_priority: 'bg-gray-100 text-gray-800',
};

const statusColors = {
  discovered: 'bg-blue-100 text-blue-800',
  applied: 'bg-green-100 text-green-800',
  under_review: 'bg-yellow-100 text-yellow-800',
  interview_scheduled: 'bg-purple-100 text-purple-800',
  rejected: 'bg-red-100 text-red-800',
  offer_received: 'bg-green-100 text-green-800',
};

export const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    platform: '',
    priority: '',
    min_fit_score: '',
  });
  const [sortBy, setSortBy] = useState<'fit_score' | 'posted_date' | 'company' | 'salary_min'>('fit_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  useEffect(() => {
    loadJobs();
  }, [filters]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const params = {
        ...filters,
        min_fit_score: filters.min_fit_score ? parseFloat(filters.min_fit_score) : undefined,
      };
      const data = await jobsApi.getJobs(params);
      setJobs(data);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateJob = async (jobId: number, updates: Partial<Job>) => {
    try {
      const updatedJob = await jobsApi.updateJob(jobId, updates);
      setJobs(jobs.map(job => job.id === jobId ? updatedJob : job));
      if (selectedJob?.id === jobId) {
        setSelectedJob(updatedJob);
      }
    } catch (error) {
      console.error('Failed to update job:', error);
    }
  };

  const filteredAndSortedJobs = jobs
    .filter(job =>
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.company.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'fit_score':
          aValue = a.fit_score;
          bValue = b.fit_score;
          break;
        case 'posted_date':
          aValue = new Date(a.posted_date || 0).getTime();
          bValue = new Date(b.posted_date || 0).getTime();
          break;
        case 'company':
          aValue = a.company.toLowerCase();
          bValue = b.company.toLowerCase();
          break;
        case 'salary_min':
          aValue = a.salary_min || 0;
          bValue = b.salary_min || 0;
          break;
        default:
          return 0;
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const renderFitScore = (score: number) => {
    const filledStars = Math.round(score / 2); // Convert 0-10 to 0-5 stars
    return (
      <div className="flex items-center">
        {[...Array(5)].map((_, i) => (
          i < filledStars ? (
            <StarIconSolid key={i} className="h-4 w-4 text-yellow-400" />
          ) : (
            <StarIcon key={i} className="h-4 w-4 text-gray-300" />
          )
        ))}
        <span className="ml-1 text-sm text-gray-600">{score.toFixed(1)}</span>
      </div>
    );
  };

  const JobCard = ({ job, onStatusChange, onClick, showApplyButton = false }: { 
    job: Job; 
    onStatusChange: (id: number, status: string) => void;
    onClick: () => void;
    showApplyButton?: boolean;
  }) => (
    <div
      className="p-4 hover:bg-gray-50 cursor-pointer border-l-4"
      onClick={onClick}
      style={{ borderLeftColor: job.priority === 'must_apply' ? '#ef4444' : job.priority === 'good_fit' ? '#f59e0b' : '#6b7280' }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">{job.title}</h3>
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${priorityColors[job.priority as keyof typeof priorityColors]}`}>
              {job.priority.replace('_', ' ')}
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-1">{job.company}</p>
          <div className="flex items-center space-x-3 text-xs text-gray-500 mb-2">
            <div className="flex items-center">
              <MapPinIcon className="h-3 w-3 mr-1" />
              {job.location}
            </div>
            {job.salary_min && (
              <div className="flex items-center">
                <CurrencyDollarIcon className="h-3 w-3 mr-1" />
                ${job.salary_min.toLocaleString()}k
              </div>
            )}
            <span className="text-blue-600 capitalize">{job.platform}</span>
          </div>
          <div className="flex items-center justify-between">
            {renderFitScore(job.fit_score)}
            <div className="flex items-center space-x-2">
              {showApplyButton && job.status === 'discovered' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onStatusChange(job.id, 'applied');
                  }}
                  className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 focus:outline-none focus:ring-1 focus:ring-green-500"
                >
                  Apply Now
                </button>
              )}
              <select
                value={job.status}
                onChange={(e) => onStatusChange(job.id, e.target.value)}
                onClick={(e) => e.stopPropagation()}
                className="text-xs border border-gray-300 rounded py-1 px-2 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="discovered">Discovered</option>
                <option value="applied">Applied</option>
                <option value="under_review">Under Review</option>
                <option value="interview_scheduled">Interview</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        <p className="text-gray-600">Manage and track discovered job opportunities</p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <div className="lg:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Search jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
          
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Status</option>
            <option value="discovered">Discovered</option>
            <option value="applied">Applied</option>
            <option value="under_review">Under Review</option>
            <option value="interview_scheduled">Interview Scheduled</option>
            <option value="rejected">Rejected</option>
          </select>

          <select
            value={filters.platform}
            onChange={(e) => setFilters({ ...filters, platform: e.target.value })}
            className="border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Platforms</option>
            <option value="linkedin">LinkedIn</option>
            <option value="indeed">Indeed</option>
            <option value="builtin">BuiltIn</option>
            <option value="ziprecruiter">ZipRecruiter</option>
          </select>

          <select
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
            className="border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Priority</option>
            <option value="must_apply">Must Apply</option>
            <option value="good_fit">Good Fit</option>
            <option value="stretch">Stretch</option>
            <option value="low_priority">Low Priority</option>
          </select>

          <input
            type="number"
            min="0"
            max="10"
            step="0.1"
            placeholder="Min Fit Score"
            value={filters.min_fit_score}
            onChange={(e) => setFilters({ ...filters, min_fit_score: e.target.value })}
            className="border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        {/* Sorting Controls */}
        <div className="flex items-center space-x-4 mt-4 pt-4 border-t border-gray-200">
          <span className="text-sm font-medium text-gray-700">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="fit_score">Fit Score</option>
            <option value="posted_date">Posted Date</option>
            <option value="company">Company</option>
            <option value="salary_min">Salary</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="flex items-center space-x-1 px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <span className="text-sm">{sortOrder === 'asc' ? '↑' : '↓'}</span>
            <span className="text-sm">{sortOrder === 'asc' ? 'Ascending' : 'Descending'}</span>
          </button>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Jobs Available Column */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 bg-blue-50">
            <h3 className="text-lg font-medium text-blue-900">Jobs Available</h3>
            <p className="text-sm text-blue-700">
              {filteredAndSortedJobs.filter(job => ['discovered', 'filtered'].includes(job.status)).length} opportunities
            </p>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading jobs...</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {filteredAndSortedJobs
                  .filter(job => ['discovered', 'filtered'].includes(job.status))
                  .map((job) => (
                    <JobCard 
                      key={job.id} 
                      job={job} 
                      onStatusChange={(id, status) => handleUpdateJob(id, { status })}
                      onClick={() => setSelectedJob(job)}
                      showApplyButton={true}
                    />
                  ))}
                {filteredAndSortedJobs.filter(job => ['discovered', 'filtered'].includes(job.status)).length === 0 && (
                  <div className="p-8 text-center">
                    <p className="text-gray-600">No available jobs found.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Jobs Applied For Column */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 bg-green-50">
            <h3 className="text-lg font-medium text-green-900">Jobs Applied For</h3>
            <p className="text-sm text-green-700">
              {filteredAndSortedJobs.filter(job => !['discovered', 'filtered'].includes(job.status)).length} applications
            </p>
          </div>
          <div className="max-h-96 overflow-y-auto">
            <div className="divide-y divide-gray-200">
              {filteredAndSortedJobs
                .filter(job => !['discovered', 'filtered'].includes(job.status))
                .map((job) => (
                  <JobCard 
                    key={job.id} 
                    job={job} 
                    onStatusChange={(id, status) => handleUpdateJob(id, { status })}
                    onClick={() => setSelectedJob(job)}
                    showApplyButton={false}
                  />
                ))}
              {filteredAndSortedJobs.filter(job => !['discovered', 'filtered'].includes(job.status)).length === 0 && (
                <div className="p-8 text-center">
                  <p className="text-gray-600">No applications yet.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Job Detail Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-bold text-gray-900">{selectedJob.title}</h2>
                <button
                  onClick={() => setSelectedJob(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <span className="sr-only">Close</span>
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-gray-900">Company</h3>
                  <p className="text-gray-600">{selectedJob.company}</p>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900">Location</h3>
                  <p className="text-gray-600">{selectedJob.location}</p>
                </div>
                
                {selectedJob.description && (
                  <div>
                    <h3 className="font-medium text-gray-900">Description</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      {selectedJob.description.length > 500
                        ? `${selectedJob.description.substring(0, 500)}...`
                        : selectedJob.description}
                    </p>
                  </div>
                )}
                
                <div className="flex space-x-4">
                  <a
                    href={selectedJob.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Apply Now
                  </a>
                  <button
                    onClick={() => setSelectedJob(null)}
                    className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};