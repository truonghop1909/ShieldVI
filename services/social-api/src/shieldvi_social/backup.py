"""SQLite online backup/verification. Does not restore, overwrite or migrate DBs."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from sqlalchemy.engine import make_url
from .config import Settings

SUPPORTED={'0001_users','0002_content','0003_worker','0004_review'}


def verify(path):
    path=Path(path).resolve(strict=True)
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as connection:
        if connection.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('Backup integrity check failed')
        if connection.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Backup foreign key check failed')
        revisions=[row[0] for row in connection.execute('SELECT version_num FROM alembic_version')]
        if len(revisions)!=1 or revisions[0] not in SUPPORTED:raise ValueError('Unknown Social DB schema')
    return {'integrity':'ok','foreign_keys':'ok','schema':revisions[0]}


def create_backup(settings,destination):
    url=make_url(settings.database_url)
    if url.drivername!='sqlite':raise ValueError('This backup utility supports SQLite only')
    source=Path(url.database).resolve(strict=True)
    destination=Path(destination).absolute()
    if source==destination.resolve():raise ValueError('Source and backup must differ')
    verify(source)
    # Exclusive creation: never replace any existing backup, symlink or live DB.
    with destination.open('xb'):
        pass
    try:
        destination.chmod(0o600)
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as origin,closing(sqlite3.connect(destination)) as target:
            origin.backup(target,pages=128)
            target.commit()
        return verify(destination)
    except Exception:
        destination.unlink(missing_ok=True)  # Only the new file exclusively created above.
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path)
    group.add_argument('--verify',type=Path)
    args=parser.parse_args()
    try:
        result=verify(args.verify) if args.verify else create_backup(Settings.from_env(),args.output)
        print(json.dumps({'status':'verified',**result}))
        return 0
    except (OSError,ValueError,sqlite3.Error) as error:
        print(json.dumps({'status':'failed','error_type':type(error).__name__,
            'hint':'Check DB configuration, schema, permissions and use a new backup filename.'}))
        return 1


if __name__=='__main__':raise SystemExit(main())
