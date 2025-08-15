# SAM.gov Opportunity Analysis System V2
[![sam-search-build](https://github.com/MindPetal/sam-search/actions/workflows/sam-search-build.yaml/badge.svg)](https://github.com/MindPetal/sam-search/actions/workflows/sam-search-build.yaml) [![sam-search-run](https://github.com/MindPetal/sam-search/actions/workflows/sam-search-run.yaml/badge.svg)](https://github.com/MindPetal/sam-search/actions/workflows/sam-search-run.yaml)

A comprehensive system for searching, storing, and analyzing government contracting opportunities from SAM.gov with capability matching and frontend interface.

## Features

- **MongoDB Storage**: Stores all opportunities locally for faster access and historical analysis
- **Capability Management**: Define your organization's capabilities with keywords, NAICS codes, and preferred agencies
- **Intelligent Matching**: Automatically matches opportunities to your capabilities with percentage scores
- **Web Interface**: React-based frontend for easy opportunity browsing and analysis
- **RESTful API**: Flask backend providing data access and analysis endpoints

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "SAM.gov Opportunity Analysis System"
        subgraph "Presentation Layer"
            Dashboard[Dashboard]
            OppList[Opportunity List]
            CapManager[Capability Manager]
            HighMatches[High Matches]
        end
        
        subgraph "Application Layer - Flask API"
            OppService[Opportunity Service]
            CapService[Capability Service]
            MatchEngine[Matching Engine]
            StatService[Statistics Service]
        end
        
        subgraph "Data Layer"
            subgraph "MongoDB Atlas"
                OppDB[(Opportunities)]
                CapDB[(Capabilities)]
                MatchDB[(Matches)]
            end
            
            subgraph "External"
                SAM[SAM.gov API<br/>Rate-Limited ETL Pipeline]
            end
        end
        
        Dashboard --> OppService
        OppList --> OppService
        CapManager --> CapService
        HighMatches --> MatchEngine
        
        OppService --> OppDB
        CapService --> CapDB
        MatchEngine --> MatchDB
        StatService --> OppDB
        StatService --> CapDB
        StatService --> MatchDB
        
        SAM --> OppDB
    end
    
    style Dashboard fill:#e1f5fe
    style OppList fill:#e1f5fe
    style CapManager fill:#e1f5fe
    style HighMatches fill:#e1f5fe
    style OppService fill:#fff3e0
    style CapService fill:#fff3e0
    style MatchEngine fill:#fff3e0
    style StatService fill:#fff3e0
    style OppDB fill:#f3e5f5
    style CapDB fill:#f3e5f5
    style MatchDB fill:#f3e5f5
    style SAM fill:#e8f5e9
```

### Component Interaction Diagram

```mermaid
sequenceDiagram
    participant UI as React Frontend
    participant API as Flask API Gateway
    participant Auth as Auth Middleware
    participant Route as Route Handler
    participant OppH as Opportunity Handler
    participant CapH as Capability Handler
    participant MatchE as Match Engine
    participant StatH as Statistics Handler
    participant MongoDB as MongoDB Atlas
    participant SAM as SAM.gov API

    UI->>API: HTTP/REST Request
    API->>Auth: Authenticate
    Auth->>Route: Route Request
    
    alt Opportunity Request
        Route->>OppH: Handle Request
        OppH->>MongoDB: Query Opportunities
        MongoDB-->>OppH: Return Data
        OppH-->>UI: JSON Response
    else Capability Request
        Route->>CapH: Handle Request
        CapH->>MongoDB: Query Capabilities
        MongoDB-->>CapH: Return Data
        CapH-->>UI: JSON Response
    else Match Request
        Route->>MatchE: Process Matching
        MatchE->>MongoDB: Query & Calculate
        MongoDB-->>MatchE: Return Matches
        MatchE-->>UI: Match Results
    else Statistics Request
        Route->>StatH: Generate Stats
        StatH->>MongoDB: Aggregate Data
        MongoDB-->>StatH: Return Stats
        StatH-->>UI: Statistics
    end
    
    Note over SAM,MongoDB: Sync Process (Scheduled)
    SAM->>MongoDB: Sync Opportunities
    MongoDB-->>SAM: Confirm Updates
```

## Functional Flow Diagrams

### 1. Opportunity Sync Flow

```mermaid
flowchart TD
    Start([START])
    CheckSync[Check Last Sync State]
    DateRange[Determine Date Range]
    ForEachNAICS[For Each NAICS Code]
    CallAPI[Call SAM.gov API<br/>Max 90 records]
    RateLimit[Rate Limiting<br/>2 sec delay]
    Process[Process & Transform<br/>Opportunity]
    Upsert[Upsert to MongoDB<br/>Deduplicate]
    MoreNAICS{More NAICS Codes?}
    UpdateSync[Update Sync State<br/>timestamp, count]
    End([END])
    
    Start --> CheckSync
    CheckSync --> DateRange
    DateRange --> ForEachNAICS
    ForEachNAICS --> CallAPI
    CallAPI --> RateLimit
    RateLimit --> Process
    Process --> Upsert
    Upsert --> MoreNAICS
    MoreNAICS -->|Yes| ForEachNAICS
    MoreNAICS -->|No| UpdateSync
    UpdateSync --> End
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style CallAPI fill:#87CEEB
    style Upsert fill:#DDA0DD
```

### 2. Capability Matching Flow

```mermaid
flowchart TD
    UserTrigger([User Triggers Analysis])
    SelectOpp[Select Opportunity]
    RetrieveCap[Retrieve All Active<br/>Capabilities from DB]
    ForEachCap[For Each Capability]
    ExtractFeatures[Extract Opportunity Features:<br/>• Title<br/>• Description<br/>• NAICS Code<br/>• Agency<br/>• Set-Aside Type]
    
    subgraph CalcScore[Calculate Match Score]
        Keyword[Keyword Match 40%<br/>• Search in title/desc<br/>• Count matched terms]
        NAICS[NAICS Match 30%<br/>• Exact code match]
        Agency[Agency Match 20%<br/>• Preferred agency]
        SetAside[Set-Aside Match 10%<br/>• Preferred type]
    end
    
    StoreResult[Store Match Result in DB<br/>opportunity_id, capability_id,<br/>score, details]
    MoreCap{More Capabilities?}
    SortMatches[Sort Matches by Score<br/>Descending]
    ReturnMatches[Return Top Matches to User]
    
    UserTrigger --> SelectOpp
    SelectOpp --> RetrieveCap
    RetrieveCap --> ForEachCap
    ForEachCap --> ExtractFeatures
    ExtractFeatures --> CalcScore
    CalcScore --> StoreResult
    StoreResult --> MoreCap
    MoreCap -->|Yes| ForEachCap
    MoreCap -->|No| SortMatches
    SortMatches --> ReturnMatches
    
    style UserTrigger fill:#90EE90
    style ReturnMatches fill:#FFB6C1
    style CalcScore fill:#FFF8DC
```

### 3. User Interaction Flow

```mermaid
flowchart TD
    UserAccess[User Access Frontend]
    
    subgraph Dashboard[Dashboard View]
        Stats[Statistics]
        RecentMatches[Recent High Matches]
    end
    
    BrowseOpp[Browse<br/>Opportunities]
    ManageCap[Manage<br/>Capabilities]
    ViewMatch[View<br/>High Match]
    SearchFilter[Search<br/>Filter]
    
    ViewDetails[View Details<br/>• Full Info<br/>• Documents<br/>• Matches]
    AddEditCap[Add/Edit Cap.<br/>• Keywords<br/>• NAICS<br/>• Agencies]
    AdjustThresh[Adjust Thresh.<br/>• >70% Match<br/>• >80% Match<br/>• >90% Match]
    ApplyFilters[Apply Filters<br/>• NAICS<br/>• Agency<br/>• Date Range]
    
    Analyze[Analyze Opportunity<br/>• Run Match<br/>• View Score]
    Export[Export Results<br/>• CSV<br/>• PDF]
    
    UserAccess --> Dashboard
    Dashboard --> BrowseOpp
    Dashboard --> ManageCap
    Dashboard --> ViewMatch
    Dashboard --> SearchFilter
    
    BrowseOpp --> ViewDetails
    ManageCap --> AddEditCap
    ViewMatch --> AdjustThresh
    SearchFilter --> ApplyFilters
    
    ViewDetails --> Analyze
    ApplyFilters --> Export
    
    style UserAccess fill:#90EE90
    style Dashboard fill:#E6E6FA
    style Analyze fill:#FFE4B5
    style Export fill:#FFE4B5
```

### 4. Data Processing Pipeline

```mermaid
flowchart TD
    SAMApi[SAM.gov API]
    
    DataExtract[Data Extraction<br/>• API Authentication<br/>• Request Formation<br/>• Response Handling]
    
    DataTransform[Data Transformation<br/>• Field Mapping<br/>• Date Parsing<br/>• Agency Formatting<br/>• NAICS Enhancement]
    
    DataValidate[Data Validation<br/>• Required Fields<br/>• Format Checking<br/>• Duplicate Detection]
    
    MongoStore[MongoDB Storage<br/>• Upsert Operation<br/>• Index Creation<br/>• Relationship Links]
    
    PostProcess[Post-Processing<br/>• Statistics Update<br/>• Trigger Analysis<br/>• Alert Generation]
    
    SAMApi --> DataExtract
    DataExtract --> DataTransform
    DataTransform --> DataValidate
    DataValidate --> MongoStore
    MongoStore --> PostProcess
    
    style SAMApi fill:#90EE90
    style DataExtract fill:#87CEEB
    style DataTransform fill:#FFE4B5
    style DataValidate fill:#F0E68C
    style MongoStore fill:#DDA0DD
    style PostProcess fill:#FFB6C1
```

## Prerequisites

- Python 3.8+
- MongoDB Atlas account (configured - see MongoDB Atlas Setup below)
- Node.js 14+ and npm
- SAM.gov API Key (get from https://sam.gov/apis)

## Deployment Architecture

### Production Deployment

```mermaid
graph TB
    Internet[Internet]
    
    LB[Load Balancer<br/>AWS ALB/Nginx]
    
    subgraph WebNodes[Web Server Nodes]
        subgraph Node1[Web Server Node 1]
            React1[React Build<br/>Static Files]
            Flask1[Flask API<br/>Gunicorn]
        end
        
        subgraph Node2[Web Server Node 2]
            React2[React Build<br/>Static Files]
            Flask2[Flask API<br/>Gunicorn]
        end
    end
    
    Redis[Redis Cache]
    
    MongoDB[MongoDB Atlas Cluster<br/>• Replica Set<br/>• Auto-scaling<br/>• Backups]
    
    SAMApi[SAM.gov API<br/>External<br/>• Rate Limited<br/>• Scheduled Sync]
    
    Workers[Background Workers<br/>• Scheduler<br/>• Sync Jobs<br/>• Analysis]
    
    Internet --> LB
    LB --> Node1
    LB --> Node2
    Node1 --> Redis
    Node2 --> Redis
    Redis --> MongoDB
    Redis --> Workers
    Workers --> MongoDB
    Workers --> SAMApi
    
    style Internet fill:#90EE90
    style LB fill:#87CEEB
    style Redis fill:#FFE4B5
    style MongoDB fill:#DDA0DD
    style SAMApi fill:#F0E68C
    style Workers fill:#FFB6C1
```

### Container Architecture (Docker)

```mermaid
graph TB
    subgraph DockerHost[Docker Host]
        subgraph DockerNetwork[Docker Network - sam-network bridge]
            Nginx[Nginx Container<br/>Port: 80]
            Flask[Flask API<br/>Port: 5001]
            MongoDB[MongoDB<br/>Port: 27017]
            Redis[Redis<br/>Port: 6379]
            Worker[Worker Container]
        end
        
        subgraph Volumes[Volumes]
            Vol1[./frontend/build → /usr/share/nginx/html]
            Vol2[./data/mongodb → /data/db]
            Vol3[./logs → /app/logs]
        end
    end
    
    Nginx -.-> Flask
    Flask -.-> MongoDB
    Flask -.-> Redis
    Worker -.-> MongoDB
    Worker -.-> Redis
    
    style DockerHost fill:#E6E6FA
    style DockerNetwork fill:#F0F8FF
    style Nginx fill:#87CEEB
    style Flask fill:#FFE4B5
    style MongoDB fill:#DDA0DD
    style Redis fill:#F0E68C
    style Worker fill:#FFB6C1
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. MongoDB Atlas Setup

The system is pre-configured to use MongoDB Atlas. The connection details are already set in `config_db.py`:

```python
# Connection is already configured in the code
# Database: sam_opportunities
# Collections: opportunities, capabilities, matches
```

**Important Security Note:** 
- Make sure your IP address is whitelisted in MongoDB Atlas Network Access settings
- Go to your MongoDB Atlas dashboard → Network Access → Add IP Address
- You can add your current IP or allow access from anywhere (0.0.0.0/0) for development

To test the connection:
```bash
python test_mongodb_atlas.py
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Security Architecture

```mermaid
graph TB
    subgraph SecurityLayers[Security Layers]
        subgraph L1[Layer 1: Network Security]
            HTTPS[HTTPS/TLS Encryption - Let's Encrypt]
            Firewall[Firewall Rules - Port 443, 80 → 443 redirect]
            DDoS[DDoS Protection - Cloudflare/AWS Shield]
            IPWhitelist[IP Whitelisting for Admin Access]
        end
        
        subgraph L2[Layer 2: Application Security]
            JWT[JWT Token Authentication]
            RateLimit[API Rate Limiting - Redis-based]
            CORS[CORS Configuration]
            InputVal[Input Validation & Sanitization]
            SQLPrev[SQL Injection Prevention - Parameterized Queries]
        end
        
        subgraph L3[Layer 3: Data Security]
            EncRest[MongoDB Atlas Encryption at Rest]
            TLS[TLS/SSL for Data in Transit]
            KeyRotate[API Key Rotation - 90-day cycle]
            EnvVars[Environment Variables for Secrets]
            AuditLog[Audit Logging for Data Access]
        end
        
        subgraph L4[Layer 4: Infrastructure Security]
            Container[Container Isolation - Docker]
            LeastPriv[Least Privilege Access]
            SecUpdates[Regular Security Updates]
            Backup[Backup & Disaster Recovery]
            Monitor[Monitoring & Alerting - Prometheus/Grafana]
        end
    end
    
    style L1 fill:#E8F5E9
    style L2 fill:#E3F2FD
    style L3 fill:#FFF3E0
    style L4 fill:#FCE4EC
```

### Authentication & Authorization Flow

```mermaid
sequenceDiagram
    participant Client
    participant LoginReq as Login Request
    participant VerifyCreds as Verify Credentials
    participant IssueJWT as Issue JWT
    participant VerifyJWT as Verify JWT
    participant Resource as Access Resource
    
    Client->>LoginReq: Authentication Request
    LoginReq->>VerifyCreds: Validate Credentials
    VerifyCreds->>IssueJWT: Generate Token
    IssueJWT-->>Client: Return JWT Token
    
    Client->>VerifyJWT: Request with JWT
    VerifyJWT->>Resource: Grant Access
    Resource-->>Client: Return Protected Data
```

## Configuration

1. The existing `config.yaml` file contains NAICS codes and agency mappings
2. Set your SAM.gov API key as an environment variable:
   ```bash
   export SAM_API_KEY="your-api-key-here"
   ```

## Usage

### 1. Verify MongoDB Atlas Connection

Test that you can connect to MongoDB Atlas:
```bash
python test_mongodb_atlas.py
```

### 2. Fetch and Store Opportunities

Run the search script to fetch opportunities from SAM.gov and store in MongoDB Atlas:

```bash
python search_db.py $SAM_API_KEY
```

The script will automatically connect to your MongoDB Atlas cluster.

### 3. Start the Backend API

```bash
python app.py
```

The API will run on http://localhost:5001

### 4. Start the Frontend

In a new terminal:
```bash
cd frontend
npm start
```

The frontend will run on http://localhost:3000

## API Endpoints

### Opportunities
- `GET /api/opportunities` - List opportunities with filters
- `GET /api/opportunities/:id` - Get single opportunity with matches
- `POST /api/opportunities/:id/analyze` - Analyze opportunity against capabilities

### Capabilities
- `GET /api/capabilities` - List all capabilities
- `POST /api/capabilities` - Create new capability
- `PUT /api/capabilities/:id` - Update capability

### Matches
- `GET /api/matches/high` - Get high-scoring matches

### Statistics
- `GET /api/statistics` - Get system statistics

## Frontend Features

### Dashboard
- Overview of total opportunities, capabilities, and matches
- Recent high-scoring matches
- Quick statistics

### Opportunities Page
- Browse all opportunities
- Filter by NAICS, agency, set-aside, and date range
- Quick analysis button for each opportunity
- Direct links to SAM.gov

### Capability Manager
- Create and manage organizational capabilities
- Define keywords, NAICS codes, and preferred agencies
- Activate/deactivate capabilities

### High Matches
- View opportunities with highest capability match scores
- Adjustable threshold filtering
- Detailed match information

## Capability Matching Algorithm

The system scores opportunities against capabilities based on:

1. **Keyword Matching (40%)**: Keywords found in opportunity title/description
2. **NAICS Code Match (30%)**: Exact NAICS code matches
3. **Agency Preference (20%)**: Preferred agency matches
4. **Set-Aside Match (10%)**: Preferred set-aside type matches

## Scheduling Automated Searches

To automatically fetch new opportunities daily, add to crontab:

```bash
# Run daily at 6 AM
0 6 * * * /usr/bin/python3 /path/to/search_db.py $SAM_API_KEY
```

Or use the existing GitHub Actions workflow by modifying `.github/workflows/` files.

## Database Schema

### Opportunities Collection
```javascript
{
  _id: ObjectId,
  title: String,
  agency: String,
  posted_date: String,
  due_date: String,
  type: String,
  set_aside: String,
  naics: String,
  url: String,
  posted_date_parsed: Date,
  due_date_parsed: Date,
  raw_data: Object,
  created_at: Date,
  last_updated: Date
}
```

### Capabilities Collection
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  keywords: [String],
  naics_codes: [String],
  preferred_agencies: [String],
  preferred_set_asides: [String],
  active: Boolean,
  created_at: Date,
  updated_at: Date
}
```

### Matches Collection
```javascript
{
  _id: ObjectId,
  opportunity_id: String,
  capability_id: String,
  match_percentage: Number,
  match_details: Object,
  created_at: Date
}
```

## Legacy MS Teams Integration

The original version posted opportunities to MS Teams. This functionality is preserved in `search.py`:

```bash
python3 search.py my-sam-api-key my-ms-webhook-url
```

For MS Teams webhook setup, see: [Create incoming webhooks with Workflows for Microsoft Teams](https://support.microsoft.com/en-us/office/create-incoming-webhooks-with-workflows-for-microsoft-teams-8ae491c7-0394-4861-ba59-055e33f75498)

## Troubleshooting

### MongoDB Atlas Connection Issues
- Ensure your IP is whitelisted in MongoDB Atlas Network Access
- Verify credentials in config_db.py are correct
- Run `python test_mongodb_atlas.py` to diagnose connection issues
- Check that your cluster is active in MongoDB Atlas dashboard

### Frontend Not Loading
- Check that backend is running on port 5001
- Verify proxy setting in frontend/package.json
- Clear browser cache

### No Opportunities Found
- Verify SAM.gov API key is valid
- Check date ranges in config.yaml
- Ensure NAICS codes are current

## Development

### Running Tests
```bash
python test_search.py
```

### Building for Production
```bash
cd frontend
npm run build
```

The built files will be in `frontend/build/` and served by Flask in production.

## Enhanced Version Available

For advanced features including AI chatbot, CRM workflow, and GraphRAG, see `README_ENHANCED.md`.

## License

See LICENSE file in the repository.

## Support

For issues or questions, please create an issue in the GitHub repository.
