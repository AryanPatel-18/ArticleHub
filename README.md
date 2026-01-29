# 📰 ArticleHub

**ArticleHub** is a content-based article publishing and recommendation system.
It allows users to read and write articles, interact with them (view, like, save), and receive personalized recommendations based on content similarity and interaction history.

The system is designed with proper separation between:
**content**, **user interactions**, and **derived recommendation data**.

---

## 🚀 Features

### 🧑‍💻 User Features

* Read articles
* Write and publish articles
* Tag articles by topic
* Like and save articles
* View personalized article recommendations
* Interaction state persists across refresh (liked/saved status)

---

### 🤖 Recommendation System

* TF-IDF vectorization of:

  * Article text
  * Article tags
* Cosine similarity for ranking
* User vector computed from past interactions:

  * view = weight 1
  * like = weight 2
  * save = weight 3
* Cold-start users get recommendations from the global article centroid

---

## 🧱 Technology Stack

### Frontend

* HTML
* CSS
* JavaScript (no framework)
* REST API communication

### Backend

* Python
* FastAPI
* SQLAlchemy ORM
* PostgreSQL

### Machine Learning

* scikit-learn
* TF-IDF Vectorizer
* Cosine similarity

---

## 🗄️ Database Schema

### Core Tables

* **users**
* **articles**
* **tags**
* **article_tags**
* **user_interactions**

### Derived Tables

* **article_vectors**
* **user_vectors**
* **article_stats**
* **user_preferred_tags**

### Important Constraint

```sql
UNIQUE (user_id, article_id, interaction_type)
```

Prevents duplicate likes and saves.

---

## 🔁 Interaction System (Like / Save)

Each interaction is stored as:

```
(user_id, article_id, interaction_type)
```

Where:

* interaction_type ∈ { view, like, save }

Presence of a row = active
Absence of a row = inactive

Backend is the **source of truth**.

---

## 🌐 API Endpoints

### 📄 Articles

```
GET /articles/{article_id}
```

Returns a full article with author and tags.

---

### 📊 Recommendations

```
GET /recommendations/{user_id}
```

Returns top recommended articles for a user.

---

### ❤️ Interaction Status

```
GET /interactions/status?user_id=U&article_id=A
```

Response:

```json
{
  "liked": true,
  "saved": false
}
```

---

### 🔁 Toggle Interaction

```
POST /interactions/toggle?user_id=U
```

Body:

```json
{
  "article_id": 5,
  "interaction_type": "like"
}
```

Response:

```json
{
  "interaction_type": "like",
  "active": true,
  "new_count": 12
}
```

Used for:

* like / unlike
* save / unsave

---

## 🖥️ Frontend Pages

### 🏠 Home Page

* Displays recommended articles
* Uses a loading spinner while fetching data
* Each article links to:

```
view_article.html?article_id=...
```

---

### 📖 View Article Page

* Loads article dynamically
* Shows:

  * title
  * author
  * date
  * tags
  * content
* Like & Save buttons:

  * Filled when active
  * Outline when inactive

---

### ✍️ Create Article Page

* Rich text editor
* Tag input system
* Autosave
* Preview
* Publish and discard functionality

---

## 🧠 Recommendation Logic

Final recommendation score:

```
score = 0.7 × text_similarity + 0.3 × tag_similarity
```

Similarity is computed using:

```
cosine_similarity(user_vector, article_vector)
```

---

## 📈 Article Statistics

Stored in:

```
article_stats
```

Tracks:

* view_count
* like_count

Updated automatically when:

* interaction rows are inserted or removed

---

## 🧪 Testing

Example:

```
GET http://localhost:8000/interactions/status?user_id=1&article_id=5
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/articlehub.git
cd articlehub
```

### 2. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the backend server

```bash
uvicorn main:app --reload
```

### 4. Open frontend

Open the HTML files directly in a browser or serve them with a static server.

---

## 🧩 Design Principles

* Backend is authoritative
* No frontend trust for likes/saves
* Proper normalization
* No duplicate interaction rows
* Explainable recommendation logic
* Separation of:

```
articles ≠ interactions ≠ stats ≠ vectors
```

---

## 🛠️ Future Improvements

* Track time spent per article
* Add FAISS / pgvector for faster similarity search
* Add search functionality
* Improve UI/UX
* Add authentication (JWT)
* Pagination for articles
* Trending articles endpoint

---

## 📜 License

This project is for educational and experimental use.

---

## 👤 Author

Developed as a full-stack and ML-integrated project combining:

* database design
* backend APIs
* frontend logic
* and recommendation systems
