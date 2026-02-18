---
name: backend-start
description: Start backend server on selected port
tools: Read,Write,Bash,Glob
model: haiku
color: green
---
Start the backend server:

1. Read current port from:
   - .env file or
   - scripts/port-detection.js output

2. Start backend with:
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port <backendPort>
   ```

3. Verify backend is running:
   - Check if server responds on http://localhost:<backendPort>
   - Return status: running/stopped/error

4. Log the startup to: logs/backend-startup.log