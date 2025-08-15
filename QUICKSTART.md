# Quick Start Guide - SAM.gov Opportunity Analysis System

✅ **MongoDB Atlas is Connected and Ready!**

Your MongoDB Atlas cluster is successfully configured with:
- Database: `sam_opportunities`
- Collections: `opportunities`, `capabilities`, `matches`

## Next Steps

### 1. Set Your SAM.gov API Key

Get your API key from https://sam.gov/apis and set it:

```bash
export SAM_API_KEY="your-api-key-here"
```

### 2. Fetch Opportunities from SAM.gov

This will pull opportunities from SAM.gov and store them in MongoDB Atlas:

```bash
python search_db.py $SAM_API_KEY
```

### 3. Start the Backend API Server

```bash
python app.py
```

The API will run on http://localhost:5000

### 4. Start the Frontend (in a new terminal)

```bash
cd frontend
npm install  # First time only
npm start
```

The frontend will run on http://localhost:3000

## Using the Application

1. **Dashboard** - View statistics and recent high-matching opportunities
2. **Opportunities** - Browse and filter all opportunities
3. **Capabilities** - Define your organization's capabilities with keywords
4. **High Matches** - See opportunities that best match your capabilities

## Key Features

- **Automatic Matching**: The system automatically matches opportunities to your defined capabilities
- **Filtering**: Filter by NAICS codes, agencies, set-asides, and date ranges
- **Analysis**: Click "Analyze Match" on any opportunity to see how well it matches your capabilities
- **Cloud Storage**: All data is stored in MongoDB Atlas for reliability and accessibility

## Testing the System

1. After fetching opportunities, go to http://localhost:3000
2. Navigate to "Capabilities" and create your first capability:
   - Add relevant keywords (e.g., "software", "development", "cloud")
   - Add NAICS codes you typically work with
   - Add preferred agencies
3. Go to "Opportunities" and click "Analyze Match" on any opportunity
4. Check "High Matches" to see the best matching opportunities

## Troubleshooting

If you encounter any issues:

1. **Test MongoDB Connection**:
   ```bash
   python test_mongodb_atlas.py
   ```

2. **Check Backend is Running**:
   - Should see "Running on http://127.0.0.1:5000" in terminal

3. **Frontend Issues**:
   - Clear browser cache
   - Check console for errors (F12 in browser)

## Daily Usage

To keep your opportunities up-to-date, run the search script daily:

```bash
python search_db.py $SAM_API_KEY
```

This will fetch new opportunities and add them to your database.