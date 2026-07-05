# Recommendation Record

Every book added to the recommendation list should be stored as a structured record.

## Required Fields

- `date_added`: Date the recommendation was added, in `YYYY-MM-DD` format.
- `module`: Recommendation module, such as `technical`, `spirituality`, or `poetry_reflective_writing`.
- `title`: Book title.
- `author`: Author name.
- `summary`: Short plain-language summary of the book.
- `goodreads_rating`: Goodreads average rating at the time it was checked.
- `goodreads_rating_checked_at`: Date the Goodreads rating was checked, in `YYYY-MM-DD` format.
- `status`: Current state, such as `recommended`, `added_to_list`, `rejected`, `already_read`, or `maybe_later`.
- `why_recommended`: Personalized reason the book was selected for Roja.
- `source_url`: URL used for rating or source evidence, when available.
- `notes`: Optional notes from Roja or the recommender.

## Important Goodreads Note

Goodreads ratings change over time, so the recommender should treat them as time-sensitive data. Each rating must include the date it was checked.

If live lookup is available, fetch the current Goodreads rating before adding a recommendation. If live lookup is not available, leave `goodreads_rating` blank and mark the rating as needing verification.
