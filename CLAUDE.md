# Total Compensation

A full-stack web application that visualizes total compensation over time for employees with complex pay structures (base pay, bonuses, stock awards, inflation adjustment).

**Hosted instance**: https://total-compensation.onrender.com/
**License**: MIT

## Project Structure

```
total-compensation/
├── .devcontainer/              # Dev container configuration
│   ├── devcontainer.json       # Container image, features, mounts, hooks
│   ├── post-create.sh          # One-time setup: deps, Claude Code, Chrome
│   └── post-start.sh           # Every reconnect: Claude config symlinks
├── .github/workflows/
│   └── docker-publish.yml      # CI: build & push Docker image to GHCR
├── .vscode/
│   ├── launch.json             # Debug configs (Flask backend, Edge frontend)
│   └── settings.json           # Editor formatting rules
├── backend/
│   ├── app.py                  # Flask application (API endpoints, static serving)
│   ├── cpi.py                  # CPI inflation calculations via BLS API
│   ├── stocks.py               # Stock price tracking via yfinance
│   ├── requirements.txt        # Python dependencies (pinned versions)
│   ├── .env                    # Environment config (STATIC_ROOT, BLS_API_KEY)
│   ├── pytest.ini              # Test configuration
│   ├── test_app.py             # Unit/integration tests
│   ├── test_e2e.py             # End-to-end API tests
│   └── test_selenium_e2e.py    # Selenium browser tests
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main React component
│   │   ├── Form.tsx            # Compensation input form
│   │   ├── Plot.tsx            # Plotly chart display
│   │   ├── RequestPayload.ts   # TypeScript interface for form data
│   │   └── ResponsePayload.ts  # TypeScript interface for API response
│   ├── public/                 # Static HTML, manifest
│   ├── build/                  # Production build output (generated)
│   ├── package.json            # Node dependencies
│   └── tsconfig.json           # TypeScript config (strict mode)
├── Dockerfile                  # Multi-stage: Python backend + Node frontend
├── docker-compose.yml          # Single service composition
└── README.md                   # Project documentation
```

## Tech Stack

- **Frontend**: React 19, TypeScript 5, Plotly.js, Create React App
- **Backend**: Flask, pandas, yfinance (stock prices), BLS API (CPI inflation)
- **Testing**: pytest, Selenium (Chrome)
- **Production**: waitress WSGI server, multi-stage Docker build
- **CI/CD**: GitHub Actions → GitHub Container Registry, hosted on Render

## Development

### Running locally (dev container)

Dependencies are installed automatically by `post-create.sh`. To run:

- **Backend**: `cd backend && flask run --port 8000`
- **Frontend**: `cd frontend && npm start` (port 3000, hot-reload)
- For frontend dev, temporarily change the API URL in `frontend/src/Plot.tsx` to `localhost:8000`

### Running via Docker

```bash
docker-compose up
```

### Running tests

```bash
cd backend && pytest                              # Unit + integration tests
cd backend && pytest test_e2e.py                  # End-to-end API tests
cd backend && pytest test_selenium_e2e.py         # Selenium browser tests
```

## API

- `POST /api/v1.0/plot/` - Accepts compensation data, returns chart series
- `GET /` - Serves the React frontend

## Key Decisions

- **yfinance for stock data**: Yahoo Finance API doesn't support CORS, so stock lookups must go through the backend
- **BLS API for inflation**: Custom CPI inflater in `cpi.py` (lightweight alternative to the `cpi` PyPI package)
- **Cookie-based state persistence**: Form data is saved in browser cookies so users don't lose their input
- **Multi-stage Docker build**: Keeps the production image small (Python alpine + pre-built React assets)

## Agent Instructions

### Dependencies

- **Python packages**: Add to `backend/requirements.txt` with pinned versions AND to `.devcontainer/post-create.sh` (the pip install line already reads from requirements.txt, so just update the file)
- **Node packages**: Add via `npm install` in `frontend/` - post-create.sh already runs `npm install` from package.json
- **System packages**: Add `sudo apt-get install -y <package>` to `.devcontainer/post-create.sh`
- **Always update `post-create.sh`** when adding any new system-level dependency so it survives container teardown

### Code conventions

- Backend Python code follows standard Flask patterns - routes in `app.py`, utilities in separate modules
- Frontend uses TypeScript strict mode - maintain type safety, don't use `any`
- Keep interfaces in their own files (`RequestPayload.ts`, `ResponsePayload.ts`)
- Tests go alongside the code they test in the `backend/` directory

### Testing

- Write pytest tests for new backend functionality in `test_app.py`
- Run the full test suite before considering work complete
- Selenium tests require Chrome (installed by post-create.sh)

### Documentation

- Update this CLAUDE.md when making structural changes or adding new conventions
- Update README.md for user-facing feature changes
