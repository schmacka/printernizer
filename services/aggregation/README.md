# Printernizer Usage Statistics Aggregation Service

FastAPI service for receiving and storing aggregated usage statistics from Printernizer installations.

## Features

- ✅ **Privacy-First**: Only accepts aggregated data (no individual events or PII)
- ✅ **Secure**: API key authentication for all endpoints
- ✅ **Rate Limited**: Prevents abuse with configurable rate limits
- ✅ **GDPR Compliant**: Data deletion endpoint for user requests
- ✅ **Production Ready**: PostgreSQL support, Docker deployment, health checks
- ✅ **Monitored**: Comprehensive logging and statistics summary endpoint

## Privacy & Security

### What Data Is Stored

The service stores **only aggregated statistics**:

- Anonymous installation UUID (random, not traceable)
- App version, platform, deployment mode
- Country code (derived from timezone, e.g., "DE", "US")
- Printer counts by type (e.g., `{"bambu_lab": 2, "prusa_core": 1}`)
- Aggregated job/file counts
- Feature usage flags
- Event type counts

### What Data Is NOT Stored

- ❌ No personally identifiable information (PII)
- ❌ No printer serial numbers
- ❌ No IP addresses
- ❌ No printer names
- ❌ No individual events (only aggregated counts)
- ❌ No file names or content

## Quick Start

### Development (SQLite)

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env and set a secure API_KEY

# Run the service
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Production (Docker + PostgreSQL)

```bash
# Copy environment configuration
cp .env.example .env

# Edit .env and configure:
# - DATABASE_URL=postgresql://user:password@postgres:5432/printernizer_stats
# - API_KEY=<secure-random-key>

# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f aggregation-service
```

## API Endpoints

### Health Check

```bash
GET /
GET /health
```

No authentication required. Returns service status.

### Submit Statistics

```bash
POST /submit
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json
Body: AggregatedStatsModel (JSON)
```

Submit aggregated statistics from a Printernizer installation.

**Rate Limit**: 10 requests per hour per installation (configurable)

**Example Request**:

```bash
curl -X POST https://stats.printernizer.com/submit \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @aggregated_stats.json
```

### Delete Installation Data (GDPR)

```bash
DELETE /installation/{installation_id}
Headers:
  X-API-Key: your-api-key
```

Delete all data for an installation. Required for GDPR compliance.

**Example**:

```bash
curl -X DELETE https://stats.printernizer.com/installation/abc123-def456 \
  -H "X-API-Key: your-api-key"
```

### Statistics Summary (Admin)

```bash
GET /stats/summary
Headers:
  X-API-Key: your-api-key
```

Get high-level statistics about submissions (total submissions, unique installations, etc.).

## Configuration

All configuration via environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./aggregation.db` |
| `API_KEY` | API key for authentication | `change-me-in-production` |
| `RATE_LIMIT_PER_HOUR` | Max submissions per installation per hour | `10` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8080` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |

## Database Schema

### Submissions Table

Stores each aggregated statistics submission:

- `id`: Auto-increment primary key
- `installation_id`: Anonymous UUID (indexed)
- `submitted_at`: Timestamp (indexed)
- `schema_version`: Payload schema version
- `period_start`, `period_end`: Time period covered
- Installation info: `app_version`, `platform`, `deployment_mode`, `country_code`
- Printer fleet: `printer_count`, `printer_types`, `printer_type_counts`
- Usage stats: `total_jobs_*`, `total_files_*`, `uptime_hours`
- Feature usage and event counts (JSON fields)

### RateLimit Table

Tracks rate limits per installation:

- `installation_id`: UUID (unique, indexed)
- `last_submission_at`: Last submission timestamp
- `submission_count`: Count in current window
- `window_start`: Current rate limit window start

## Deployment

### Deploy to Cloud

#### AWS (ECS + RDS PostgreSQL)

```bash
# Build and push Docker image
docker build -t printernizer-aggregation .
docker tag printernizer-aggregation:latest <your-ecr-repo>:latest
docker push <your-ecr-repo>:latest

# Deploy via ECS with RDS PostgreSQL
# Set environment variables in ECS task definition
```

#### Azure (Container Apps + PostgreSQL)

```bash
# Build and push to Azure Container Registry
az acr build --registry <your-acr> --image printernizer-aggregation:latest .

# Deploy to Container Apps
az containerapp create \
  --name printernizer-aggregation \
  --resource-group <your-rg> \
  --image <your-acr>.azurecr.io/printernizer-aggregation:latest \
  --environment <your-env> \
  --ingress external --target-port 8080
```

#### Google Cloud (Cloud Run + Cloud SQL PostgreSQL)

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/<project-id>/printernizer-aggregation
gcloud run deploy printernizer-aggregation \
  --image gcr.io/<project-id>/printernizer-aggregation \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=<cloud-sql-url>,API_KEY=<secure-key>
```

### Monitoring

- **Health checks**: `/health` endpoint for load balancers
- **Logs**: Structured JSON logs via structlog
- **Metrics**: Monitor submission counts via `/stats/summary`

Recommended monitoring:
- Set up alerts for 429 (rate limit) and 500 errors
- Monitor database size and query performance
- Track unique installation count growth

## Development

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Database Migrations (Alembic)

```bash
# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head
```

## Security Checklist

- [ ] Change default `API_KEY` to a secure random value
- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Enable HTTPS (use reverse proxy like nginx or cloud load balancer)
- [ ] Restrict `ALLOWED_ORIGINS` for CORS
- [ ] Set up database backups
- [ ] Monitor for unusual submission patterns
- [ ] Implement IP-based rate limiting (if needed)
- [ ] Review logs regularly

## License

Same as Printernizer main application.

## Support

For issues or questions, see the main Printernizer repository.
