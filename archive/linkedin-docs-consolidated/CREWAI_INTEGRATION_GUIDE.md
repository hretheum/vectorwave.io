# CrewAI LinkedIn Integration Guide

## 🎯 Overview

Ten dokument opisuje integrację LinkedIn automation module z CrewAI editorial flow. Moduł obsługuje automatyczne publikowanie postów z PDF, scheduling oraz error recovery.

## 🚀 Quick Integration

### 1. Basic Integration

```python
# crewai_linkedin_task.py
from crewai import Task, Agent
import subprocess
import json
from datetime import datetime, timezone

class LinkedInPublishTask(Task):
    """Task for publishing content to LinkedIn"""
    
    def __init__(self, linkedin_module_path="/path/to/linkedin"):
        self.linkedin_path = linkedin_module_path
        self.account = "production"
        
    def execute(self, content, media_path=None, schedule_date=None):
        """
        Publish content to LinkedIn
        
        Args:
            content (str): Post content (max 3000 chars)
            media_path (str): Optional path to PDF file
            schedule_date (datetime): Optional schedule date (None = immediate)
        """
        # Build command
        cmd = [
            "node",
            f"{self.linkedin_path}/scripts/publish_post.js",
            "--content", content,
            "--account", self.account
        ]
        
        # Add media if provided
        if media_path:
            cmd.extend(["--pdf", media_path])
            
        # Handle scheduling
        if schedule_date:
            iso_date = schedule_date.isoformat()
            cmd.extend(["--schedule", iso_date])
        else:
            cmd.append("--immediate")
            
        # Execute
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if "PUBLICATION COMPLETED!" in result.stdout:
                return {
                    "success": True,
                    "method": "scheduled" if schedule_date else "immediate",
                    "output": result.stdout
                }
            else:
                raise Exception(f"Publication failed: {result.stderr}")
                
        except Exception as e:
            # Auto-diagnostic on selector errors
            if "selector" in str(e) or "not found" in str(e):
                self._run_diagnostic()
                # Retry once
                return self.execute(content, media_path, schedule_date)
            raise
            
    def _run_diagnostic(self):
        """Run LinkedIn selector diagnostic"""
        subprocess.run([
            "node",
            f"{self.linkedin_path}/scripts/linkedin-cli.js",
            "diagnose",
            "--fix"
        ])

# Usage in CrewAI flow
linkedin_task = LinkedInPublishTask(
    linkedin_module_path="/Users/your-user/dev/bezrobocie/vector-wave/linkedin"
)

# Immediate publish
result = linkedin_task.execute(
    content="🚀 Exciting AI update from our team!",
    media_path="/path/to/presentation.pdf"
)

# Scheduled publish
from datetime import datetime, timedelta
schedule_time = datetime.now(timezone.utc) + timedelta(hours=24)
result = linkedin_task.execute(
    content="📅 Tomorrow's AI insights",
    schedule_date=schedule_time
)
```

### 2. Advanced CrewAI Agent Integration

```python
# crewai_linkedin_agent.py
from crewai import Agent, Task, Crew
from langchain.tools import Tool
import os
import sys

# Add LinkedIn module to path
sys.path.append('/path/to/linkedin/scripts')

class LinkedInPublisherAgent(Agent):
    """Agent responsible for LinkedIn content publishing"""
    
    def __init__(self, linkedin_path):
        self.linkedin_path = linkedin_path
        
        # Define tools
        publish_tool = Tool(
            name="publish_to_linkedin",
            func=self._publish_to_linkedin,
            description="Publish content to LinkedIn with optional PDF and scheduling"
        )
        
        validate_tool = Tool(
            name="validate_linkedin_session",
            func=self._validate_session,
            description="Validate LinkedIn session is active"
        )
        
        super().__init__(
            role="LinkedIn Publisher",
            goal="Publish engaging content to LinkedIn at optimal times",
            backstory="Expert in LinkedIn content strategy and automation",
            tools=[publish_tool, validate_tool],
            verbose=True
        )
        
    def _publish_to_linkedin(self, content: str, **kwargs) -> dict:
        """Tool function for publishing"""
        from publish_post import LinkedInPublisher
        
        publisher = LinkedInPublisher(accountName='production')
        
        options = {
            'content': content,
            'immediate': kwargs.get('immediate', True),
            'pdfPath': kwargs.get('pdf_path'),
            'scheduleTime': kwargs.get('schedule_time')
        }
        
        try:
            result = publisher.publishPost(options)
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def _validate_session(self) -> dict:
        """Tool function for session validation"""
        from session_manager import SessionManager
        
        manager = SessionManager(accountName='production')
        result = manager.validateSession()
        
        return {
            'valid': result['success'],
            'message': result.get('error', 'Session is valid')
        }

# Example CrewAI workflow
def create_linkedin_crew():
    # Content creation agent
    content_agent = Agent(
        role="Content Creator",
        goal="Create engaging LinkedIn content",
        backstory="Expert copywriter specializing in B2B content"
    )
    
    # LinkedIn publisher agent
    publisher_agent = LinkedInPublisherAgent(
        linkedin_path="/path/to/linkedin"
    )
    
    # Tasks
    create_content_task = Task(
        description="Create LinkedIn post about AI advancements",
        agent=content_agent,
        expected_output="LinkedIn post content (max 3000 chars)"
    )
    
    publish_task = Task(
        description="Publish the content to LinkedIn",
        agent=publisher_agent,
        context=[create_content_task],
        expected_output="Publication confirmation"
    )
    
    # Create crew
    crew = Crew(
        agents=[content_agent, publisher_agent],
        tasks=[create_content_task, publish_task],
        verbose=True
    )
    
    return crew

# Execute workflow
crew = create_linkedin_crew()
result = crew.kickoff()
```

### 3. n8n Integration Example

```javascript
// n8n Function Node
const linkedinPath = '/path/to/linkedin';
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

// Helper function
async function publishToLinkedIn(item) {
    const { content, pdfUrl, scheduleTime } = item;
    
    // Download PDF if URL provided
    let pdfPath = null;
    if (pdfUrl) {
        const response = await $http.get(pdfUrl, { encoding: 'binary' });
        pdfPath = `/tmp/linkedin-${Date.now()}.pdf`;
        await $fs.writeFile(pdfPath, response.body, 'binary');
    }
    
    // Build command
    let command = `node ${linkedinPath}/scripts/publish_post.js`;
    command += ` --content "${content.replace(/"/g, '\\"')}"`;
    
    if (pdfPath) {
        command += ` --pdf "${pdfPath}"`;
    }
    
    if (scheduleTime) {
        command += ` --schedule "${scheduleTime}"`;
    } else {
        command += ` --immediate`;
    }
    
    try {
        const { stdout } = await execAsync(command);
        
        // Cleanup
        if (pdfPath) {
            await $fs.unlink(pdfPath);
        }
        
        return {
            success: stdout.includes('PUBLICATION COMPLETED!'),
            output: stdout
        };
    } catch (error) {
        // Auto-diagnostic
        if (error.message.includes('selector')) {
            await execAsync(`node ${linkedinPath}/scripts/linkedin-cli.js diagnose --fix`);
            // Retry
            return publishToLinkedIn(item);
        }
        throw error;
    }
}

// Process items
const results = [];
for (const item of $input.all()) {
    try {
        const result = await publishToLinkedIn(item.json);
        results.push({
            json: {
                ...item.json,
                linkedin: result,
                publishedAt: new Date().toISOString()
            }
        });
    } catch (error) {
        results.push({
            json: {
                ...item.json,
                error: error.message,
                failedAt: new Date().toISOString()
            }
        });
    }
}

return results;
```

## 📋 API Contract

### Input Format

```typescript
interface LinkedInPublishRequest {
    content: string;           // Post content (max 3000 characters)
    mediaPath?: string;        // Optional: Path to PDF file
    scheduledDate?: string;    // Optional: ISO 8601 date (null = immediate)
}
```

### Output Format

```typescript
interface LinkedInPublishResponse {
    success: boolean;
    method: 'immediate' | 'scheduled';
    scheduledFor?: string;     // ISO date if scheduled
    postUrl?: string;          // LinkedIn post URL (if available)
    publishedAt: string;       // ISO timestamp
    error?: string;            // Error message if failed
}
```

## 🔧 Configuration

### 1. Environment Setup

```bash
# In your CrewAI project
cd your-crewai-project

# Install LinkedIn module dependencies
cd /path/to/linkedin
npm install

# Create production session
node scripts/linkedin-cli.js session create --account production

# Validate it works
node scripts/linkedin-cli.js session validate --account production
```

### 2. CrewAI Config

```yaml
# crewai_config.yaml
linkedin:
  module_path: "/path/to/linkedin"
  account: "production"
  retry_on_error: true
  auto_diagnostic: true
  
scheduling:
  timezone: "Europe/Warsaw"
  optimal_times:
    - "09:00"
    - "12:00"
    - "17:00"
  avoid_weekends: true
```

### 3. Error Handling

```python
# Robust error handling
class LinkedInPublishError(Exception):
    """Custom exception for LinkedIn publishing"""
    pass

def publish_with_retry(content, max_retries=3):
    """Publish with automatic retry and diagnostic"""
    
    for attempt in range(max_retries):
        try:
            # Attempt publication
            result = linkedin_task.execute(content)
            
            if result['success']:
                return result
                
        except Exception as e:
            error_msg = str(e)
            
            # Session expired - need manual intervention
            if "Session expired" in error_msg:
                raise LinkedInPublishError(
                    "LinkedIn session expired. "
                    "Run: linkedin-cli session create --account production"
                )
                
            # Selector error - run diagnostic
            if "selector" in error_msg or "not found" in error_msg:
                print(f"Attempt {attempt + 1}: Running diagnostic...")
                subprocess.run([
                    "node", 
                    f"{LINKEDIN_PATH}/scripts/linkedin-cli.js", 
                    "diagnose", 
                    "--fix"
                ])
                continue
                
            # Other errors
            if attempt == max_retries - 1:
                raise LinkedInPublishError(f"Failed after {max_retries} attempts: {error_msg}")
                
    return {'success': False, 'error': 'Max retries exceeded'}
```

## 📊 Monitoring & Logging

### 1. Health Check Integration

```python
# health_check.py
def check_linkedin_health():
    """Check LinkedIn module health"""
    
    try:
        # Validate session
        result = subprocess.run([
            "node",
            f"{LINKEDIN_PATH}/scripts/linkedin-cli.js",
            "session",
            "validate",
            "--account",
            "production"
        ], capture_output=True, text=True)
        
        session_valid = "Session is valid" in result.stdout
        
        # Run diagnostic
        diag_result = subprocess.run([
            "node",
            f"{LINKEDIN_PATH}/scripts/linkedin-cli.js",
            "diagnose"
        ], capture_output=True, text=True)
        
        selectors_ok = "All selectors are working" in diag_result.stdout
        
        return {
            'healthy': session_valid and selectors_ok,
            'session_valid': session_valid,
            'selectors_ok': selectors_ok,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
```

### 2. Logging Best Practices

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('linkedin_publisher')

def publish_with_logging(content, **kwargs):
    """Publish with comprehensive logging"""
    
    logger.info(f"Starting LinkedIn publication for content: {content[:50]}...")
    
    try:
        # Log parameters
        logger.debug(f"Parameters: {kwargs}")
        
        # Execute
        result = linkedin_task.execute(content, **kwargs)
        
        # Log success
        logger.info(f"Publication successful: {result}")
        
        # Track metrics
        track_publication_metric(
            success=True,
            method=result.get('method', 'unknown'),
            has_media=kwargs.get('media_path') is not None
        )
        
        return result
        
    except Exception as e:
        # Log failure
        logger.error(f"Publication failed: {str(e)}", exc_info=True)
        
        # Track failure metric
        track_publication_metric(
            success=False,
            error_type=type(e).__name__
        )
        
        raise
```

## 🚨 Common Integration Issues

### 1. Path Issues

```python
# Always use absolute paths
import os

LINKEDIN_PATH = os.path.abspath("/path/to/linkedin")
PDF_PATH = os.path.abspath(pdf_file)
```

### 2. Timezone Handling

```python
from datetime import datetime, timezone
import pytz

# Always use UTC internally
utc_time = datetime.now(timezone.utc)

# Convert to LinkedIn account timezone if needed
warsaw_tz = pytz.timezone('Europe/Warsaw')
local_time = utc_time.astimezone(warsaw_tz)
```

### 3. Content Validation

```python
def validate_linkedin_content(content):
    """Validate content meets LinkedIn requirements"""
    
    # Length check
    if len(content) > 3000:
        raise ValueError(f"Content too long: {len(content)} chars (max 3000)")
        
    # Hashtag check
    hashtags = len([w for w in content.split() if w.startswith('#')])
    if hashtags > 30:
        raise ValueError(f"Too many hashtags: {hashtags} (max 30)")
        
    # URL check
    urls = len([w for w in content.split() if w.startswith(('http://', 'https://'))])
    if urls > 3:
        raise ValueError(f"Too many URLs: {urls} (max 3)")
        
    return True
```

## 📚 Complete Example

```python
# complete_crewai_linkedin_integration.py
from crewai import Agent, Task, Crew
from datetime import datetime, timezone, timedelta
import subprocess
import os
import logging

# Configuration
LINKEDIN_PATH = "/path/to/linkedin"
ACCOUNT = "production"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInPublisherAgent(Agent):
    """Specialized agent for LinkedIn publishing"""
    
    def __init__(self):
        super().__init__(
            role="LinkedIn Content Publisher",
            goal="Publish high-quality content to LinkedIn at optimal times",
            backstory="""You are an expert in LinkedIn content strategy and 
                        automation. You understand the best times to post and 
                        how to maximize engagement.""",
            verbose=True
        )
        
    def publish_content(self, content, schedule_hours_ahead=None, pdf_path=None):
        """
        Main publishing method with full error handling
        """
        try:
            # Validate content
            self._validate_content(content)
            
            # Prepare command
            cmd = [
                "node",
                f"{LINKEDIN_PATH}/scripts/publish_post.js",
                "--content", content,
                "--account", ACCOUNT
            ]
            
            # Add PDF if provided
            if pdf_path and os.path.exists(pdf_path):
                cmd.extend(["--pdf", pdf_path])
                logger.info(f"Including PDF: {pdf_path}")
                
            # Handle scheduling
            if schedule_hours_ahead:
                schedule_time = datetime.now(timezone.utc) + timedelta(hours=schedule_hours_ahead)
                cmd.extend(["--schedule", schedule_time.isoformat()])
                logger.info(f"Scheduling for: {schedule_time}")
            else:
                cmd.append("--immediate")
                logger.info("Publishing immediately")
                
            # Execute
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check result
            if "PUBLICATION COMPLETED!" in result.stdout:
                logger.info("Publication successful!")
                return {
                    'success': True,
                    'output': result.stdout,
                    'scheduled_for': schedule_time.isoformat() if schedule_hours_ahead else None
                }
            else:
                raise Exception(f"Publication failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error during publication: {str(e)}")
            
            # Auto-recovery for selector errors
            if self._is_selector_error(str(e)):
                logger.info("Running automatic diagnostic...")
                self._run_diagnostic()
                
                # Retry once
                logger.info("Retrying publication...")
                return self.publish_content(content, schedule_hours_ahead, pdf_path)
                
            raise
            
    def _validate_content(self, content):
        """Validate content meets LinkedIn requirements"""
        if len(content) > 3000:
            raise ValueError(f"Content too long: {len(content)} chars")
            
        hashtag_count = content.count('#')
        if hashtag_count > 30:
            raise ValueError(f"Too many hashtags: {hashtag_count}")
            
    def _is_selector_error(self, error_msg):
        """Check if error is selector-related"""
        selector_keywords = ['selector', 'not found', 'element', 'timeout']
        return any(keyword in error_msg.lower() for keyword in selector_keywords)
        
    def _run_diagnostic(self):
        """Run LinkedIn diagnostic tool"""
        subprocess.run([
            "node",
            f"{LINKEDIN_PATH}/scripts/linkedin-cli.js",
            "diagnose",
            "--fix"
        ], check=True)

# Example usage
def main():
    # Create publisher agent
    publisher = LinkedInPublisherAgent()
    
    # Example 1: Immediate publication
    result = publisher.publish_content(
        content="🚀 Exciting news from our AI team! #AI #Innovation",
        pdf_path="/path/to/presentation.pdf"
    )
    print("Immediate publication result:", result)
    
    # Example 2: Scheduled publication
    result = publisher.publish_content(
        content="📅 Join us tomorrow for AI insights! #AI #Tech",
        schedule_hours_ahead=24
    )
    print("Scheduled publication result:", result)

if __name__ == "__main__":
    main()
```

## 🎯 Best Practices

1. **Always validate sessions** before publishing
2. **Use absolute paths** for all file references
3. **Handle timezones properly** - use UTC internally
4. **Implement retry logic** with exponential backoff
5. **Log everything** for debugging
6. **Monitor health** regularly
7. **Test with dev account** before production
8. **Deploy with Docker** for consistent environment
9. **Use CI/CD pipeline** for automated testing
10. **Backup sessions regularly** for quick recovery

## 🐳 Docker Integration

### Running in Container

```python
# Execute CLI in Docker container
import subprocess

def publish_in_docker(content, schedule_time=None):
    """Publish using dockerized LinkedIn module"""
    
    cmd = [
        "docker", "exec", "linkedin-module-local",
        "node", "scripts/linkedin-cli.js", "publish",
        "-c", content
    ]
    
    if schedule_time:
        cmd.extend(["-s", schedule_time])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
```

### Health Check Integration

```python
# Monitor LinkedIn module health
import requests

def check_linkedin_health():
    """Check if LinkedIn module is healthy"""
    
    # Docker internal health check
    health_url = "http://localhost:8090/health"
    
    # Uptime Kuma monitoring
    monitor_url = "http://localhost:3001/api/status-page/linkedin"
    
    try:
        # Check both endpoints
        module_health = requests.get(health_url).json()
        monitor_status = requests.get(monitor_url).json()
        
        return {
            'module': module_health,
            'monitor': monitor_status,
            'overall': module_health.get('status') == 'ok'
        }
    except Exception as e:
        return {'error': str(e), 'overall': False}
```

## 🔗 Additional Resources

### Project Documentation
- [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) - Complete project overview
- [LinkedIn Module README](./README.md) - Getting started guide
- [CLI Documentation](./CLI_DOCUMENTATION.md) - CLI reference
- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md) - Production deployment
- [CI/CD Guide](./docs/CI_CD_GUIDE.md) - Pipeline setup

### Technical Reports
- [Implementation Report](./IMPLEMENTATION_REPORT.md) - Browser automation details
- [Deployment Report](./DEPLOYMENT_REPORT.md) - Docker & CI/CD implementation
- [Atomic Tasks](./LINKEDIN_MODULE_ATOMIC_TASKS.md) - Development roadmap

### External Documentation
- [CrewAI Documentation](https://docs.crewai.com/)
- [n8n Documentation](https://docs.n8n.io/)
- [Stagehand Documentation](https://github.com/browserbase/stagehand)

---

**Version**: 2.1.0  
**Last Updated**: 2025-01-30  
**Support**: For issues, check diagnostics first with `linkedin-cli diagnose`