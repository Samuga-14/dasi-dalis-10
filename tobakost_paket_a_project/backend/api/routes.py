"""Route catalogue used by the HTTP adapter and frontend documentation."""

PUBLIC_ROUTES = {
    "health": "GET /api/health",
    "analytics": "GET /api/data",
    "warehouse": "GET /api/warehouse?table=<allowed_table>",
    "prediction": "POST /api/predict",
}

ADMIN_ROUTES = {
    "create_listing": "POST /api/kos",
    "refresh_pipeline": "POST /api/run-etl",
}
