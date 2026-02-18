---
name: frontend-start
description: Start frontend dev server on selected port
tools: Read,Write,Bash,Glob
model: haiku
color: purple
---
Start the frontend development server:

1. Read current port from:
   - vite.config.ts or
   - scripts/port-detection.js output

2. Start frontend with:
   ```bash
   cd frontend
   npm run dev -- --port <frontendPort>
   ```

3. Verify frontend is running:
   - Check if server responds on http://localhost:<frontendPort>
   - Return status: running/stopped/error

4. Log the startup to: logs/frontend-startup.log