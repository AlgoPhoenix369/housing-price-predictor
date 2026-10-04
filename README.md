# Housing Price Predictor

An AI-powered web application that predicts house prices in Washington State. A LightGBM regression model, trained earlier on a cleaned housing dataset, is served through a FastAPI backend. Users enter property details in a web form, receive a predicted price with a range, and can review their prediction history.

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [The Model](#the-model)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Using the App](#using-the-app)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Design Decisions](#design-decisions)
- [Troubleshooting](#troubleshooting)
- [Limitations & Future Enhancements](#limitations--future-enhancements)
- [Git Workflow](#git-workflow)

---

## Features

- **Price prediction**: enter living area, bedrooms, bathrooms, lot size, floors, house age and ZIP code to get a predicted price.
- **Price range**: every prediction comes with a range of the predicted price plus or minus $20,000.
- **ZIP code validation**: ZIP codes the model was not trained on are rejected with a clear message, instead of returning a misleading price.
- **Prediction history**: every prediction is saved and shown in a table with Show more and Show less controls.
- **Trend summary**: the history shows the number of predictions, the average, the highest and the lowest predicted price.
- **Private per-visitor history**: each browser gets an anonymous ID, so visitors only see their own predictions.
- **Interactive API documentation**: Swagger UI is available at `/docs` while the app is running.

---

## How It Works

```
Browser (HTML, CSS, JavaScript)
        |
        |  POST /api/predict   (X-Client-Id header)
        v
FastAPI backend
   1. Validates the input
   2. Checks the ZIP code was seen during training
   3. Rebuilds the training pipeline for the new input
   4. Predicts with the LightGBM model
   5. Saves the prediction to SQLite
        |
        v
Predicted price and range returned to the browser
```

The web page is served by the same FastAPI application, so the whole project runs as a single service from one command.

---

## The Model

The model was trained earlier. This repository contains the trained files and the application built around them.

### Training pipeline

1. **Dataset**: a cleaned housing dataset for Washington State.
2. **Features**: `sqft_living`, `no_of_bedrooms`, `no_of_bathrooms`, `sqft_lot`, `no_of_floors`, `house_age` and `zipcode`.
3. **Target**: `price`, transformed with `log1p` to reduce skew in house prices.
4. **ZIP code encoding**: `OneHotEncoder(handle_unknown='ignore')` turns the ZIP code into indicator columns.
5. **Polynomial features**: `PolynomialFeatures(degree=2, include_bias=False)` adds squared terms and interactions between the features.
6. **Split**: 80 percent training and 20 percent testing, with `random_state=42`.
7. **Model**: `LGBMRegressor` with `n_estimators=1000`, `learning_rate=0.05`, `max_depth=6`, `subsample=0.8`, `colsample_bytree=0.8` and `random_state=42`.
8. **Saved artifacts**: the model, the encoder and the polynomial transformer are saved with `joblib`.

An R2 score of 0.80 was reported for the model.

### What each saved file does

| File | Purpose |
|------|---------|
| `models/model.pkl` | The trained LightGBM regressor. It takes the transformed feature matrix and returns the predicted log price. |
| `models/encoder.pkl` | The fitted one-hot encoder for ZIP codes. It converts a ZIP code into indicator columns and also holds the list of ZIP codes seen in training. |
| `models/poly.pkl` | The fitted polynomial transformer. It expands the numeric and ZIP columns into squared terms and interactions, exactly as during training. |

### Prediction flow

1. The six numeric inputs are placed in the same column order as in training.
2. The ZIP code is converted to the type used in training and one-hot encoded.
3. The numeric and encoded columns are combined and passed through the polynomial transformer.
4. The LightGBM model predicts the log price.
5. The log price is converted back to dollars with `expm1` and rounded to cents.
6. The price range is the predicted price plus or minus $20,000.

---

## Tech Stack

| Area | Technology |
|------|------------|
| Machine learning | LightGBM, scikit-learn, pandas, NumPy, joblib |
| Backend | FastAPI, Uvicorn, Pydantic |
| Database | SQLite through SQLAlchemy 2 |
| Frontend | HTML, CSS and vanilla JavaScript, served by FastAPI |
| Language | Python 3.10 or newer (built and tested on 3.13) |

---

## Project Structure

```
housing-price-predictor/
|-- app/
|   |-- static/
|   |   |-- index.html      Prediction form and history table
|   |   |-- script.js       Form handling, API calls and history rendering
|   |   `-- style.css       Page styles
|   |-- __init__.py
|   |-- client_id.py        Reads and validates the anonymous X-Client-Id header
|   |-- config.py           Model paths, database URL, ZIP code range, range margin
|   |-- database.py         SQLAlchemy engine, session and base class
|   |-- main.py             FastAPI app and endpoints
|   |-- models.py           Prediction table definition
|   |-- predictor.py        Loads the model files and rebuilds the training pipeline
|   `-- schemas.py          Request and response validation
|-- models/
|   |-- encoder.pkl         Trained ZIP code encoder
|   |-- model.pkl           Trained LightGBM model
|   `-- poly.pkl            Trained polynomial feature transformer
|-- .gitignore
|-- README.md
`-- requirements.txt
```

---

## Getting Started

### Prerequisites

- [Git](https://git-scm.com/)
- Python 3.10 or newer

### 1. Clone the repository

```bash
git clone https://github.com/AlgoPhoenix369/housing-price-predictor.git
cd housing-price-predictor
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once and try again.

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

The library versions are pinned to the ones the model was trained with, so the saved files load exactly as intended.

### 4. Run the app

Run this from the project root:

```bash
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` in your browser. The interactive API documentation is at `http://localhost:8000/docs`.

The prediction history is stored in a local SQLite file (`predictions.db`) that is created automatically on first run. To reset it, stop the app and delete that file.

---

## Using the App

1. Choose whether you want to buy or sell.
2. Enter the ZIP code. Hover over the info icon next to the field to see the accepted range.
3. Fill in the living area, bedrooms, bathrooms, lot size, floors and house age.
4. Click **Predict price** to see the predicted price and its range.
5. Scroll to **Your prediction history** to review earlier predictions. Use **Show more** and **Show less** to expand or collapse the table, and **Clear history** to delete it.

### Input limits

| Field | Accepted values |
|-------|-----------------|
| ZIP code | 98001 to 99001 (only ZIP codes present in the training data) |
| Living area | 200 to 10,000 sqft |
| Bedrooms | 0 to 10 |
| Bathrooms | 0 to 10 |
| Lot size | 500 to 500,000 sqft |
| Floors | 1 to 4 |
| House age | 0 to 150 years |

---

## API Reference

The prediction and history endpoints require an `X-Client-Id` header (16 to 64 letters, numbers, `_` or `-`). The web page generates and sends it automatically.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/predict` | Predict a price and save it to the visitor's history |
| `GET` | `/api/history?limit=50` | List the visitor's recent predictions, newest first (limit 1 to 200) |
| `DELETE` | `/api/history` | Delete the visitor's whole history |

### Example request

```json
{
  "sqft_living": 1500,
  "no_of_bedrooms": 3,
  "no_of_bathrooms": 2,
  "sqft_lot": 5000,
  "no_of_floors": 1,
  "house_age": 20,
  "zipcode": 98001,
  "purpose": "buy"
}
```

### Example response (values are illustrative)

```json
{
  "id": 1,
  "predicted_price": 455000.0,
  "range_low": 435000.0,
  "range_high": 475000.0
}
```

### Errors

| Status | Meaning |
|--------|---------|
| `400` | Missing or invalid `X-Client-Id` header |
| `422` | Invalid input, or a ZIP code the model was not trained on |

The easiest way to try the API is the interactive documentation at `/docs`.

---

## Configuration

The app works with no configuration. One optional environment variable is supported:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy database address for the prediction history | A local SQLite file named `predictions.db` in the project root |

---

## Design Decisions

- **Model loaded once**: the three model files are loaded when the server starts and reused for every request, so predictions are fast.
- **Training pipeline in one place**: `predictor.py` rebuilds the exact preprocessing steps used in training, so the saved files receive input in the format they expect.
- **ZIP code guard**: the encoder ignores unknown ZIP codes, which would silently produce a wrong price. The API checks the ZIP code against the training data first and returns a clear error instead.
- **Input validation**: Pydantic schemas keep every field inside a realistic range before it reaches the model.
- **Anonymous history**: a random ID stored in the browser separates each visitor's history without requiring accounts.
- **Single service**: FastAPI serves both the API and the web page, so the app starts with one command.

---

## Troubleshooting

**`uvicorn` is not recognized**
Activate the virtual environment first. Your terminal prompt should show `(.venv)`.

**Warnings or errors when loading the model files**
Install the exact versions from `requirements.txt` inside a fresh virtual environment.

**"ZIP code is not covered by the model"**
Use a Washington State ZIP code between 98001 and 99001 that appears in the training data.

**Port 8000 is already in use**
Start the app on another port, for example `uvicorn app.main:app --port 8001`.

**The history is empty after switching browsers**
History is tied to the anonymous ID stored in each browser, and private windows start with a new ID.

---

## Limitations & Future Enhancements

- **ZIP Code Support:**

> **Note:** *Currently, the system supports ZIP codes **98001 to 99001 (Washington state)** as a **proof-of-concept**. Future updates will expand coverage to include more locations.*

---
