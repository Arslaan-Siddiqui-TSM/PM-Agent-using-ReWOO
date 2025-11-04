# Docker Setup for Qdrant

This document explains how to set up and run Qdrant vector database using Docker for the PM Agent RAG system.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)

## Quick Start

### 1. Start Qdrant

From the project root directory, run:

```bash
docker-compose up -d qdrant
```

This will:
- Pull the latest Qdrant image (if not already present)
- Start Qdrant on ports 6333 (REST API) and 6334 (gRPC)
- Create a volume at `./qdrant_storage` for data persistence

### 2. Verify Qdrant is Running

Check the container status:

```bash
docker ps
```

You should see `pm-agent-qdrant` in the list of running containers.

Access the Qdrant dashboard:
```
http://localhost:6333/dashboard
```

### 3. Check Logs

View Qdrant logs:

```bash
docker-compose logs qdrant
```

Follow logs in real-time:

```bash
docker-compose logs -f qdrant
```

## Common Commands

### Stop Qdrant

```bash
docker-compose stop qdrant
```

### Restart Qdrant

```bash
docker-compose restart qdrant
```

### Stop and Remove Qdrant (keeps data)

```bash
docker-compose down
```

### Stop and Remove Qdrant (DELETE all data)

```bash
docker-compose down -v
```

⚠️ **Warning:** The `-v` flag will delete all vector embeddings!

## Data Persistence

Qdrant data is stored in:
- **Local directory:** `./qdrant_storage/`
- **Docker volume:** Mounted to `/qdrant/storage` inside the container

This ensures your embeddings persist across container restarts.

## Troubleshooting

### Port Already in Use

If port 6333 or 6334 is already in use:

1. Check what's using the port:
   ```bash
   # Windows PowerShell
   netstat -ano | findstr :6333
   ```

2. Edit `docker-compose.yml` to use different ports:
   ```yaml
   ports:
     - "6335:6333"  # Change external port
     - "6336:6334"
   ```

3. Update `.env` file:
   ```
   QDRANT_URL=http://localhost:6335
   ```

### Container Won't Start

Check Docker Desktop is running:
- Open Docker Desktop application
- Ensure Docker engine is started

Check for errors in logs:
```bash
docker-compose logs qdrant
```

### Connection Refused

Ensure Qdrant is running:
```bash
docker ps
```

Test connection:
```bash
curl http://localhost:6333/healthz
```

Should return: `{"title":"healthz","version":"1.x.x"}`

### Reset Everything

Complete reset (removes all data):

```bash
docker-compose down -v
rm -rf qdrant_storage/
docker-compose up -d qdrant
```

## Qdrant Dashboard

Access the web UI at:
```
http://localhost:6333/dashboard
```

Features:
- View collections
- Browse vectors
- Check cluster health
- Monitor storage usage

## Collection Management

Collections are automatically created by the application with naming pattern:
- Session collections: `pm_agent_<session_id>`
- Global cache: `pm_agent_cache`

View collections via API:
```bash
curl http://localhost:6333/collections
```

## Performance Tuning

For production deployments, consider:

1. **Memory limits** (in `docker-compose.yml`):
   ```yaml
   mem_limit: 4g
   mem_reservation: 2g
   ```

2. **CPU limits**:
   ```yaml
   cpus: '2.0'
   ```

3. **Persistent storage** on SSD for better performance

4. **Backup strategy** for `qdrant_storage/` directory

## Security

For production:

1. Enable authentication in `docker-compose.yml`:
   ```yaml
   environment:
     - QDRANT__SERVICE__API_KEY=your-secret-key
   ```

2. Update application config:
   ```python
   QDRANT_API_KEY=your-secret-key
   ```

3. Use HTTPS proxy (nginx/traefik) instead of direct access

## Additional Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant Docker Hub](https://hub.docker.com/r/qdrant/qdrant)
- [Qdrant GitHub](https://github.com/qdrant/qdrant)

## Support

If you encounter issues:

1. Check Docker logs: `docker-compose logs qdrant`
2. Verify Docker Desktop is running
3. Ensure ports 6333/6334 are available
4. Try restarting: `docker-compose restart qdrant`


