import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  XMarkIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  EnvelopeIcon,
  EyeIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import { applicationsApi, jobsApi, communicationsApi, Application, Job } from '../services/api.ts';
import { format } from 'date-fns';

const statusColumns = {
  pending: {
    title: 'Pending',
    color: 'bg-yellow-100 border-yellow-300',
    headerColor: 'bg-yellow-50 text-yellow-800',
    icon: ClockIcon,
  },
  submitted: {
    title: 'Submitted',
    color: 'bg-blue-100 border-blue-300',
    headerColor: 'bg-blue-50 text-blue-800',
    icon: CheckCircleIcon,
  },
  under_review: {
    title: 'Under Review',
    color: 'bg-purple-100 border-purple-300',
    headerColor: 'bg-purple-50 text-purple-800',
    icon: EyeIcon,
  },
  interview_scheduled: {
    title: 'Interview',
    color: 'bg-green-100 border-green-300',
    headerColor: 'bg-green-50 text-green-800',
    icon: CheckCircleIcon,
  },
  rejected: {
    title: 'Rejected',
    color: 'bg-red-100 border-red-300',
    headerColor: 'bg-red-50 text-red-800',
    icon: XMarkIcon,
  },
  failed: {
    title: 'Failed',
    color: 'bg-gray-100 border-gray-300',
    headerColor: 'bg-gray-50 text-gray-800',
    icon: ExclamationTriangleIcon,
  },
};

interface ApplicationWithJob extends Application {
  job?: Job;
}

export const Applications: React.FC = () => {
  const [applications, setApplications] = useState<ApplicationWithJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApplication, setSelectedApplication] = useState<ApplicationWithJob | null>(null);
  const [sendingFollowUp, setSendingFollowUp] = useState<number | null>(null);
  const [draggedApp, setDraggedApp] = useState<ApplicationWithJob | null>(null);

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      setLoading(true);
      const apps = await applicationsApi.getApplications();
      
      // Fetch job details for each application
      const appsWithJobs = await Promise.all(
        apps.map(async (app: Application) => {
          try {
            const job = await jobsApi.getJob(app.job_id);
            return { ...app, job };
          } catch (error) {
            console.error(`Failed to load job ${app.job_id}:`, error);
            return app;
          }
        })
      );
      
      setApplications(appsWithJobs);
    } catch (error) {
      console.error('Failed to load applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateApplicationStatus = async (applicationId: number, newStatus: string) => {
    try {
      await applicationsApi.updateApplication(applicationId, { status: newStatus });
      
      // Update local state
      setApplications(prev => 
        prev.map(app => 
          app.id === applicationId 
            ? { ...app, status: newStatus }
            : app
        )
      );
    } catch (error) {
      console.error('Failed to update application status:', error);
    }
  };

  const handleDragStart = (e: React.DragEvent, application: ApplicationWithJob) => {
    setDraggedApp(application);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, newStatus: string) => {
    e.preventDefault();
    
    if (draggedApp && draggedApp.status !== newStatus) {
      updateApplicationStatus(draggedApp.id, newStatus);
    }
    
    setDraggedApp(null);
  };

  const sendFollowUp = async (applicationId: number) => {
    try {
      setSendingFollowUp(applicationId);
      await communicationsApi.sendFollowUp(applicationId);
      // Reload applications to show updated communication status
      loadApplications();
    } catch (error) {
      console.error('Failed to send follow-up:', error);
    } finally {
      setSendingFollowUp(null);
    }
  };

  const getApplicationsByStatus = (status: string) => {
    return applications.filter(app => app.status === status);
  };

  const ApplicationCard = ({ application }: { application: ApplicationWithJob }) => (
    <div
      draggable
      onDragStart={(e) => handleDragStart(e, application)}
      className={`bg-white rounded-lg border-l-4 shadow-sm p-4 mb-3 cursor-move hover:shadow-md transition-shadow ${
        draggedApp?.id === application.id ? 'opacity-50' : ''
      } ${statusColumns[application.status as keyof typeof statusColumns]?.color || 'border-gray-300'}`}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-medium text-gray-900 line-clamp-2">
          {application.job?.title || 'Unknown Position'}
        </h3>
        <span className="text-xs text-gray-500 ml-2">
          #{application.id}
        </span>
      </div>
      
      <p className="text-sm text-gray-600 mb-2">
        {application.job?.company} • {application.job?.location}
      </p>
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{application.method}</span>
        <span>
          {application.submitted_at 
            ? format(new Date(application.submitted_at), 'MMM d')
            : format(new Date(application.created_at), 'MMM d')
          }
        </span>
      </div>
      
      {application.status === 'submitted' && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <button
            onClick={() => sendFollowUp(application.id)}
            disabled={sendingFollowUp === application.id}
            className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
          >
            <EnvelopeIcon className="h-3 w-3" />
            <span>
              {sendingFollowUp === application.id ? 'Sending...' : 'Send Follow-up'}
            </span>
          </button>
        </div>
      )}
      
      {application.error_message && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          {application.error_message}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
          <p className="text-gray-600">Track your job applications through the pipeline</p>
        </div>
        <div className="text-sm text-gray-500">
          Total: {applications.length} applications
        </div>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {Object.entries(statusColumns).map(([status, config]) => {
          const statusApps = getApplicationsByStatus(status);
          const Icon = config.icon;
          
          return (
            <div
              key={status}
              className="bg-gray-50 rounded-lg p-4 min-h-96"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, status)}
            >
              {/* Column Header */}
              <div className={`rounded-lg p-3 mb-4 ${config.headerColor}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Icon className="h-4 w-4" />
                    <h3 className="font-medium text-sm">{config.title}</h3>
                  </div>
                  <span className="text-xs font-medium bg-white px-2 py-1 rounded-full">
                    {statusApps.length}
                  </span>
                </div>
              </div>

              {/* Applications */}
              <div className="space-y-3">
                {statusApps.map((application) => (
                  <ApplicationCard key={application.id} application={application} />
                ))}
                
                {statusApps.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    <PlusIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No applications</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-blue-600">
            {getApplicationsByStatus('submitted').length}
          </div>
          <div className="text-sm text-gray-600">Submitted</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-purple-600">
            {getApplicationsByStatus('under_review').length}
          </div>
          <div className="text-sm text-gray-600">Under Review</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-green-600">
            {getApplicationsByStatus('interview_scheduled').length}
          </div>
          <div className="text-sm text-gray-600">Interviews</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-gray-600">
            {applications.length}
          </div>
          <div className="text-sm text-gray-600">Total</div>
        </div>
      </div>
    </div>
  );
};