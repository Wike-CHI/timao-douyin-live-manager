---
name: port-detection
description: Detect available ports for frontend and backend
tools: Read,Write,Glob,Grep,Bash
model: haiku
color: blue
---
Create a script to detect available ports:

1. Define port ranges:
   - Frontend: 5173, 5174, 5175, 5176, 5177
   - Backend: 8000, 8001, 8002, 8003, 8004

2. For each port in range:
   - Check if port is available using socket connection
   - Return first available port in each range

3. Output format:
   {
     "frontendPort": <available port or null>,
     "backendPort": <available port or null>,
     "checked": {
       "frontend": [list of checked ports],
       "backend": [list of checked ports]
     }
   }

4. Save the detection script to: scripts/port-detection.js