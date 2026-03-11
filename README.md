# STIM Client Matcher

A web app for matching Excel files against a Salesforce client export (~37,000 records).

## Quick start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Stack
- **Backend**: FastAPI + rapidfuzz + openpyxl + pandas
- **Frontend**: React 18 + Vite + Tailwind CSS

## Matching tiers
| Tier | Method | Fields required |
|------|--------|----------------|
| 1 | Exact org number | Organisation Number |
| 2 | Fuzzy name + city boost | Company Name, City |
| 3 | Fuzzy name only | Company Name |
