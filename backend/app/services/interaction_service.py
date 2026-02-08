from sqlalchemy.orm import Session
from models.interaction_model import UserInteraction
from models.article_model import ArticleStat
from schemas.interaction_schema import (
    UserInteractionCreateRequest,
    UserInteractionResponse,
    InteractionStatusResponse,
    InteractionToggleRequest,
    InteractionToggleResponse
)
from services.user_vector_service import mark_user_vector_dirty
from core.logger import get_logger
logger = get_logger(__name__)


def create_interaction(
    db: Session,
    user_id: int,
    data: UserInteractionCreateRequest
) -> UserInteractionResponse:

    logger.info(
        f"interaction_create_start user_id={user_id} "
        f"article_id={data.article_id} type={data.interaction_type}"
    )

    try:
        interaction = UserInteraction(
            user_id=user_id,
            article_id=data.article_id,
            interaction_type=data.interaction_type
        )

        db.add(interaction)

        stats = (
            db.query(ArticleStat)
            .filter(ArticleStat.article_id == data.article_id)
            .first()
        )

        if stats is None:
            stats = ArticleStat(
                article_id=data.article_id,
                view_count=0,
                like_count=0,
                save_count=0
            )
            db.add(stats)

        if data.interaction_type == "view":
            stats.view_count += 1
        elif data.interaction_type == "like":
            stats.like_count += 1
        elif data.interaction_type == "save":
            stats.save_count += 1

        logger.info(
            f"article_stats_updated article_id={data.article_id} "
            f"type={data.interaction_type}"
        )

        if data.interaction_type in ("like", "save"):
            mark_user_vector_dirty(db, user_id)
            logger.info(f"user_vector_marked_dirty user_id={user_id}")

        db.commit()
        db.refresh(interaction)

        logger.info(
            f"interaction_created interaction_id={interaction.interaction_id}"
        )

        return UserInteractionResponse(
            interaction_id=interaction.interaction_id,
            user_id=interaction.user_id,
            article_id=interaction.article_id,
            interaction_type=interaction.interaction_type,
            created_at=interaction.created_at
        )

    except Exception:
        db.rollback()
        logger.exception("interaction_create_failed")
        raise



def get_interaction_status(db: Session, user_id: int, article_id: int):
    like_exists = (
        db.query(UserInteraction)
        .filter(
            UserInteraction.user_id == user_id,
            UserInteraction.article_id == article_id,
            UserInteraction.interaction_type == "like"
        )
        .first()
        is not None
    )

    save_exists = (
        db.query(UserInteraction)
        .filter(
            UserInteraction.user_id == user_id,
            UserInteraction.article_id == article_id,
            UserInteraction.interaction_type == "save"
        )
        .first()
        is not None
    )

    logger.info(
        f"interaction_status_loaded user_id={user_id} article_id={article_id}"
    )

    return InteractionStatusResponse(
        liked=like_exists,
        saved=save_exists
    )



def toggle_interaction(
    db: Session,
    user_id: int,
    data: InteractionToggleRequest
) -> InteractionToggleResponse:

    logger.info(
        f"interaction_toggle_start user_id={user_id} "
        f"article_id={data.article_id} type={data.interaction_type}"
    )

    try:
        existing = (
            db.query(UserInteraction)
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.article_id == data.article_id,
                UserInteraction.interaction_type == data.interaction_type
            )
            .first()
        )

        stats = (
            db.query(ArticleStat)
            .filter(ArticleStat.article_id == data.article_id)
            .first()
        )

        if stats is None:
            stats = ArticleStat(
                article_id=data.article_id,
                view_count=0,
                like_count=0,
                save_count=0
            )
            db.add(stats)
            db.commit()
            db.refresh(stats)

        # REMOVE
        if existing:
            db.delete(existing)

            if data.interaction_type == "like" and stats.like_count > 0:
                stats.like_count -= 1

            if data.interaction_type == "save" and stats.save_count > 0:
                stats.save_count -= 1

            if data.interaction_type in ("like", "save"):
                mark_user_vector_dirty(db, user_id)
                logger.info(f"user_vector_marked_dirty user_id={user_id}")

            db.commit()

            logger.info(
                f"interaction_removed user_id={user_id} "
                f"article_id={data.article_id} type={data.interaction_type}"
            )

            return InteractionToggleResponse(
                interaction_type=data.interaction_type,
                active=False,
                new_count=stats.like_count if data.interaction_type == "like" else None
            )

        # CREATE
        new_interaction = UserInteraction(
            user_id=user_id,
            article_id=data.article_id,
            interaction_type=data.interaction_type
        )

        db.add(new_interaction)

        if data.interaction_type == "like":
            stats.like_count += 1

        if data.interaction_type == "save":
            stats.save_count += 1

        if data.interaction_type in ("like", "save"):
            mark_user_vector_dirty(db, user_id)
            logger.info(f"user_vector_marked_dirty user_id={user_id}")

        db.commit()

        logger.info(
            f"interaction_created user_id={user_id} "
            f"article_id={data.article_id} type={data.interaction_type}"
        )

        return InteractionToggleResponse(
            interaction_type=data.interaction_type,
            active=True,
            new_count=stats.like_count if data.interaction_type == "like" else None
        )

    except Exception:
        db.rollback()
        logger.exception("interaction_toggle_failed")
        raise
