from sqlalchemy.orm import Session
from models.interaction_model import UserInteraction
from models.article_model import ArticleStat
from schemas.interaction_schema import UserInteractionCreateRequest, UserInteractionResponse, InteractionStatusResponse, InteractionToggleRequest, InteractionToggleResponse

def create_interaction(
    db: Session,
    user_id: int,
    data: UserInteractionCreateRequest
) -> UserInteractionResponse:

    # 1. Insert interaction row
    interaction = UserInteraction(
        user_id=user_id,
        article_id=data.article_id,
        interaction_type=data.interaction_type
    )

    db.add(interaction)

    # 2. Fetch or create stats row
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

    # 3. Update correct counter
    if data.interaction_type == "view":
        stats.view_count += 1
    elif data.interaction_type == "like":
        stats.like_count += 1
    elif data.interaction_type == "save":
        stats.save_count += 1

    # 4. Commit once
    db.commit()
    db.refresh(interaction)

    return UserInteractionResponse(
        interaction_id=interaction.interaction_id,
        user_id=interaction.user_id,
        article_id=interaction.article_id,
        interaction_type=interaction.interaction_type,
        created_at=interaction.created_at
    )


def get_interaction_status(db: Session, user_id: int, article_id: int):
    like_exists = (
        db.query(UserInteraction)
        .filter(
            UserInteraction.user_id == user_id,
            UserInteraction.article_id == article_id,
            UserInteraction.interaction_type == "like"
        )
        .first()
        is not None # Checking if the query returned anything or not
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

    return InteractionStatusResponse(
        liked=like_exists,
        saved=save_exists
    )
    
def toggle_interaction(
    db: Session,
    user_id: int,
    data: InteractionToggleRequest
) -> InteractionToggleResponse:

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
        stats = ArticleStat(article_id=data.article_id, view_count=0, like_count=0)
        db.add(stats)
        db.commit()
        db.refresh(stats)

    # CASE 1: interaction exists → REMOVE
    if existing:
        db.delete(existing)

        if data.interaction_type == "like":
            if stats.like_count > 0:
                stats.like_count -= 1
        
        if data.interaction_type == 'save':
            if stats.save_count > 0:
                stats.save_count -= 1

        db.commit()

        return InteractionToggleResponse(
            interaction_type=data.interaction_type,
            active=False,
            new_count=stats.like_count if data.interaction_type == "like" else None
        )

    # CASE 2: interaction does not exist → CREATE
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
    
    db.commit()

    return InteractionToggleResponse(
        interaction_type=data.interaction_type,
        active=True,
        new_count=stats.like_count if data.interaction_type == "like" else None
    )