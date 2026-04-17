---
name: apify-scrapper
description: Use this skill for ALL web scraping tasks. Trigger on: scrape Instagram, scrape Facebook, scrape YouTube, scrape TikTok, collect Google Maps listings, scrape e-commerce products, scrape TripAdvisor reviews, scrape Booking.com hotels, or ANY task that requires collecting structured data from a specific website or social platform.
---

# Apify Ultimate Scraper Skill

## Core Rule

Never call `apify_actor_discover` for tasks in the routing table below.
Always use the exact actor IDs listed here. Load the reference file to get the input template before calling `apify_actor_start`.

## Actor Routing Table

| Task | Actor ID | Reference |
|------|----------|-----------|
| Instagram profiles | apify/instagram-profile-scraper | references/instagram.md |
| Instagram posts/hashtags | apify/instagram-post-scraper | references/instagram.md |
| Instagram comments | apify/instagram-comment-scraper | references/instagram.md |
| Instagram reels | apify/instagram-reel-scraper | references/instagram.md |
| Google Maps listings | compass/crawler-google-places | references/google-maps.md |
| YouTube videos/channels | streamers/youtube-scraper | references/youtube.md |
| TikTok profiles/videos | clockworks/tiktok-scraper | references/tiktok.md |
| Facebook pages/posts | apify/facebook-pages-scraper | references/facebook.md |
| E-commerce products | apify/e-commerce-scraping-tool | references/ecommerce.md |
| Booking.com hotels | voyager/booking-scraper | references/ecommerce.md |
| TripAdvisor reviews | maxcopell/tripadvisor-reviews | references/ecommerce.md |

## Workflow

1. Match the user's task to a row in the routing table.
2. Load the reference file for that actor using `read_file`.
3. Populate the input template with values from the user's request.
4. Call `apify_actor_start` with the actor ID and populated input.
5. Call `apify_actor_await` with the returned `runId` and `datasetId` to wait for results.

**Multiple parallel actors:** call `apify_actor_start` once per actor first, then call `apify_actor_await` for each run in sequence. The actors execute in parallel on Apify's side — sequential waiting still yields parallel execution time.

## When to Fall Back to Discovery

Only use `apify_actor_discover` when the task does not match any row above. In that case first read `references/actor-catalog.md` for the curated shortlist before falling back to a live store search.
