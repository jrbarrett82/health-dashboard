# Health Info

Automated health data visualization and AI analysis system. Fetches nutrition and weight data from Gmail (Lose It! CSV exports), stores it in InfluxDB, visualizes it in Grafana, and provides AI-powered insights using Ollama.

Inspired by [fitbit-grafana](https://github.com/arpanghosh8453/fitbit-grafana).

## Features

- 📧 **Automatic Gmail Integration** - Fetches CSV attachments from "Lose It! Weekly Summary" emails
- 📊 **InfluxDB Storage** - Time-series database optimized for health metrics
- 📈 **Grafana Dashboards** - Beautiful visualizations of weight, calories, macronutrients, and more
- 🤖 **AI Chat Interface** - Ask questions about your health data using local Ollama
- 🔄 **Easy Sync** - One command to update all your data

## Prerequisites

- Python 3.8+
- Docker & Docker Compose
- Gmail account with "Lose It! Weekly Summary" label
- [Ollama](https://ollama.ai) installed locally (optional, for AI chat)

## Quick Start

### 1. Clone and Setup

```bash
cd health-info
cp .env.template .env
```

Edit `.env` and configure your settings (especially Ollama host if different).

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Gmail API Access

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to this directory
6. Make sure you have a Gmail label called "Lose It! Weekly Summary"

### 4. Start InfluxDB & Grafana

```bash
docker compose up -d
```

This starts:
- InfluxDB on `http://localhost:8086`
- Grafana on `http://localhost:3000` (admin/admin)

### 5. Sync Your Data

Run the sync script to fetch emails and import data:

```bash
python sync_data.py
```

On first run, you'll authenticate with Gmail via your browser.

### 6. View Your Dashboard

Open Grafana at `http://localhost:3000`:
- Username: `admin`
- Password: `admin`

The "Health & Nutrition Dashboard" should be automatically available.

### 7. Chat with Your Data (Optional)

If you have Ollama running:

```bash
python health_chat.py
```

Ask questions like:
- "What's my average calorie intake?"
- "Am I losing weight?"
- "How much protein am I getting?"

## Project Structure

```
health-info/
├── src/
│   ├── database.py        # InfluxDB interface
│   ├── gmail_fetcher.py   # Gmail API integration
│   └── csv_parser.py      # Lose It! CSV parser
├── grafana/
│   ├── dashboards/        # Grafana dashboard configs
│   └── datasources/       # InfluxDB datasource config
├── sync_data.py           # Main data sync script
├── health_chat.py         # AI chat interface
├── docker-compose.yml     # Docker services
├── requirements.txt       # Python dependencies
└── .env                   # Configuration (create from .env.template)
```

## Configuration

Edit `.env` to customize:

- `GMAIL_LABEL_NAME` - Gmail label to monitor (default: "Lose It! Weekly Summary")
- `OLLAMA_HOST` - Ollama API endpoint
- `OLLAMA_MODEL` - Model to use for chat (default: qwen2.5:7b-instruct)
- `SYNC_LOOKBACK_DAYS` - How far back to fetch emails (default: 90)

## Usage

### Regular Data Sync

Run sync manually or set up a cron job:

```bash
python sync_data.py
```

### Querying Data

Use the chat interface:

```bash
python health_chat.py
```

Or query InfluxDB directly:

```bash
docker exec -it health-influxdb influx -database HealthStats
```

### Customizing Dashboards

Edit `grafana/dashboards/health-dashboard.json` or create new dashboards in the Grafana UI.

## Data Schema

InfluxDB measurement: `daily_nutrition`

Fields:
- `calories` - Daily total calories
- `protein_g` - Protein in grams
- `carbs_g` - Carbohydrates in grams
- `fat_g` - Fat in grams
- `sodium_mg` - Sodium in milligrams
- `sugar_g` - Sugar in grams
- `fiber_g` - Fiber in grams
- `weight_lbs` - Body weight in pounds (optional)

## Troubleshooting

### Can't connect to InfluxDB

Make sure Docker is running:
```bash
docker compose up -d
```

### Gmail authentication fails

Delete `token.json` and run sync again to re-authenticate.

### No data in Grafana

Check that sync completed successfully and data is in InfluxDB:
```bash
python sync_data.py
```

### Ollama connection error

Update `OLLAMA_HOST` in `.env` to match your Ollama installation.

## License

MIT
