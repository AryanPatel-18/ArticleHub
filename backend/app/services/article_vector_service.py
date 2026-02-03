import json
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from collections import Counter
from models.article_model import Article, ArticleTag, Tag
from models.vector_model import ArticleVector


def create_article_vector(db: Session, article_id: int):
    """
    Recompute TF-IDF using ALL articles,
    then store vector ONLY for the given article_id.
    """

    # 1. Fetch all articles
    articles = db.query(Article).all()

    article_ids = []
    texts = []

    for article in articles:
        article_ids.append(article.article_id)
        texts.append(article.content)

    # 2. Fetch tags for all articles
    rows = (
        db.query(ArticleTag.article_id, Tag.tag_name)
        .join(Tag, ArticleTag.tag_id == Tag.tag_id)
        .all()
    )

    tag_map = {}
    for aid, tag_name in rows:
        tag_map.setdefault(aid, []).append(tag_name)

    tag_texts = []
    for aid in article_ids:
        tag_texts.append(" ".join(tag_map.get(aid, [])))

    # 3. Fit TF-IDF on FULL corpus
    text_vectorizer = TfidfVectorizer(stop_words="english", max_features=50000)
    tag_vectorizer = TfidfVectorizer()

    text_vectors = text_vectorizer.fit_transform(texts)
    tag_vectors = tag_vectorizer.fit_transform(tag_texts)

    # 4. Find index of target article
    target_index = article_ids.index(article_id)

    text_row = text_vectors[target_index]
    tag_row = tag_vectors[target_index]

    text_vector_json = {
        "indices": text_row.indices.tolist(),
        "values": text_row.data.tolist()
    }

    tag_vector_json = {
        "indices": tag_row.indices.tolist(),
        "values": tag_row.data.tolist()
    }

    # 5. Insert into article_vectors
    vector = ArticleVector(
        article_id=article_id,
        text_vector=json.dumps(text_vector_json),
        tag_vector=json.dumps(tag_vector_json),
        vector_version=1
    )

    db.add(vector)
    db.commit()

TOKEN_PATTERN = re.compile(r"\b[a-zA-Z]{2,}\b")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_query_vector(db: Session, query: str) -> dict:
    """
    Builds a TF-IDF sparse vector for a search query
    using the SAME vocabulary and IDF values as article vectors.
    """

    # 1. Load latest vocabulary + idf (single source of truth)
    sample_vector = (
        db.query(ArticleVector)
        .order_by(ArticleVector.vector_version.desc())
        .first()
    )

    if not sample_vector:
        raise RuntimeError("No article vectors exist. Cannot build query vector.")

    vocab = sample_vector.text_vector["vocabulary"]
    idf = sample_vector.text_vector["idf"]

    # 2. Tokenize query
    tokens = tokenize(query)
    if not tokens:
        return {"indices": [], "values": []}

    term_counts = Counter(tokens)
    total_terms = sum(term_counts.values())

    indices = []
    values = []

    # 3. Build TF-IDF vector
    for term, count in term_counts.items():
        if term not in vocab:
            continue

        idx = vocab[term]
        tf = count / total_terms
        tf_idf = tf * idf[idx]

        indices.append(idx)
        values.append(tf_idf)

    return {
        "indices": indices,
        "values": values
    }