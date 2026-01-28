from database.db import SessionLocal, engine
from models import User, Article

def test_relationships():
    db = SessionLocal()

    try:
        # 1. Create a user
        user = User(
            user_email="reltest@example.com",
            user_name="reltestuser",
            password_hash="fakehash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print("User created:", user.user_id)

        # 2. Create an article authored by that user
        article = Article(
            author_id=user.user_id,
            title="Relationship Test Article",
            content="Testing SQLAlchemy relationships."
        )
        db.add(article)
        db.commit()
        db.refresh(article)

        print("Article created:", article.article_id)

        # 3. TEST: article → author
        assert article.author.user_id == user.user_id
        print("article.author works")

        # 4. TEST: user → articles
        assert len(user.articles) == 1
        assert user.articles[0].article_id == article.article_id
        print("user.articles works")

        print("✅ Relationship resolution test PASSED")

    finally:
        db.close()


if __name__ == "__main__":
    test_relationships()
