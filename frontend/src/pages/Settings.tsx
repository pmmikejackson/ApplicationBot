import React, { useState } from 'react';
import {
  UserIcon,
  CogIcon,
  DocumentTextIcon,
  KeyIcon,
  BellIcon,
} from '@heroicons/react/24/outline';

type SettingsTab = 'profile' | 'preferences' | 'documents' | 'credentials' | 'notifications';

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [profile, setProfile] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    linkedinUrl: '',
    portfolioUrl: '',
    yearsExperience: 5,
    targetTitles: ['Senior Product Manager', 'Director of Product Management'],
    skills: ['Product Management', 'Data Analytics', 'Agile', 'SQL'],
    salaryMin: 120000,
    salaryMax: 180000,
    remotePreference: true,
    locationPreferences: ['Remote', 'San Francisco', 'New York'],
  });

  const [credentials, setCredentials] = useState({
    linkedinUsername: '',
    linkedinPassword: '',
    indeedUsername: '',
    indeedPassword: '',
  });

  const [preferences, setPreferences] = useState({
    autoApplyEnabled: false,
    maxApplicationsPerDay: 5,
    followUpDays: 7,
    emailNotifications: true,
    slackNotifications: false,
  });

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'preferences', name: 'Job Preferences', icon: CogIcon },
    { id: 'documents', name: 'Documents', icon: DocumentTextIcon },
    { id: 'credentials', name: 'Platform Credentials', icon: KeyIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
  ];

  const handleSave = () => {
    // TODO: Implement save functionality
    alert('Settings saved successfully!');
  };

  const renderProfileTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            First Name
          </label>
          <input
            type="text"
            value={profile.firstName}
            onChange={(e) => setProfile({ ...profile, firstName: e.target.value })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Last Name
          </label>
          <input
            type="text"
            value={profile.lastName}
            onChange={(e) => setProfile({ ...profile, lastName: e.target.value })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input
            type="email"
            value={profile.email}
            onChange={(e) => setProfile({ ...profile, email: e.target.value })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone
          </label>
          <input
            type="tel"
            value={profile.phone}
            onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            LinkedIn URL
          </label>
          <input
            type="url"
            value={profile.linkedinUrl}
            onChange={(e) => setProfile({ ...profile, linkedinUrl: e.target.value })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Portfolio URL
          </label>
          <input
            type="url"
            value={profile.portfolioUrl}
            onChange={(e) => setProfile({ ...profile, portfolioUrl: e.target.value })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Years of Experience
        </label>
        <input
          type="number"
          min="0"
          max="50"
          value={profile.yearsExperience}
          onChange={(e) => setProfile({ ...profile, yearsExperience: parseInt(e.target.value) })}
          className="w-32 border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
    </div>
  );

  const renderPreferencesTab = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Job Titles
        </label>
        <div className="space-y-2">
          {profile.targetTitles.map((title, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="text"
                value={title}
                onChange={(e) => {
                  const newTitles = [...profile.targetTitles];
                  newTitles[index] = e.target.value;
                  setProfile({ ...profile, targetTitles: newTitles });
                }}
                className="flex-1 border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={() => {
                  const newTitles = profile.targetTitles.filter((_, i) => i !== index);
                  setProfile({ ...profile, targetTitles: newTitles });
                }}
                className="text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
          ))}
          <button
            onClick={() => setProfile({ ...profile, targetTitles: [...profile.targetTitles, ''] })}
            className="text-primary-600 hover:text-primary-800 text-sm"
          >
            + Add Title
          </button>
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Skills
        </label>
        <div className="space-y-2">
          {profile.skills.map((skill, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="text"
                value={skill}
                onChange={(e) => {
                  const newSkills = [...profile.skills];
                  newSkills[index] = e.target.value;
                  setProfile({ ...profile, skills: newSkills });
                }}
                className="flex-1 border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={() => {
                  const newSkills = profile.skills.filter((_, i) => i !== index);
                  setProfile({ ...profile, skills: newSkills });
                }}
                className="text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
          ))}
          <button
            onClick={() => setProfile({ ...profile, skills: [...profile.skills, ''] })}
            className="text-primary-600 hover:text-primary-800 text-sm"
          >
            + Add Skill
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Salary ($)
          </label>
          <input
            type="number"
            min="0"
            step="1000"
            value={profile.salaryMin}
            onChange={(e) => setProfile({ ...profile, salaryMin: parseInt(e.target.value) })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Maximum Salary ($)
          </label>
          <input
            type="number"
            min="0"
            step="1000"
            value={profile.salaryMax}
            onChange={(e) => setProfile({ ...profile, salaryMax: parseInt(e.target.value) })}
            className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>
      
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={profile.remotePreference}
            onChange={(e) => setProfile({ ...profile, remotePreference: e.target.checked })}
            className="mr-2"
          />
          <span className="text-sm font-medium text-gray-700">Prefer remote work</span>
        </label>
      </div>
      
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={preferences.autoApplyEnabled}
            onChange={(e) => setPreferences({ ...preferences, autoApplyEnabled: e.target.checked })}
            className="mr-2"
          />
          <span className="text-sm font-medium text-gray-700">Enable automatic job applications</span>
        </label>
        <p className="text-sm text-gray-600 mt-1">
          Automatically apply to jobs marked as "Must Apply" with your default resume and cover letter.
        </p>
      </div>
    </div>
  );

  const renderDocumentsTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Resume Templates</h3>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">Upload your resume template</p>
          <input
            type="file"
            accept=".pdf,.doc,.docx"
            className="mt-2"
          />
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Cover Letter Template</h3>
        <textarea
          rows={8}
          placeholder="Write your cover letter template here. Use placeholders like {company} and {position} for dynamic content."
          className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
    </div>
  );

  const renderCredentialsTab = () => (
    <div className="space-y-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <p className="text-sm text-yellow-800">
          <strong>Note:</strong> Your credentials are encrypted and stored securely. They are only used for automated job applications.
        </p>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">LinkedIn</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username/Email
            </label>
            <input
              type="text"
              value={credentials.linkedinUsername}
              onChange={(e) => setCredentials({ ...credentials, linkedinUsername: e.target.value })}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={credentials.linkedinPassword}
              onChange={(e) => setCredentials({ ...credentials, linkedinPassword: e.target.value })}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Indeed</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username/Email
            </label>
            <input
              type="text"
              value={credentials.indeedUsername}
              onChange={(e) => setCredentials({ ...credentials, indeedUsername: e.target.value })}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={credentials.indeedPassword}
              onChange={(e) => setCredentials({ ...credentials, indeedPassword: e.target.value })}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationsTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Email Notifications</h3>
        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={preferences.emailNotifications}
              onChange={(e) => setPreferences({ ...preferences, emailNotifications: e.target.checked })}
              className="mr-3"
            />
            <div>
              <span className="text-sm font-medium text-gray-700">Daily job digest</span>
              <p className="text-sm text-gray-600">Receive a summary of new jobs found</p>
            </div>
          </label>
          
          <label className="flex items-center">
            <input type="checkbox" className="mr-3" />
            <div>
              <span className="text-sm font-medium text-gray-700">Application confirmations</span>
              <p className="text-sm text-gray-600">Get notified when applications are submitted</p>
            </div>
          </label>
          
          <label className="flex items-center">
            <input type="checkbox" className="mr-3" />
            <div>
              <span className="text-sm font-medium text-gray-700">Interview invitations</span>
              <p className="text-sm text-gray-600">Alert when interview requests are received</p>
            </div>
          </label>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Automation Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Maximum Applications Per Day
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={preferences.maxApplicationsPerDay}
              onChange={(e) => setPreferences({ ...preferences, maxApplicationsPerDay: parseInt(e.target.value) })}
              className="w-32 border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Follow-up Email Delay (days)
            </label>
            <input
              type="number"
              min="1"
              max="30"
              value={preferences.followUpDays}
              onChange={(e) => setPreferences({ ...preferences, followUpDays: parseInt(e.target.value) })}
              className="w-32 border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileTab();
      case 'preferences':
        return renderPreferencesTab();
      case 'documents':
        return renderDocumentsTab();
      case 'credentials':
        return renderCredentialsTab();
      case 'notifications':
        return renderNotificationsTab();
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your profile and application preferences</p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="flex">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 border-r border-gray-200">
            <nav className="space-y-1 p-4">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as SettingsTab)}
                  className={`${
                    activeTab === tab.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  } group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full text-left`}
                >
                  <tab.icon
                    className={`${
                      activeTab === tab.id ? 'text-primary-500' : 'text-gray-400'
                    } mr-3 h-5 w-5`}
                  />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6">
            {renderTabContent()}
            
            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  type="button"
                  className="bg-primary-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};