# Digital Signage System

A complete digital signage solution with a central control server and lightweight player clients.

## Features

- **Content Groups**: Organize media (images, videos) into logical groups (e.g., "Gym Promotions", "Check-in Info")
- **Schedule Groups**: Define when content plays with flexible scheduling
- **Device Management**: Control individual displays with mix-and-match content and schedule assignments
- **Default Display**: Configurable logo and background for when no content is scheduled
- **Real-time Sync**: WebSocket-based instant updates to players
- **Local Caching**: Players download and store content locally - no streaming required
- **Modern UI**: Clean, professional web interface

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Control Server                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Web UI    │  │  REST API   │  │  WebSocket Server   │  │
│  │  (React)    │  │  (FastAPI)  │  │  (Real-time sync)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                          │                                   │
│                    ┌─────┴─────┐                             │
│                    │  SQLite   │                             │
│                    │  Database │                             │
│                    └───────────┘                             │
└─────────────────────────────────────────────────────────────┘
                           │
                    Local Network
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
┌────┴────┐          ┌────┴────┐          ┌────┴────┐
│ Player  │          │ Player  │          │ Player  │
│   #1    │          │   #2    │          │   #3    │
└─────────┘          └─────────┘          └─────────┘
```

## Quick Start

### Server Setup

1. **Install Dependencies**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

2. **Start the Server**
   ```bash
   python main.py
   ```
   The server runs on `http://localhost:8000`

3. **Start the Web UI** (Development)
   ```bash
   cd web-ui
   npm install
   npm run dev
   ```
   Access the UI at `http://localhost:5173`

### Player Setup (Raspberry Pi or similar)

1. **Copy the player script**
   ```bash
   scp player/player.py pi@your-pi:/home/pi/
   ```

2. **Run setup on the player device**
   ```bash
   python3 player.py --setup
   ```
   Enter:
   - Server URL (e.g., `http://192.168.1.100:8000`)
   - Device Key (get this from the web UI after creating a device)

3. **Start the player**
   ```bash
   python3 player.py
   ```

## Configuration

### Content Groups vs Schedule Groups

**Content Groups** are collections of media:
- "Gym Promotions" - videos and images about gym classes
- "Check-in Welcome" - welcome messages for the check-in area
- "Holiday Specials" - seasonal content

**Schedule Groups** define *when* content plays:
- "Business Hours" - 9 AM to 5 PM, weekdays
- "Weekend" - All day Saturday and Sunday
- "Evening" - 5 PM to 10 PM

### Device Assignment

Each device can have:
1. **Schedule Group**: Controls timing (when content plays)
2. **Content Groups**: Fallback content when no schedule is active

This allows flexible configurations:
- Device A: Uses "Business Hours" schedule, falls back to "Gym Promotions"
- Device B: Uses "Business Hours" schedule, falls back to "Check-in Welcome"
- Both devices follow the same timing but show different content

### Default Display

When no content is scheduled and no fallback content groups are assigned:
1. Upload a logo (PNG with transparency recommended)
2. Choose a background: solid color, single image, or slideshow
3. Configure logo position and scale

## API Endpoints

### Content Groups
- `GET /api/content-groups` - List all groups
- `POST /api/content-groups` - Create a group
- `GET /api/content-groups/{id}` - Get group with content
- `PATCH /api/content-groups/{id}` - Update group
- `DELETE /api/content-groups/{id}` - Delete group
- `POST /api/content-groups/{id}/content` - Upload content

### Schedule Groups
- `GET /api/schedule-groups` - List all schedule groups
- `POST /api/schedule-groups` - Create schedule group
- `GET /api/schedule-groups/{id}` - Get with schedules
- `PATCH /api/schedule-groups/{id}` - Update
- `DELETE /api/schedule-groups/{id}` - Delete

### Schedules
- `POST /api/schedules` - Create schedule
- `PATCH /api/schedules/{id}` - Update schedule
- `DELETE /api/schedules/{id}` - Delete schedule

### Devices
- `GET /api/devices` - List all devices
- `POST /api/devices` - Create device (returns device key)
- `GET /api/devices/{id}` - Get device details
- `PATCH /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device

### Player API
- `GET /api/player/{device_key}/config` - Get full device config
- `GET /api/player/{device_key}/playlist` - Get current playlist

### WebSocket
- `WS /ws/{device_key}` - Real-time updates for players

## Production Deployment

### Server

1. **Use a production ASGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

2. **Build the web UI**
   ```bash
   cd web-ui
   npm run build
   ```
   Serve the `dist` folder with nginx or similar

3. **Use a proper database** (optional)
   Update `DATABASE_URL` environment variable for PostgreSQL

### Player Auto-start (Raspberry Pi)

Create a systemd service at `/etc/systemd/system/signage-player.service`:

```ini
[Unit]
Description=Digital Signage Player
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/player.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable signage-player
sudo systemctl start signage-player
```

## Troubleshooting

### Player can't connect to server
- Check firewall allows port 8000
- Verify server URL includes `http://`
- Ensure device key is correct

### Content not displaying
- Check browser console for errors
- Verify content files exist in uploads directory
- Check file permissions

### Sync issues
- Check network connectivity
- Review server logs for errors
- Verify device is marked as active

## License

MIT License - Feel free to use and modify.
