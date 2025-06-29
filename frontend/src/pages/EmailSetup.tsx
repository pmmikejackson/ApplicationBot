import React, { useState, useEffect } from 'react';
import {
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

interface OAuthStatus {
  configured: boolean;
  status: string;
  email?: string;
  last_check?: string;
  next_steps: string[];
}

export const EmailSetup: React.FC = () => {
  const [oauthStatus, setOauthStatus] = useState<OAuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [authUrl, setAuthUrl] = useState<string>('');
  const [flowId, setFlowId] = useState<string>('');
  const [authPort, setAuthPort] = useState<number>(8080);
  const [step, setStep] = useState<'check' | 'upload' | 'authorize' | 'waiting' | 'complete'>('check');
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    checkOAuthStatus();
    
    // Cleanup polling interval on unmount
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, []);

  const checkOAuthStatus = async () => {
    try {
      const response = await fetch('http://192.168.1.79:8001/api/v1/oauth/oauth-status');
      const data = await response.json();
      setOauthStatus(data);
      
      if (data.configured) {
        setStep('complete');
      } else {
        setStep('upload');
      }
    } catch (error) {
      console.error('Failed to check OAuth status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('credentials_file', file);
      formData.append('port', '8080');

      const response = await fetch('http://192.168.1.79:8001/api/v1/oauth/start-oauth-flow', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.success) {
        setAuthUrl(data.authorization_url);
        setFlowId(data.flow_id);
        setAuthPort(data.port || 8080);
        setStep('authorize');
      } else {
        alert('Failed to start OAuth flow: ' + (data.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed: ' + error);
    } finally {
      setUploading(false);
    }
  };

  const startAuthorizationPolling = () => {
    setStep('waiting');
    setUploading(true);
    
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://192.168.1.79:8001/api/v1/oauth/check-authorization-status/${flowId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
          clearInterval(interval);
          setPollInterval(null);
          setStep('complete');
          setUploading(false);
          checkOAuthStatus();
        } else if (data.status === 'error' || data.status === 'timeout') {
          clearInterval(interval);
          setPollInterval(null);
          setUploading(false);
          alert(`Authorization failed: ${data.message}`);
          setStep('upload');
        }
      } catch (error) {
        console.error('Error checking authorization status:', error);
      }
    }, 3000); // Poll every 3 seconds
    
    setPollInterval(interval);
    
    // Stop polling after 5 minutes
    setTimeout(() => {
      if (interval) {
        clearInterval(interval);
        setPollInterval(null);
        setUploading(false);
        alert('Authorization timeout. Please try again.');
        setStep('upload');
      }
    }, 300000);
  };
  
  const openAuthorizationUrl = () => {
    window.open(authUrl, '_blank');
    startAuthorizationPolling();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Email Setup</h1>
        <p className="text-gray-600">Configure OAuth2 authentication for automatic job email processing</p>
      </div>

      {/* Status Card */}
      {oauthStatus && (
        <div className={`rounded-lg p-6 ${oauthStatus.configured ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
          <div className="flex items-center">
            {oauthStatus.configured ? (
              <CheckCircleIcon className="h-6 w-6 text-green-600 mr-3" />
            ) : (
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600 mr-3" />
            )}
            <div>
              <h3 className="font-medium">{oauthStatus.status}</h3>
              {oauthStatus.email && (
                <p className="text-sm text-gray-600">Connected to: {oauthStatus.email}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Setup Steps */}
      {step === 'upload' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Step 1: Upload OAuth2 Credentials</h2>
          
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-900 mb-2">First, get your OAuth2 credentials:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
                <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="underline">Google Cloud Console</a></li>
                <li>Create or select a project (e.g., "ApplicationBot")</li>
                <li>Enable the Gmail API in APIs &amp; Services &gt; Library</li>
                <li>Go to APIs &amp; Services &gt; Credentials</li>
                <li>Click "+ CREATE CREDENTIALS" &gt; "OAuth client ID"</li>
                <li>Select "Desktop application"</li>
                <li>Download the JSON file</li>
              </ol>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload OAuth2 Credentials JSON File
              </label>
              <div className="flex items-center justify-center w-full">
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <CloudArrowUpIcon className="w-8 h-8 mb-4 text-gray-500" />
                    <p className="mb-2 text-sm text-gray-500">
                      <span className="font-semibold">Click to upload</span> OAuth2 credentials
                    </p>
                    <p className="text-xs text-gray-500">JSON files only</p>
                  </div>
                  <input
                    type="file"
                    className="hidden"
                    accept=".json"
                    onChange={handleFileUpload}
                    disabled={uploading}
                  />
                </label>
              </div>
              {uploading && (
                <div className="mt-2 text-center">
                  <ArrowPathIcon className="h-4 w-4 animate-spin inline mr-2" />
                  Uploading and starting OAuth flow...
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {step === 'authorize' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Step 2: Authorize Application</h2>
          
          <div className="space-y-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-medium text-green-900 mb-2">Ready to authorize!</h3>
              <p className="text-sm text-green-800 mb-3">
                Click the button below to open Google's authorization page in a new tab. 
                Authorization will complete automatically - no need to copy/paste codes.
              </p>
              <p className="text-xs text-green-700 mb-3">
                Local server running on port {authPort} will handle the authorization response.
              </p>
              <button
                onClick={openAuthorizationUrl}
                disabled={uploading}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center space-x-2"
              >
                {uploading && <ArrowPathIcon className="h-4 w-4 animate-spin" />}
                <span>Authorize Gmail Access</span>
              </button>
            </div>
          </div>
        </div>
      )}
      
      {step === 'waiting' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Waiting for Authorization...</h2>
          
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center">
                <ArrowPathIcon className="h-6 w-6 animate-spin text-blue-600 mr-3" />
                <div>
                  <h3 className="font-medium text-blue-900">Please complete authorization in the opened tab</h3>
                  <p className="text-sm text-blue-800 mt-1">
                    After granting permissions, this page will automatically complete the setup.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-gray-600">
                If the authorization tab didn't open, you can 
                <a href={authUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">click here</a>
              </p>
            </div>
          </div>
        </div>
      )}

      {step === 'complete' && oauthStatus?.configured && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">✅ OAuth2 Setup Complete!</h2>
          
          <div className="space-y-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-green-800">
                Email processing is now configured and running automatically every 15 minutes.
              </p>
            </div>

            <div>
              <h3 className="font-medium mb-2">Next Steps:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                {oauthStatus.next_steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ul>
            </div>

            <button
              onClick={checkOAuthStatus}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
            >
              Refresh Status
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="font-medium mb-3">What happens next?</h3>
        <ul className="space-y-2 text-sm text-gray-600">
          <li>• ApplicationBot will check your email every 15 minutes</li>
          <li>• Job alerts from LinkedIn, Indeed, BuiltIn will be automatically parsed</li>
          <li>• New jobs will appear in your dashboard without manual intervention</li>
          <li>• Set up job alerts on those platforms to receive emails at mike@mikejacksonpm.com</li>
        </ul>
      </div>
    </div>
  );
};