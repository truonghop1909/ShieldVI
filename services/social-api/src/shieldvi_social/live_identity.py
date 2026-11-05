"""Display handles on authorized live content; IDs remain canonical for AI."""
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy import select
from .models import User,Comment
from .content_store import visible_comment

class LiveIdentity(BaseModel):
    model_config=ConfigDict(extra='forbid')
    author_id:str=Field(min_length=1,max_length=120)
    author_username:str|None=Field(max_length=30)
    reply_to_user_id:str|None=Field(max_length=120)
    reply_to_username:str|None=Field(max_length=30)

def identities(db,rows,viewer):
    """Call after content visibility filtering; never serialize a User object."""
    parent_ids={r['parent_id'] for r in rows if r.get('parent_id')}
    parents={p.id:p for p in db.scalars(select(Comment).where(Comment.id.in_(parent_ids)))} if parent_ids else {}
    parents={key:row for key,row in parents.items() if row.visibility_status!='DELETED_BY_AUTHOR' and visible_comment(db,row,viewer)}
    authors={r['author_id'] for r in rows}|{p.author_id for p in parents.values()}
    names=dict(db.execute(select(User.id,User.username).where(User.id.in_(authors))).all()) if authors else {}
    result=[]
    for row in rows:
        parent=parents.get(row.get('parent_id'))
        identity=LiveIdentity(author_id=row['author_id'],author_username=names.get(row['author_id']),
            reply_to_user_id=parent.author_id if parent else None,
            reply_to_username=names.get(parent.author_id) if parent else None)
        result.append({**row,**identity.model_dump()})
    return result
