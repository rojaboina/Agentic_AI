# Reading Taste Profile

This profile is based on the initial list of books Roja has read. It is intentionally lightweight and should be updated as ratings, notes, rejections, and weekly feedback are added.

## Recommendation Modules

The recommender should support these modules as first-class categories:

- Autobiography / Memoir
- Self-Help / Personal Growth
- Technical
- Poetry / Reflective Writing
- Philosophy
- Spirituality

## Strong Signals

- Prefers books about meaning, resilience, mortality, healing, and inner transformation.
- Responds to practical spirituality, manifestation, forgiveness, and mindset-oriented self-help.
- Enjoys concise reflective writing, poetic/philosophical fragments, and emotionally warm books.
- Values craft and clarity in writing, especially nonfiction communication and creative process.
- Likes practical systems for attention, wealth, communication, and personal growth.
- In technical reading, favors deep architecture, data systems, data engineering, and AI orchestration.

## Genre Preferences

### Autobiography / Memoir

Likely fit:
- Reflective life stories with emotional depth.
- Medical, spiritual, creative, or adversity-driven memoirs.
- Books that connect personal suffering to meaning, service, or transformation.

Avoid:
- Celebrity memoirs that are mostly fame-driven.
- Memoirs without introspection or craft.

### Self-Help / Spiritual Growth

Likely fit:
- Practical wisdom with exercises or principles.
- Healing, mindset, compassion, purpose, communication, focus, or financial freedom.
- Books that feel warm and spiritually open, but still applicable.

Avoid:
- Overly aggressive productivity books.
- Generic motivation without depth.

### Technical

Likely fit:
- Data engineering, distributed systems, AI agents/orchestration, applied ML systems, system design.
- Books with durable concepts rather than quick trend-chasing.
- Practical architecture guidance with examples.

Avoid:
- Very shallow AI hype books.
- Highly academic books unless they are clearly useful for building.

### Poetry / Reflective Writing

Likely fit:
- Accessible poetry, prose poetry, illustrated philosophy, and healing reflections.
- Themes of identity, tenderness, resilience, self-trust, love, grief, and hope.

Avoid:
- Extremely dense or obscure poetry as a default recommendation.

### Philosophy

Likely fit:
- Practical philosophy connected to daily life, meaning, ethics, suffering, freedom, or attention.
- Existential, Stoic, Buddhist-adjacent, and contemplative works that are readable without being simplistic.
- Books that help connect inner life with action, responsibility, and purpose.

Avoid:
- Very technical academic philosophy as a default recommendation.
- Abstract argument-heavy texts unless paired with strong context or commentary.

### Spirituality

Likely fit:
- Spiritual growth, forgiveness, healing, prayer/meditation, manifestation, consciousness, and mystical experience.
- Warm, reflective books that leave room for wonder while still offering practices or insight.
- Memoir-style spirituality and accessible spiritual classics.

Avoid:
- Highly dogmatic books unless specifically requested.
- Shallow manifestation books that repeat ideas without new depth.

## Current Recommendation Query Template

Recommend one book per genre for this week:

- autobiography/memoir
- self-help/spiritual growth
- technical
- poetry/reflective writing
- philosophy
- spirituality

Filter out books already read. Prefer recommendations that connect to Roja's taste profile and explain the match using specific evidence.

Each recommended book must include:

- Date added
- Module/category
- Title
- Author
- Short summary
- Goodreads rating
- Date the Goodreads rating was checked
- Why it matches Roja's taste profile
- Source URL when available
