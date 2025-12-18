import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Load server port from config.json
function getServerPort() {
  const configPaths = [
    path.resolve(__dirname, 'config.json'),
    path.resolve(__dirname, '..', 'config.json'),
    path.resolve(__dirname, '..', 'server', 'config.json'),
  ]
  
  for (const configPath of configPaths) {
    try {
      if (fs.existsSync(configPath)) {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'))
        if (config.server_port) {
          console.log(`Loaded config from ${configPath}`)
          console.log(`Proxying API requests to http://localhost:${config.server_port}`)
          return config.server_port
        }
      }
    } catch (e) {
      // Continue to next path
    }
  }
  
  console.log('No config.json found, using default port 8000')
  return 8000
}

const serverPort = getServerPort()

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': `http://localhost:${serverPort}`,
      '/uploads': `http://localhost:${serverPort}`,
      '/ws': {
        target: `ws://localhost:${serverPort}`,
        ws: true
      }
    }
  }
})