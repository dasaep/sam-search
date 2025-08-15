# SAM.gov Opportunity Intelligence Platform - Enhanced Version

A comprehensive, AI-powered government contracting opportunity management system with advanced features including GraphRAG, LLM chatbot, CRM workflow, and automated synchronization.

## 🚀 Key Features

### 1. **Intelligent API Throttling & Sync**
- Automated incremental synchronization every 15 minutes
- Rate-limited to 90 opportunities per run to avoid API throttling
- Tracks last synced opportunity to prevent duplicates
- Configurable sync intervals and batch sizes

### 2. **CRM Workflow System**
- 8-stage opportunity pipeline (Discovered → Reviewing → Qualified → Proposal Prep → Submitted → Awarded/Lost/Declined)
- Drag-and-drop interface for stage management
- Document attachment and tracking
- Activity logging and audit trail
- Custom fields for estimated value, win probability, priority

### 3. **GraphRAG with Neo4j**
- Knowledge graph of opportunities, agencies, NAICS codes, and capabilities
- Relationship mapping for similar opportunity discovery
- Keyword extraction and linking
- Graph-based queries for complex analysis

### 4. **AI Chatbot with Ollama**
- Natural language queries about opportunities
- Context-aware responses using local LLM
- Intent recognition and entity extraction
- Session management and conversation history
- Suggested follow-up questions

### 5. **Enhanced UI Components**
- Real-time chat interface
- Kanban-style CRM board
- Advanced filtering and search
- Statistics dashboard
- Document management interface

### 6. **Containerized Architecture**
- Docker Compose for easy deployment
- Separate containers for each service
- Volume persistence for data
- Environment-based configuration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Dashboard │ │   CRM    │ │   Chat   │ │Analytics │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                    Flask API Backend                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   Sync   │ │   CRM    │ │  Chat    │ │  Graph   │       │
│  │ Manager  │ │ Workflow │ │  Bot     │ │   RAG    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│    MongoDB     │ │    Neo4j    │ │     Ollama     │
│  (Document DB) │ │ (Graph DB)  │ │   (Local LLM)  │
└────────────────┘ └─────────────┘ └────────────────┘
```

## 📋 Prerequisites

- Docker & Docker Compose
- SAM.gov API Key
- 8GB+ RAM (for Ollama LLM)
- 20GB+ disk space

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone <repository>
cd sam-search

# Set environment variables
export SAM_API_KEY="your-sam-api-key"
```

### 2. Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Download Ollama model (first time only)
docker exec -it sam-ollama ollama pull llama2

# Check service status
docker-compose ps
```

### 3. Access the Application

- **Frontend**: http://localhost
- **API**: http://localhost:5001
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)
- **MongoDB**: mongodb://localhost:27017

## 💡 Usage Examples

### Chat Interface

Ask natural language questions:
- "Show me recent opportunities from the Department of Defense"
- "Find opportunities with high capability matches"
- "What's the status of our opportunity pipeline?"
- "Find opportunities similar to [opportunity_id]"

### CRM Workflow

1. Opportunities automatically start in "Discovered" stage
2. Drag cards between stages to update status
3. Click on cards to edit details (value, probability, assignee)
4. Track document attachments and activities

### Scheduled Sync

The scheduler runs automatically every 15 minutes. Monitor sync status:

```bash
# View scheduler logs
docker logs sam-scheduler

# Check sync history in MongoDB
docker exec -it sam-mongodb mongosh
> use sam_opportunities
> db.sync_jobs.find().sort({executed_at: -1}).limit(5)
```

## 🔧 Configuration

### Sync Settings (environment variables)

```bash
SYNC_INTERVAL_MINUTES=15  # How often to sync
MAX_OPPORTUNITIES_PER_RUN=90  # API throttle limit
DAYS_LOOKBACK=30  # Initial sync lookback period
```

### Database Connections

MongoDB Atlas (alternative to local):
```bash
MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/"
```

Neo4j:
```bash
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="password123"
```

Ollama:
```bash
OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="llama2"  # or mistral, codellama, etc.
```

## 📊 API Endpoints

### CRM Endpoints
- `GET /api/crm/opportunities` - Get opportunities by stage
- `PUT /api/crm/opportunities/:id/stage` - Update opportunity stage
- `PUT /api/crm/opportunities/:id/fields` - Update CRM fields
- `GET /api/crm/pipeline` - Get pipeline statistics
- `POST /api/crm/opportunities/:id/documents` - Add document
- `GET /api/crm/opportunities/:id/activities` - Get activity log

### Chat Endpoint
- `POST /api/chat` - Send message to chatbot
  ```json
  {
    "message": "Find recent opportunities",
    "session_id": "session_123"
  }
  ```

### Graph Endpoints
- `GET /api/graph/opportunities/:id/similar` - Find similar opportunities
- `GET /api/graph/opportunities/:id/network` - Get opportunity network
- `POST /api/graph/query` - Execute custom Cypher query

### Sync Endpoints
- `POST /api/sync/incremental` - Trigger incremental sync
- `POST /api/sync/full` - Trigger full sync
- `GET /api/sync/status` - Get sync status
- `GET /api/sync/history` - Get sync history

## 🔍 Advanced Queries

### Neo4j Graph Queries

Find opportunities with shared keywords:
```cypher
MATCH (o1:Opportunity)-[:CONTAINS_KEYWORD]->(k:Keyword)<-[:CONTAINS_KEYWORD]-(o2:Opportunity)
WHERE o1.id = $opportunity_id
RETURN o2, count(k) as shared_keywords
ORDER BY shared_keywords DESC
```

Agency opportunity network:
```cypher
MATCH (a:Agency)<-[:POSTED_BY]-(o:Opportunity)-[:CLASSIFIED_AS]->(n:NAICS)
WHERE a.name =~ '.*DEFENSE.*'
RETURN a, o, n
```

### MongoDB Aggregations

Pipeline value by stage:
```javascript
db.opportunity_tracking.aggregate([
  {$group: {
    _id: "$stage",
    total_value: {$sum: "$estimated_value"},
    count: {$sum: 1}
  }},
  {$sort: {total_value: -1}}
])
```

## 🐛 Troubleshooting

### Ollama Issues
```bash
# Check Ollama status
docker logs sam-ollama

# Manually download model
docker exec -it sam-ollama ollama pull llama2

# Test Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Hello"
}'
```

### Neo4j Connection
```bash
# Check Neo4j logs
docker logs sam-neo4j

# Test connection
docker exec -it sam-neo4j cypher-shell -u neo4j -p password123
```

### Sync Issues
```bash
# Check scheduler logs
docker logs sam-scheduler

# Manually trigger sync
curl -X POST http://localhost:5001/api/sync/incremental
```

## 🚢 Production Deployment

### Using Docker Swarm
```bash
docker swarm init
docker stack deploy -c docker-compose.yml sam-stack
```

### Using Kubernetes
```bash
kubectl apply -f k8s/
```

### Environment Variables for Production
```bash
NODE_ENV=production
FLASK_ENV=production
DEBUG=false
SECRET_KEY=<generate-secure-key>
```

## 📈 Monitoring

### Prometheus Metrics
The application exposes metrics at `/metrics`:
- Sync success/failure rates
- API response times
- Database query performance
- Chat interaction counts

### Logging
All services log to Docker volumes:
- Application logs: `/app/logs`
- Scheduler logs: `/app/logs/scheduler.log`
- Database logs: Standard Docker logs

## 🔐 Security Considerations

1. **API Keys**: Store in environment variables or secrets manager
2. **Database Credentials**: Use strong passwords, rotate regularly
3. **Network**: Use TLS/SSL in production
4. **Access Control**: Implement authentication for production
5. **Data Privacy**: Ensure compliance with government data requirements

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- SAM.gov API for opportunity data
- Neo4j for graph database capabilities
- Ollama for local LLM inference
- MongoDB for document storage
- React for frontend framework