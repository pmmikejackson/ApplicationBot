# Email-Based Job Discovery Setup Guide

This guide helps you set up automatic job discovery by parsing job alert emails from major platforms. This approach is safer and more reliable than web scraping.

## 🎯 Overview

ApplicationBot monitors a dedicated email inbox for job alerts from:
- **LinkedIn** (Job alerts, daily/weekly digests)
- **Indeed** (Job alerts, recommended jobs)
- **BuiltIn** (Job recommendations)
- **ZipRecruiter** (Job matches)
- **Other platforms** (easily extensible)

The system runs automatically every 15 minutes, parsing new emails and adding jobs to your dashboard.

## 📧 Step 1: Set Up Job Alerts

### LinkedIn Job Alerts
1. Go to [LinkedIn Jobs](https://www.linkedin.com/jobs/)
2. Search for your target roles (e.g., "Senior Product Manager", "Director Product")
3. Click **"Create alert"** for each search
4. Set frequency to **Daily** or **Weekly**
5. Ensure alerts go to your monitored email address

### Indeed Job Alerts  
1. Go to [Indeed](https://www.indeed.com/)
2. Search for your roles and location
3. Click **"Get new jobs for this search by email"**
4. Set frequency to **Daily**
5. Use the same email address

### BuiltIn Alerts
1. Go to [BuiltIn](https://builtin.com/) for your city
2. Create account and set job preferences
3. Enable email notifications in settings
4. Set to **Daily** or **Real-time**

### ZipRecruiter Alerts
1. Go to [ZipRecruiter](https://www.ziprecruiter.com/)
2. Search and click **"Get email alerts"**
3. Set preferences and frequency

## 🔧 Step 2: Configure ApplicationBot

### Environment Variables (.env file)
```bash
# Email Processing Configuration
EMAIL_PARSING_ENABLED=true

# Gmail Configuration (Recommended)
IMAP_SERVER=imap.gmail.com
IMAP_USER=your-jobs-email@gmail.com
IMAP_PASSWORD=your-app-specific-password

# Alternative Email Providers
# IMAP_SERVER=imap.outlook.com     # For Outlook/Hotmail
# IMAP_SERVER=imap.yahoo.com       # For Yahoo Mail
```

### Gmail App Password Setup (Required for Gmail)
1. **Enable 2-Factor Authentication** on your Google account
2. Go to [Google Account Settings](https://myaccount.google.com/)
3. Navigate to **Security > 2-Step Verification > App passwords**
4. Generate app password for **Mail**
5. Use this 16-character password (not your regular password) in `IMAP_PASSWORD`

### Outlook App Password Setup
1. Go to [Microsoft Account Security](https://account.microsoft.com/security)
2. Enable **Two-step verification**
3. Create **App password** for Mail
4. Use in `IMAP_PASSWORD`

## 📁 Step 3: Email Organization (Recommended)

### Option A: Dedicated Email Address
Create a dedicated email address like `jobs@yourdomain.com` for all job alerts:

**Pros:**
- Clean separation from personal email
- Easy to monitor and debug
- Professional for future business use

**Setup:**
1. Create new Gmail/Outlook account: `yourname.jobs@gmail.com`
2. Configure all job alert platforms to use this email
3. Use this email in ApplicationBot configuration

### Option B: Email Forwarding Rules
Keep using your main email but set up forwarding rules:

**Gmail Forwarding:**
1. Go to Gmail Settings > Forwarding and POP/IMAP
2. Create filter for job alert emails
3. Forward to your ApplicationBot monitored address

**Outlook Rules:**
1. Go to Outlook Settings > Rules
2. Create rule based on sender/subject patterns
3. Forward job-related emails

## 🚀 Step 4: Test and Monitor

### Testing Your Setup
1. **Send test email** to your configured address with job-like content
2. **Check ApplicationBot logs** for processing activity
3. **Verify dashboard** shows new jobs appearing
4. **Monitor for 24-48 hours** to ensure regular processing

### Monitoring Dashboard
The ApplicationBot dashboard shows:
- **Email Processing Status**: Active/Setup Required
- **Last Check Time**: When emails were last processed
- **Processing Frequency**: Every 15 minutes
- **Jobs Found**: Count of jobs discovered via email

### Troubleshooting
- **"Setup Required" status**: Check `.env` configuration
- **"Connection Failed"**: Verify IMAP credentials and server
- **No jobs appearing**: Check email alerts are being sent
- **Duplicate jobs**: Normal - system filters duplicates automatically

## 🔄 Step 5: Email Alert Optimization

### Recommended Alert Frequency
- **Daily alerts**: Best for active job searching
- **Weekly digests**: Good for passive monitoring
- **Real-time alerts**: Only for high-priority roles

### Search Term Optimization
Use specific, targeted searches:
```
✅ Good: "Senior Product Manager Remote"
✅ Good: "Director of Product San Francisco"
❌ Too broad: "Product Manager"
❌ Too broad: "Product"
```

### Platform-Specific Tips

**LinkedIn:**
- Use multiple specific searches rather than one broad search
- Include location preferences
- Set experience level filters

**Indeed:**
- Use salary filters to reduce noise
- Include company size preferences
- Set job type (Full-time, Remote, etc.)

## 📈 Advanced Configuration

### Custom Email Patterns
If you receive job emails from other platforms, you can extend the parser by modifying `email_parser_service.py`:

```python
# Add new platform patterns
'yourplatform': {
    'sender_patterns': ['jobs@yourplatform.com'],
    'subject_patterns': ['job alert', 'new opportunities'],
    'job_title_patterns': [r'<title>([^<]+)</title>'],
    # ... more patterns
}
```

### Multiple Email Sources
Configure multiple email addresses by:
1. Setting up separate IMAP configurations
2. Running multiple parser instances
3. Using email forwarding to consolidate

### Business/Enterprise Setup
For business use:
1. **Custom domain email**: jobs@yourcompany.com
2. **Email security**: SPF, DKIM, DMARC configuration
3. **Backup processing**: Multiple IMAP accounts
4. **Analytics**: Enhanced logging and monitoring

## 🎯 Expected Results

After 24-48 hours of setup, you should see:
- **10-50 new jobs daily** (depends on your search criteria)
- **Automatic job discovery** without manual intervention
- **Clean, organized job pipeline** in your ApplicationBot dashboard
- **No account bans or rate limiting** (unlike web scraping)

## 🆘 Support

If you encounter issues:
1. Check ApplicationBot logs for error messages
2. Verify email alert frequency and content
3. Test IMAP connection with a mail client
4. Review `.env` configuration for typos

This email-based approach provides reliable, sustainable job discovery that scales with your needs!