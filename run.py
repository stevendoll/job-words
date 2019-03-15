from app import app, db
from app.models import User, PhraseGroup, Phrase, UserPhrase, Finding

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'PhraseGroup': PhraseGroup, 'Phrase': Phrase, 'UserPhrase': UserPhrase, 'Finding': Finding}

