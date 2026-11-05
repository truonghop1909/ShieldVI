from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .content_schemas import CommentCreate, CommentOutput, CommentPage, ContentCreate, ContentDelete, ContentUpdate, PostOutput, PostPage
from .content_store import audit, blocked_comments, enqueue, fingerprint, mutate, output, prior_create, privileged, rate_limit, visible_comment, visible_post
from .dependencies import Principal, content_writer, current_principal, get_content_write_db, get_db
from .models import Comment, Post, PUBLIC_VISIBILITY

router = APIRouter(prefix="/api/v1", tags=["content"])


def must_read(row, user, db):
    visible = visible_comment(db, row, user) if isinstance(row, Comment) else visible_post(row, user)
    if not visible:
        raise HTTPException(404, "Content not found")
    return row


def lock_post(db, post_id):
    return db.scalar(select(Post).where(Post.id == post_id).with_for_update().execution_options(populate_existing=True))


def lock_comment(db, comment_id):
    initial = db.get(Comment, comment_id)
    if initial is None:
        raise HTTPException(404, "Content not found")
    lock_post(db, initial.post_id)  # Same lock order as comment creation/post deletion.
    return db.scalar(select(Comment).where(Comment.id == comment_id).with_for_update().execution_options(populate_existing=True))


def persist_create(db, model, row, user, key, digest, response):
    try:
        db.add(row)
        db.flush()  # ID/defaults exist before job and audit, all in the same transaction.
        enqueue(db, row)
        audit(db, row, user, "CREATE")
        db.commit()
        return output(row, user)
    except IntegrityError:
        db.rollback()
        prior = prior_create(db, model, user, key, digest)
        if prior is None:
            raise HTTPException(409, "Content could not be created") from None
        response.status_code = 200
        response.headers["Idempotency-Replayed"] = "true"
        return output(prior, user)


@router.post("/posts", response_model=PostOutput, status_code=201)
def create_post(payload: ContentCreate, request: Request, response: Response,
                idempotency_key: UUID = Header(alias="Idempotency-Key"),
                principal: Principal = Depends(content_writer), db: Session = Depends(get_content_write_db)):
    user = principal.user
    key, digest = str(idempotency_key), fingerprint(payload.body)
    prior = prior_create(db, Post, user, key, digest)
    if prior:
        response.status_code = 200
        response.headers["Idempotency-Replayed"] = "true"
        return output(prior, user)
    rate_limit(db, request.app.state.settings, user)
    row = Post(author_id=user.id, body=payload.body, create_key=key, request_hash=digest)
    return persist_create(db, Post, row, user, key, digest, response)


@router.get("/feed", response_model=PostPage)
def feed(page: int = Query(default=1, ge=1, le=10000), page_size: int = Query(default=20, ge=1, le=50),
         principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
    query = select(Post).where(Post.visibility_status.in_(PUBLIC_VISIBILITY))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Post.created_at.desc(), Post.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [output(row, principal.user) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/posts/{post_id}", response_model=PostOutput)
def read_post(post_id: UUID, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
    return output(must_read(db.get(Post, str(post_id)), principal.user, db), principal.user)


@router.patch("/posts/{post_id}", response_model=PostOutput)
def edit_post(post_id: UUID, payload: ContentUpdate, request: Request,
              principal: Principal = Depends(content_writer), db: Session = Depends(get_content_write_db)):
    rate_limit(db, request.app.state.settings, principal.user)
    row = must_read(lock_post(db, str(post_id)), principal.user, db)
    return output(mutate(db, row, principal.user, payload), principal.user)


@router.delete("/posts/{post_id}", response_model=PostOutput)
def delete_post(post_id: UUID, payload: ContentDelete, request: Request,
                principal: Principal = Depends(content_writer), db: Session = Depends(get_content_write_db)):
    rate_limit(db, request.app.state.settings, principal.user)
    row = must_read(lock_post(db, str(post_id)), principal.user, db)
    return output(mutate(db, row, principal.user, payload, deleting=True), principal.user)


@router.post("/posts/{post_id}/comments", response_model=CommentOutput, status_code=201)
def create_comment(post_id: UUID, payload: CommentCreate, request: Request, response: Response,
                   idempotency_key: UUID = Header(alias="Idempotency-Key"),
                   principal: Principal = Depends(content_writer), db: Session = Depends(get_content_write_db)):
    user = principal.user
    post_id, parent_id, key = str(post_id), str(payload.parent_id) if payload.parent_id else None, str(idempotency_key)
    digest = fingerprint(payload.body, post_id, parent_id)
    prior = prior_create(db, Comment, user, key, digest)
    if prior:
        response.status_code = 200
        response.headers["Idempotency-Replayed"] = "true"
        return output(prior, user)
    rate_limit(db, request.app.state.settings, user)
    post = must_read(lock_post(db, post_id), user, db)
    if post.visibility_status == "DELETED_BY_AUTHOR":
        raise HTTPException(409, "Cannot comment on a deleted post")
    depth = 0
    if parent_id:
        parent = db.get(Comment, parent_id)
        if parent is None or parent.post_id != post_id or parent.visibility_status == "DELETED_BY_AUTHOR":
            raise HTTPException(404, "Parent comment not found in this post")
        must_read(parent, user, db)
        depth = parent.depth + 1
        if depth > 32:
            raise HTTPException(422, "Maximum reply depth is 32")
    row = Comment(author_id=user.id, body=payload.body, post_id=post_id, parent_id=parent_id,
                  depth=depth, create_key=key, request_hash=digest)
    return persist_create(db, Comment, row, user, key, digest, response)


@router.get("/posts/{post_id}/comments", response_model=CommentPage)
def comments(post_id: UUID, page: int = Query(default=1, ge=1, le=10000),
             page_size: int = Query(default=20, ge=1, le=50),
             principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
    post_id = str(post_id)
    user = principal.user
    post = must_read(db.get(Post, post_id), user, db)
    if post.visibility_status == "DELETED_BY_AUTHOR":
        raise HTTPException(404, "Content not found")
    query = select(Comment).where(Comment.post_id == post_id, Comment.visibility_status != "DELETED_BY_AUTHOR")
    if not privileged(user):
        own = Comment.author_id == user.id
        if post.visibility_status in PUBLIC_VISIBILITY:
            blocked = blocked_comments(post_id)
            public = and_(Comment.visibility_status.in_(PUBLIC_VISIBILITY), Comment.id.not_in(select(blocked.c.id)))
            query = query.where(or_(own, public))
        else:
            query = query.where(own)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Comment.created_at, Comment.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [output(row, user) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/comments/{comment_id}", response_model=CommentOutput)
def read_comment(comment_id: UUID, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)):
    return output(must_read(db.get(Comment, str(comment_id)), principal.user, db), principal.user)


@router.patch("/comments/{comment_id}", response_model=CommentOutput)
def edit_comment(comment_id: UUID, payload: ContentUpdate, request: Request,
                 principal: Principal = Depends(content_writer), db: Session = Depends(get_content_write_db)):
    rate_limit(db, request.app.state.settings, principal.user)
    row = must_read(lock_comment(db, str(comment_id)), principal.user, db)
    return output(mutate(db, row, principal.user, payload), principal.user)


@router.delete("/comments/{comment_id}", response_model=CommentOutput)
def delete_comment(comment_id: UUID, payload: ContentDelete, request: Request,
                   principal: Principal = Depends(content_writer), db: Session = Depends(get_content_write_db)):
    rate_limit(db, request.app.state.settings, principal.user)
    row = must_read(lock_comment(db, str(comment_id)), principal.user, db)
    return output(mutate(db, row, principal.user, payload, deleting=True), principal.user)
