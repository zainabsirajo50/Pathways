"""Local administrative CLI. No HTTP endpoints or credential CLI arguments."""
import argparse
import json
import os
import uuid
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.config import BACKEND, get_settings
from app.services.publication import (authorize, destination, snapshot, validate_review, record_review,
    approve_destination, revoke_destination, ReviewError, AuthorizationError)

def main(argv=None):
    parser = argparse.ArgumentParser(description='Authenticated local destination content administration')
    parser.add_argument('action',choices=['inspect','validate','review','approve','revoke'])
    parser.add_argument('slug')
    parser.add_argument('--evidence-file', help='JSON file with evidence and notes; contains no credentials')
    parser.add_argument('--review-id', type=uuid.UUID)
    parser.add_argument('--reason')
    parser.add_argument('--confirm', action='store_true', help='Explicitly confirm review, approval or revocation')
    args = parser.parse_args(argv)
    values = {**dotenv_values(BACKEND / '.env'), **os.environ}
    roles = {r.strip() for r in values.get('PATHWAYS_CONTENT_REVIEW_ROLES','').split(',') if r.strip()}
    if not roles: parser.error('PATHWAYS_CONTENT_REVIEW_ROLES is empty; content administration is disabled')
    if args.action in {'review','approve','revoke'} and not args.confirm: parser.error('Write actions require --confirm')
    engine = None
    try:
        engine = create_engine(get_settings().database_url, hide_parameters=True)
        with Session(engine) as session, session.begin():
            authorize(session,roles)
            if args.action == 'inspect':
                print(json.dumps(snapshot(session,destination(session,args.slug)),indent=2))
            elif args.action in {'validate','review'}:
                if not args.evidence_file: raise ReviewError('--evidence-file is required')
                with open(args.evidence_file,encoding='utf-8') as f: payload = json.load(f)
                if not isinstance(payload,dict): raise ReviewError('Evidence file must be an object')
                if args.action == 'validate':
                    validate_review(snapshot(session,destination(session,args.slug)),payload.get('evidence'),payload.get('notes'))
                    print('Content validation passed. No publication, entrance or route status changed.')
                else:
                    review = record_review(session,args.slug,payload.get('evidence'),payload.get('notes'),roles)
                    message = f'Review recorded: {review.id}. Destination publication unchanged.'
            elif args.action == 'approve':
                if not args.review_id or not args.reason: raise ReviewError('--review-id and --reason are required')
                approve_destination(session,args.slug,args.review_id,args.reason,roles)
                message = 'Content publication approved. Entrance and route statuses unchanged.'
            else:
                if not args.reason: raise ReviewError('--reason is required')
                revoke_destination(session,args.slug,args.reason,roles)
                message = 'Content publication revoked. Historical reviews and field locks retained.'
        if args.action in {'review','approve','revoke'}: print(message)
        return 0
    except (ReviewError,AuthorizationError,ValueError,OSError) as exc:
        # These are local validation errors, never DB exceptions/credentials.
        print(f'Content action rejected: {exc}')
        return 1
    except SQLAlchemyError:
        print('Content action failed; transaction rolled back. Check database connectivity and permissions.')
        return 1
    finally:
        if engine is not None: engine.dispose()

if __name__ == '__main__':
    raise SystemExit(main())

