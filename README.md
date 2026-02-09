# ArticleHub

ArticleHub is a full-stack article publishing platform with a content-based recommendation engine.
The system allows users to create, read, and interact with articles while generating personalized recommendations using natural-language feature extraction and similarity scoring.

This project demonstrates backend API design, relational database modeling, frontend integration, and applied machine-learning concepts in a single system.

---

## Project Overview

ArticleHub separates application concerns into three major domains:

* Content management (articles, tags, authorship)
* User interaction tracking (views, likes, saves)
* Recommendation data (vectors, similarity scoring, statistics)

The backend acts as the single source of truth for all interaction and recommendation data.

---

## Features

### Content System

* Article creation and publishing
* Tagging system
* Article viewing interface
* Author attribution
* Rich text article content

### Interaction System

* View tracking
* Like / Unlike articles
* Save / Unsave articles
* Persistent interaction state
* Automatic statistics updates

### Recommendation Engine

* TF-IDF vectorization of article content
* Tag-based similarity scoring
* Weighted user-interaction profiling
* Cold-start recommendation handling
* Cosine similarity ranking

---

## Recommendation Logic

Article similarity is computed using vector representations derived from:

* Article text content
* Article tags

User preference vectors are calculated using weighted interactions:

| Interaction | Weight |
| ----------- | ------ |
| View        | 1      |
| Like        | 2      |
| Save        | 3      |

Final recommendation score:

score = 0.7 × text_similarity + 0.3 × tag_similarity

Cold-start users receive recommendations based on the global article centroid.

---

## Technology Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL

### Frontend

* HTML
* CSS
* Vanilla JavaScript
* REST API integration

### Machine Learning

* scikit-learn
* TF-IDF Vectorizer
* Cosine Similarity

---

## Database Design

### Core Tables

* users
* articles
* tags
* article_tags
* user_interactions

### Derived Tables

* article_vectors
* user_vectors
* article_stats
* user_preferred_tags

### Interaction Constraint

```sql
UNIQUE (user_id, article_id, interaction_type)
```

This prevents duplicate interactions such as multiple likes from the same user.

---

## API Endpoints

### Articles

```
GET /articles/{article_id}
```

Returns a complete article with metadata and tags.

---

### Recommendations

```
GET /recommendations/{user_id}
```

Returns ranked article recommendations for a user.

---

### Interaction Status

```
GET /interactions/status?user_id={id}&article_id={id}
```

Returns like/save state for an article.

---

### Toggle Interaction

```
POST /interactions/toggle?user_id={id}
```

Used for like/unlike and save/unsave operations.

---

## Frontend Pages

Home Page

* Displays recommended articles
* Loading state handling
* Navigation to article pages

View Article Page

* Dynamic article loading
* Tag display
* Interaction buttons
* Metadata display

Create Article Page

* Rich text editor
* Tag input system
* Autosave support
* Preview functionality
* Publish and discard options

---

## Setup Instructions

### Clone Repository

```bash
git clone https://github.com/your-username/articlehub.git
cd articlehub
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Backend Server

```bash
uvicorn main:app --reload
```

Backend runs at:

```
http://localhost:8000
```

### Open Frontend

Open the HTML files directly in a browser or serve them using a static server.

---

## Design Principles

* Backend-driven state management
* Normalized relational schema
* Deterministic recommendation logic
* Clear separation of system responsibilities
* Idempotent interaction operations
* Explainable ML pipeline

---

## Testing

Example request:

```bash
GET http://localhost:8000/interactions/status?user_id=1&article_id=5
```

---

## Future Improvements

* Authentication system (JWT)
* Search functionality
* Pagination support
* Trending articles endpoint
* Vector search optimization (FAISS / pgvector)
* UI improvements
* Reading-time tracking

---

## License

This project is intended for educational and experimental purposes.

---

## Author

ArticleHub was developed as a full-stack system integrating:

* database design
* backend API development
* frontend interaction logic
* content-based recommendation systems
