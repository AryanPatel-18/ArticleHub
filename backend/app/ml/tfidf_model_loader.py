import pickle
from pathlib import Path

MODEL_DIR = Path("model_store")
TEXT_MODEL_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
TAG_MODEL_PATH = MODEL_DIR / "tag_vectorizer.pkl"

_text_vectorizer = None
_tag_vectorizer = None

# Fetching the vector weights from the ML file
def get_vectorizers():
    global _text_vectorizer, _tag_vectorizer

    if _text_vectorizer is None:
        with open(TEXT_MODEL_PATH, "rb") as f:
            _text_vectorizer = pickle.load(f)

    if _tag_vectorizer is None:
        with open(TAG_MODEL_PATH, "rb") as f:
            _tag_vectorizer = pickle.load(f)

    return _text_vectorizer, _tag_vectorizer
