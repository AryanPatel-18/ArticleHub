from datetime import date
from io import BytesIO
from collections import defaultdict
import matplotlib
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from models.article_model import Article
from models.interaction_model import UserInteraction
from models.user_model import User
from core.logger import get_logger

logger = get_logger(__name__)
matplotlib.use("Agg")



def generate_user_article_interaction_graph(
    db: Session,
    user_id: int
) -> BytesIO:
    logger.info(f"analytics_graph_start user_id={user_id}")

    try:
        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

        if not user:
            logger.warning(f"analytics_user_not_found user_id={user_id}")
            raise ValueError("User not found")

        start_date = user.created_at.date()
        end_date = date.today()

        article_ids = [
            row.article_id
            for row in db.query(Article.article_id)
            .filter(Article.author_id == user_id)
            .all()
        ]

        logger.info(
            f"analytics_articles_loaded user_id={user_id} "
            f"count={len(article_ids)}"
        )

        if not article_ids:
            logger.info(f"analytics_no_articles user_id={user_id}")

            fig, ax = plt.subplots()
            ax.set_title("No articles published yet")

            buffer = BytesIO()
            plt.savefig(buffer, format="png")
            plt.close()
            buffer.seek(0)
            return buffer

        interactions = (
            db.query(
                UserInteraction.interaction_type,
                UserInteraction.created_at
            )
            .filter(UserInteraction.article_id.in_(article_ids))
            .all()
        )

        logger.info(
            f"analytics_interactions_loaded user_id={user_id} "
            f"count={len(interactions)}"
        )

        daily_counts = defaultdict(lambda: {
            "view": 0,
            "like": 0,
            "save": 0
        })

        for interaction_type, created_at in interactions:
            interaction_date = created_at.date()
            daily_counts[interaction_date][interaction_type] += 1

        dates = []
        views = []
        likes = []
        saves = []

        cumulative_views = 0
        cumulative_likes = 0
        cumulative_saves = 0

        current_date = start_date
        while current_date <= end_date:
            counts = daily_counts[current_date]

            cumulative_views += counts["view"]
            cumulative_likes += counts["like"]
            cumulative_saves += counts["save"]

            dates.append(current_date)
            views.append(cumulative_views)
            likes.append(cumulative_likes)
            saves.append(cumulative_saves)

            current_date = current_date.fromordinal(
                current_date.toordinal() + 1
            )

        bg_color = "#F3F1E7"
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        ax.plot(dates, views, label="Views")
        ax.plot(dates, likes, label="Likes")
        ax.plot(dates, saves, label="Saves")

        ax.set_xlabel("Date")
        ax.set_ylabel("Count")
        ax.set_title("Cumulative Interactions on My Articles")

        ax.legend()
        ax.grid(False)

        fig.autofmt_xdate()

        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close()

        buffer.seek(0)

        logger.info(f"analytics_graph_generated user_id={user_id}")

        return buffer

    except Exception:
        logger.exception(f"analytics_graph_failed user_id={user_id}")
        raise
