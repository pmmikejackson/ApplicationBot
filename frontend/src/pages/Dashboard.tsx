import React, { useState, useEffect } from 'react';
import {
  BriefcaseIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { jobsApi, scrapersApi, JobStats } from '../services/api.ts';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<JobStats | null>(null);
  const [scrapingStatus, setScrapingStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [jobStats, scrapingData] = await Promise.all([
        jobsApi.getJobStats(),
        scrapersApi.getScrapingStatus(),
      ]);
      setStats(jobStats);
      setScrapingStatus(scrapingData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartScraping = async () => {
    try {
      setScraping(true);
      await scrapersApi.scrapeJobs({
        keywords: ['Director of Product Management', 'Senior Product Manager', 'VP Product'],
        location: 'Remote',
        remote_only: true,
        senior_level: true,
      });
      // Reload data after scraping
      setTimeout(loadDashboardData, 2000);
    } catch (error) {
      console.error('Scraping failed:', error);
    } finally {
      setScraping(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Jobs',
      value: stats?.total_jobs || 0,
      icon: BriefcaseIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      name: 'Applications Submitted',
      value: stats?.applied_jobs || 0,
      icon: CheckCircleIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      name: 'High Priority',
      value: stats?.high_priority_jobs || 0,
      icon: ExclamationTriangleIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      name: 'Avg Fit Score',
      value: Math.round(stats?.average_fit_score || 0),
      icon: ClockIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  const platformData = stats?.platform_breakdown
    ? Object.entries(stats.platform_breakdown).map(([platform, count]) => ({
        platform: platform.charAt(0).toUpperCase() + platform.slice(1),
        count,
      }))
    : [];

  const statusData = stats?.status_breakdown
    ? Object.entries(stats.status_breakdown).map(([status, count]) => ({
        status: status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        count,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Overview of your job application automation</p>
        </div>
        <button
          onClick={handleStartScraping}
          disabled={scraping}
          className="bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md flex items-center space-x-2"
        >
          <ArrowPathIcon className={`h-4 w-4 ${scraping ? 'animate-spin' : ''}`} />
          <span>{scraping ? 'Scraping...' : 'Start Job Search'}</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`p-2 rounded-md ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Platform Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Jobs by Platform</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={platformData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="platform" />
                <YAxis tickFormatter={(value) => Math.round(value).toString()} />
                <Tooltip formatter={(value) => [Math.round(Number(value)), 'Jobs']} />
                <Bar dataKey="count" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Application Status</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                  label={({ status, count }) => `${status}: ${count}`}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [Math.round(Number(value)), 'Applications']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
        </div>
        <div className="p-6">
          {scrapingStatus && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-md">
                <div>
                  <p className="font-medium text-gray-900">Last Job Discovery</p>
                  <p className="text-sm text-gray-600">
                    {scrapingStatus.jobs_discovered_today} jobs found today
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    Updated: {new Date(scrapingStatus.last_updated).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};