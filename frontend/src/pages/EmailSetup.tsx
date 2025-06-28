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
  const [authCode, setAuthCode] = useState<string>('');
  const [step, setStep] = useState<'check' | 'upload' | 'authorize' | 'complete'>('check');

  useEffect(() => {
    checkOAuthStatus();
  }, []);

  const checkOAuthStatus = async () => {
    try {
      const response = await fetch('http://192.168.1.79:8000/api/v1/oauth/oauth-status');
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
      formData.append('redirect_uri', 'urn:ietf:wg:oauth:2.0:oob');

      const response = await fetch('http://192.168.1.79:8000/api/v1/oauth/start-oauth-flow', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.success) {
        setAuthUrl(data.authorization_url);
        setFlowId(data.flow_id);
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

  const completeOAuthFlow = async () => {
    if (!authCode.trim()) {
      alert('Please enter the authorization code');
      return;
    }

    try {
      setUploading(true);
      const response = await fetch('http://192.168.1.79:8000/api/v1/oauth/complete-oauth-flow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          authorization_code: authCode,
          flow_id: flowId,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setStep('complete');
        checkOAuthStatus(); // Refresh status
        alert('OAuth2 setup completed successfully!');
      } else {
        alert('Failed to complete OAuth flow: ' + (data.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('OAuth completion failed:', error);
      alert('OAuth completion failed: ' + error);
    } finally {
      setUploading(false);
    }
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
                <li>Enable the Gmail API in APIs & Services > Library</li>
                <li>Go to APIs & Services > Credentials</li>
                <li>Click "+ CREATE CREDENTIALS" > "OAuth client ID"</li>
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
              <h3 className="font-medium text-green-900 mb-2">Authorization URL generated!</h3>
              <p className="text-sm text-green-800 mb-3">
                Click the link below to authorize ApplicationBot to access your Gmail:
              </p>
              <a
                href={authUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Authorize Gmail Access
              </a>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Authorization Code
              </label>
              <input
                type="text"
                value={authCode}
                onChange={(e) => setAuthCode(e.target.value)}
                placeholder="Paste the authorization code here"
                className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                After clicking "Authorize Gmail Access", copy the code and paste it here
              </p>
            </div>

            <button
              onClick={completeOAuthFlow}
              disabled={uploading || !authCode.trim()}
              className="bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md flex items-center space-x-2"
            >
              {uploading && <ArrowPathIcon className="h-4 w-4 animate-spin" />}
              <span>Complete Setup</span>
            </button>
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