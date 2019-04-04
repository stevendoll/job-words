from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import re
import json
from app import app, db
from app.forms import LoginForm, SignupForm, DocumentForm
from app.models import User, Role, Phrase, DocumentPhrase, Finding, Document, UserPhrase

# check user authorization
def roles_accepted(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # user has no roles or no roles that match
            if not current_user.get_roles() or not (
                list(set(roles) & set(current_user.get_roles()))
            ):
                flash(
                    "Not authorized. You do not have a role that allows access to this feature.",
                    "warning",
                )
                return redirect(url_for("index"))
            return f(*args, **kwargs)

        return wrapped

    return wrapper


@app.route("/initialize")
def setup():

    admin_users = app.config["ADMINISTRATORS"].split(",")

    # check if roles empty
    if Role.query.first() == None:

        # add roles
        r1 = Role(role_id="Admin", description="Administrator role.")
        db.session.add_all([r1])
        db.session.commit()

        # add admins
        for username in admin_users:

            user = User.get_by_username(username)
            if user:
                user.add_role("Admin")
                app.logger.info("Granted Admin role: %s", user.username)
            else:
                app.logger.warning("Unable to grant Admin role: %s", username)

        flash("Dashboard initialized", "success")
    else:
        flash("Already initialized", "error")
    return redirect(url_for("index"))


@app.route("/")
@app.route("/index")
def index():
    phrase = Phrase.get_last()

    phrases = Phrase.get_all()

    my_phrases = None

    return render_template(
        "phrase-list.html",
        title="Search Phrases",
        phrases=phrases,
        my_phrases=my_phrases,
        phrase=phrase,
    )


@app.route("/charts")
def charts():
    return render_template("charts.html", title="Home")


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/test")
def test():
    return render_template("test.html", title="About")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if (
            user is None
            or user.password_hash is None
            or not user.check_password(form.password.data)
        ):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        flash("Welcome back " + user.username)
        return redirect(url_for("index"))
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash("Goodbye")
    return redirect(url_for("index"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("signup.html", title="Sign up", form=form)


@app.route("/users")
@login_required
def user_list():

    users = User.get_all()

    return render_template("user-list.html", title="Users", users=users)


@app.route("/phrases")
def phrase_list():

    term = request.args.get("term", "")

    regex = r"[^\w\.\s\-\,]"
    term = re.sub(regex, "", term.lower().strip())

    phrase = Phrase.get_last()

    if term and "," in term:

        if current_user.is_authenticated:
            Comparison.add_comparison(term=term, user=current_user)
        else:
            Comparison.add_comparison(term=term)

    elif term:
        if current_user.is_anonymous:
            phrase = Phrase.lookup(term)
        else:
            phrase = Phrase.lookup(term, user=current_user)

        if phrase == None:
            flash("Something went wrong")
        # elif phrase.search_count == 1:
        #     flash('New search phrase! ')
        # else:
        #     flash('Searched ' + str(phrase.search_count) + ' times!')

    phrases = Phrase.get_all()

    if current_user.is_anonymous:
        my_phrases = None
    else:
        my_phrases = User.get_by_username(current_user.username).phrases

    return render_template(
        "phrase-list.html",
        title="Search Phrases",
        phrases=phrases,
        my_phrases=my_phrases,
        phrase=phrase,
    )


@app.route("/phrases/latest")
def phrase_latest():

    phrases = Phrase.get_all()

    return render_template(
        "phrase-latest.html", title="Latest Phrases", phrases=phrases
    )


@app.route("/phrases/<phrase_slug>")
def phrase_view(phrase_slug):

    phrase = Phrase.get_phrase(phrase_slug)

    return render_template("phrase.html", title="phrase.phrase_text", phrase=phrase)


@app.route("/users/<username>/phrases")
@login_required
def user_phrase_list(username):

    phrases = User.get_by_username(username).phrases

    return render_template(
        "user-phrase-list.html", title="User Phrases", phrases=phrases
    )


@app.route("/documents", methods=["GET", "POST"])
def document_list():

    form = DocumentForm()
    if form.validate_on_submit():

        if current_user.is_authenticated:
            Document.add_document(
                title=form.title.data, body=form.body.data, user=current_user
            )
        else:
            flash("Please register or login to analyze documents.")

    documents = Document.get_all()

    return render_template(
        "document-list.html", title="All documents", documents=documents
    )


@app.route("/documents/new")
@login_required
def create_document():
    form = DocumentForm()
    return render_template("document-form.html", title="Create document", form=form)


@app.route("/users/<username>/documents")
@login_required
def user_document_list(username):

    documents = User.get_by_username(username).documents

    return render_template(
        "user-document-list.html", title="User Documents", documents=documents
    )


@app.route("/documents/<slug>")
@login_required
def document(slug):

    document = Document.get_by_slug(slug=slug)

    phrases = Document.get_phrases(document)

    return render_template(
        "user-document.html",
        title="Document Analysis",
        phrases=phrases,
        document=document,
    )


@app.route("/api/phrases")
def phrase_list_api():

    # entire market of phrases
    phrases = Phrase.get_all()

    result = {}
    phrase_list = []

    for phrase in phrases:
        phrase_list.append(phrase.serialize())

    result["phrases"] = phrase_list
    result["phraseCount"] = len(phrase_list)

    return json.dumps(result)


@app.route("/api/documents/<slug>/phrases")
def document_phrase_list_api(slug):

    document = Document.get_by_slug(slug=slug)

    phrases = Document.get_phrases(document)

    result = {}
    phrase_list = []

    for phrase in phrases:
        phrase_list.append(phrase.serialize())

    result["phrases"] = phrase_list
    result["phraseCount"] = len(phrase_list)

    return json.dumps(result)
