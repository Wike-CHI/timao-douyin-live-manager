---
name: port-rotation
description: Rotate to alternative ports when primary ports are occupied
tools: Read,Write,Glob,Grep,Bash
model: haiku
color: orange
---
Implement port rotation mechanism:

1. Extended port ranges:
   - Frontend: 5180-5200 (extended range)
   - Backend: 8010-8050 (extended range)

2. Rotation logic:
   - Try ports sequentially from extended range
   - Skip ports that are still occupied
   - Maximum 20 attempts per service

3. Update configuration:
   - Modify vite.config.ts with new frontend port
   - Modify .env with new backend port
   - Update tauri.conf.json with both ports

4. Output rotated ports and updated config paths