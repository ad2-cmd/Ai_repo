from sqlalchemy.orm import Session


def upsert_record(session: Session, model, data: dict):
    instance = session.query(model).filter_by(id=data.get('id')).one_or_none()
    if not instance:
        session.add(model(data))
        return

    for key, value in data.items():
        setattr(instance, key, value)
