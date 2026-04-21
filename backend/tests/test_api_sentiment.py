"""
Tests for sentiment analysis API endpoints.
"""


def test_sentiment_health(client):
    response = client.get("/api/v1/sentiment/health")
    assert response.status_code == 200


def test_get_sentiment(client):
    """Test full sentiment pipeline."""
    response = client.get("/api/v1/sentiment/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "symbol" in data or "ticker" in data
    assert "aggregated_sentiment" in data or "status" in data


def test_get_news(client):
    """Test news fetch endpoint."""
    response = client.get("/api/v1/sentiment/news/AAPL?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data or "status" in data


def test_news_only(client):
    """Test news-only endpoint (no sentiment analysis)."""
    response = client.get("/api/v1/sentiment/AAPL/news-only?days=7")
    assert response.status_code == 200
