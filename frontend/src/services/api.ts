import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.1.79:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  description?: string;
  application_url: string;
  platform: string;
  fit_score: number;
  priority: string;
  status: string;
  posted_date?: string;
  discovered_at: string;
  is_remote: boolean;
  is_hybrid: boolean;
}

export interface Application {
  id: number;
  job_id: number;
  status: string;
  method: string;
  submitted_at?: string;
  created_at: string;
  error_message?: string;
}

export interface ScrapeRequest {
  keywords: string[];
  location: string;
  platforms?: string[];
  remote_only: boolean;
  senior_level: boolean;
  salary_min?: number;
}

export interface JobStats {
  total_jobs: number;
  applied_jobs: number;
  high_priority_jobs: number;
  platform_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
  average_fit_score: number;
}

// API functions
export const jobsApi = {
  getJobs: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    platform?: string;
    priority?: string;
    min_fit_score?: number;
  }) => {
    const response = await api.get('/jobs/', { params });
    return response.data;
  },

  getJob: async (id: number) => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },

  updateJob: async (id: number, data: Partial<Job>) => {
    const response = await api.put(`/jobs/${id}`, data);
    return response.data;
  },

  deleteJob: async (id: number) => {
    const response = await api.delete(`/jobs/${id}`);
    return response.data;
  },

  getJobStats: async (): Promise<JobStats> => {
    const response = await api.get('/jobs/stats/summary');
    return response.data;
  },
};

export const scrapersApi = {
  scrapeJobs: async (request: ScrapeRequest) => {
    const response = await api.post('/scrapers/scrape', request);
    return response.data;
  },

  scrapeSinglePlatform: async (platform: string, request: ScrapeRequest) => {
    const response = await api.post(`/scrapers/scrape/${platform}`, request);
    return response.data;
  },

  getScrapingStatus: async () => {
    const response = await api.get('/scrapers/status');
    return response.data;
  },

  testPlatformConnection: async (platform: string) => {
    const response = await api.get(`/scrapers/test/${platform}`);
    return response.data;
  },

  getSupportedPlatforms: async () => {
    const response = await api.get('/scrapers/platforms');
    return response.data;
  },
};

export const applicationsApi = {
  getApplications: async (params?: { skip?: number; limit?: number; status?: string }) => {
    const response = await api.get('/applications/', { params });
    return response.data;
  },

  getApplication: async (id: number) => {
    const response = await api.get(`/applications/${id}`);
    return response.data;
  },

  createApplication: async (data: Partial<Application>) => {
    const response = await api.post('/applications/', data);
    return response.data;
  },

  updateApplication: async (id: number, data: Partial<Application>) => {
    const response = await api.put(`/applications/${id}`, data);
    return response.data;
  },
};

export const emailParserApi = {
  parseEmails: async (data: {
    days_back: number;
    imap_server: string;
    email_user: string;
    email_password: string;
  }) => {
    const response = await api.post('/email-parser/parse-emails', data);
    return response.data;
  },

  parseEmailsFromConfig: async (days_back: number = 7) => {
    const response = await api.post(`/email-parser/parse-emails-from-config?days_back=${days_back}`);
    return response.data;
  },

  testEmailConfig: async () => {
    const response = await api.get('/email-parser/email-config-test');
    return response.data;
  },
};

export const communicationsApi = {
  getCommunications: async (params?: { job_id?: number; type?: string }) => {
    const response = await api.get('/communications/', { params });
    return response.data;
  },

  sendFollowUp: async (jobId: number, message?: string) => {
    const response = await api.post(`/communications/follow-up/${jobId}`, { message });
    return response.data;
  },

  scheduleFollowUp: async (jobId: number, daysDelay: number) => {
    const response = await api.post(`/communications/schedule-follow-up/${jobId}`, {
      days_delay: daysDelay,
    });
    return response.data;
  },
};