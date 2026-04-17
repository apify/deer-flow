# E-Commerce Actors

## Actor: apify/e-commerce-scraping-tool

Generic e-commerce scraper supporting Amazon, eBay, and other online shops. Returns product name, price, rating, reviews count, availability.

### Input Template

```json
{
  "startUrls": [
    {"url": "<PRODUCT_LISTING_URL>"}
  ],
  "maxItems": 20
}
```

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startUrls | array of objects | Product listing or search result URLs |
| maxItems | integer | Max products to return |

### Example

User: "Scrape laptop prices from Amazon"

```json
{
  "startUrls": [{"url": "https://www.amazon.com/s?k=laptop"}],
  "maxItems": 20
}
```

---

## Actor: voyager/booking-scraper

Scrapes Booking.com hotel listings: name, price, rating, location, amenities, availability.

### Input Template

```json
{
  "startUrls": [
    {"url": "https://www.booking.com/searchresults.html?ss=<DESTINATION>"}
  ],
  "maxItems": 20
}
```

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startUrls | array of objects | Booking.com search results URL. Build the URL by searching on booking.com and copying the results page URL. |
| maxItems | integer | Max hotels to return |

### Example

User: "Find hotels in Prague on Booking.com"

```json
{
  "startUrls": [{"url": "https://www.booking.com/searchresults.html?ss=Prague"}],
  "maxItems": 20
}
```

---

## Actor: maxcopell/tripadvisor-reviews

Scrapes reviews from TripAdvisor for restaurants, hotels, and attractions.

### Input Template

```json
{
  "startUrls": [
    {"url": "<TRIPADVISOR_LISTING_URL>"}
  ],
  "maxItems": 50
}
```

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startUrls | array of objects | Direct URL to a TripAdvisor restaurant, hotel, or attraction page |
| maxItems | integer | Max reviews to return |

### Example

User: "Get reviews for a restaurant on TripAdvisor"

```json
{
  "startUrls": [{"url": "https://www.tripadvisor.com/Restaurant_Review-g274707-d1058505-Reviews-Cafe_Savoy-Prague_Bohemia.html"}],
  "maxItems": 50
}
```
