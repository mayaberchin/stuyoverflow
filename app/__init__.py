import os
import csv
import uuid

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from functools import wraps
# https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/file
import data

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

oauth = OAuth(app)

google = oauth.register(
    'google',
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile',
        'code_challenge_method': 'S256',
                   },

    server_metadata_url= 'https://accounts.google.com/.well-known/openid-configuration'
)



data.create_tables()

ALLOWED_UPLOADS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "doc", "docx"}

WHITELIST = ['tm@stuycs.org', 'mayaberchin@gmail.com', 'MeganKwok168@gmail.com']

POST_PAGE_INFO = {
    "announcements": {
        "page_title": "Announcements",
        "page_description": "Teacher posts, assignments, and important class updates.",
        "selected_post_type": "announcement",
        "new_post_label": "New Announcement",
    },
    "questions": {
        "page_title": "Questions",
        "page_description": "Ask longer questions and provide context for help.",
        "selected_post_type": "question",
        "new_post_label": "New Question",
    },
    "chat": {
        "page_title": "Chat",
        "page_description": "CHat!!!!",
        "selected_post_type": "chat",
        "new_post_label": "New Chat",
    },
    "notes_resources": {
        "page_title": "Notes / Resources",
        "page_description": "Share notes, reminders, links, and useful resources.",
        "selected_post_type": "note",
        "new_post_label": "New Note",
    },
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('login-new.html')

@app.route('/login')
def login():
    redirect_uri = url_for('authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorized')
def authorized():
    try:
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()
        session['user'] = user_info
        email = session['user']['email']
        if not data.user_exists(email):
            return register_user()
        return redirect(url_for('home'))
    except Exception as e:
        #return 'Authorization error: ' + str(e)
        return 'Authorization error. Please try again. <a href="/logout">Login with stuy.edu</a>'

def register_user():
    email = session['user']['email']
    if email[-9:] == '@stuy.edu' or email in WHITELIST:
        email = session['user']['email']
        name = session['user']['name']
        data.add_user(email, name)
        return redirect(url_for('home'))
    session.pop('user', None)
    return 'You are not signed in with a stuy.edu account, nor is your email on our whitelist. <a href="/">Login</a>'

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

#main
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    # TEMP
    display_skills = True
    if display_skills:
        return redirect(url_for('skills'))
    email = session['user']['email']
    # get homepage posts
    homepage_post_ids = data.get_homepage_posts(email, 20)
    homepage_posts = []
    for post_id in homepage_post_ids["unread"]:
        post_data = data.get_post_data(post_id)
        homepage_posts.append(post_data)
    homepage_posts.reverse()
    # get unresolved posts
    unresolved_post_ids = data.get_all_unresolved()
    unresolved_posts = []
    for post_id in unresolved_post_ids:
        post_data = data.get_post_data(post_id)
        unresolved_posts.append(post_data)
    unresolved_posts.reverse()
    class_ids = data.get_user_classes(email)
    classes = []
    instructors_posts = []
    for class_id in class_ids:
        # get course data
        class_data = data.get_class_data(class_id)
        classes.append(class_data)
        print("1")
        teacher_post_data = data.get_teacher_posts(class_id)
        print("2")
        instructors_posts.append(teacher_post_data)
        print("3")
    return render_template(
        "homepage.html",
        homepage_posts=homepage_posts,
        unresolved_posts=unresolved_posts,
        classes=classes,
        get_user_name=data.get_user_name,
        instructors_posts=instructors_posts
    )


# TEMP
@app.route('/skills', methods=['GET', 'POST'])
#login_required
def skills():
    # OLD IMPLEMENTATION (OBSOLETE)
    '''
    skills = ['common sense','reading comp','hw','timeliness','participation','comms','hardware','terminal','racket','prefix notation',
              'logic','conditionals','variables','functions','return types','recursion','loops','comments','turtles','patches','shapes','programs','interface','webpage']
    entries = [['overall',3.57,3.14,3.00,2.57,3.29,4.00,3.00,3.20,3.00,4.00,3.86,3.40,'-','-','-','-','-','-','-','-','-','-','-','-'],
              ['10-19-26m',4,3,4,3,4,4,'-','-',4,'-',4,4,'-','-','-','-','-','-','-','-','-','-','-','-'],
              ['10-12-26m',4,3,2,1,4,4,'-',4,4,'-',4,4,'-','-','-','-','-','-','-','-','-','-','-','-'],
              ['10-05-26m',4,2,1,0,3,4,'-',4,3,'-',4,4,'-','-','-','-','-','-','-','-','-','-','-','-'],
              ['09-28-26m',4,4,3,3,4,4,'-',3,3,'-',4,3,'-','-','-','-','-','-','-','-','-','-','-','-'],
              ['09-21-26m',3,4,4,3,4,4,4,3,2,4,4,2,'-','-','-','-','-','-','-','-','-','-','-','-','-'],
              ['09-14-26m',3,3,3,4,2,4,4,2,2,4,4,'-','-','-','-','-','-','-','-','-','-','-','-','-'],
              ['09-07-26m',3,3,4,4,2,4,1,'-','-','-',3,'-','-','-','-','-','-','-','-','-','-','-','-','-']]
    email = session['user']['email']
    is_stuy = email[-8:] == 'stuy.edu'
    is_whitelisted = email in WHITELIST
    return render_template('skills.html', name=session['user']['name'], email=email, is_stuy=str(is_stuy), is_whitelisted=str(is_whitelisted), skills=skills, entries=entries)
    #return render_template('skills.html', name='Maya', email='mayaberchin@gmail.com', is_stuy='False', is_whitelisted='True',  skills=skills, entries=entries)
    '''
    # CURRENT TEMPORARY IMPLEMENTATION--SHOWCASE BAREBONES CSV
    content=''
    with open('./static/skills.csv', 'r', encoding='UTF-8') as f:
        content = f.readlines()
    return render_template('skills.html', content=content)

@app.route('/download_skills', methods=['GET', 'POST'])
@login_required
def download_skills():
    # CURRENT TEMPORARY IMPLEMENTATION--SHOWCASE BAREBONES CSV
    return send_file('./static/skills.csv', as_attachment=True)


# ------------------ POST PAGES ------------------
@login_required
def render_post_page(page):
    page_info = POST_PAGE_INFO[page]
    can_post = page != 'announcements' or data.is_stuy_teacher(session['user']['email'])
    return render_template(
        'post_page.html',
        page_title=page_info['page_title'],
        page_description=page_info['page_description'],
        selected_post_type=page_info['selected_post_type'],
        new_post_label=page_info['new_post_label'],
        can_post=can_post,
        current_user_email=session['user']['email']
    )

@app.route("/announcements")
@login_required
def announcements():
    return render_post_page("announcements")



@app.route("/pinned")
@login_required
def pinned():
    return render_template("pinned.html")
    #return render_post_page("pinned")


@app.route("/questions")
@login_required
def questions():
    return render_post_page("questions")


@app.route("/chat")
@login_required
def chat():
    return render_post_page("chat")


@app.route("/notes_resources")
@login_required
def notes_rsrc():
    return render_post_page("notes_resources")


@app.route("/account")
@login_required
def account():
    return render_template("account.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

# ------------------ REACT POST API ROUTES ------------------

@app.route("/api/classes")
def api_classes():
    email = session['user']['email']
    classes = []
    for class_id in data.get_user_classes(email):
        classes.append({
            "class_id": class_id,
            "name": data.get_class_name(class_id),
            "is_teacher": data.is_class_teacher(class_id, email),
        })

    return jsonify({"classes": classes})

# loads posts
@app.route("/api/posts")
@login_required
def api_posts():
    email = session['user']['email']
    category = request.args.get("category", "")
    all_posts = data.get_all_posts()
    all_posts = data.sort_by_ctime(all_posts) # newest posts first
    posts = []

    for post_id in all_posts:
        post = data.get_post_data(post_id)
        post = add_display_author(post)

        if post["parent_id"] == "" and (category == "" or post["category"] == category) and ((data.is_dojo(email) and post["show_dojo"] == "yes") or post["class_id"] in data.get_user_classes(email)):
            posts.append(post)

    return jsonify({"posts": posts})

# ceates and saves a new post
@app.route("/api/posts", methods=["POST"])
@login_required
def api_create_post():
    email = session['user']['email']
    
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        post = request.form
    else:
        post = request.get_json() or {}

    title = post.get("title", "").strip()
    class_id = post.get("class_id", "").strip()
    body = post.get("body", "").strip()
    category = post.get("category", "").strip()
    show_dojo = "yes" if post.get("shareWithDojo") else "no"
    is_anonymous = "yes" if post.get("isAnonymous") else "no"
    attachment = ""

    # if there is a file attached, save it and store link in attachments
    file = request.files.get("attachment")
    if file is not None and file.filename != "":
        if "." not in file.filename:
            return jsonify({"error": "That file type is not supported"}), 400
        extension = file.filename.rsplit(".", 1)[1].lower()
        if extension not in ALLOWED_UPLOADS:
            return jsonify({"error": "That file type is not supported"}), 400

        # secure_filename cleans up weird filenames before saving
        clean_name = secure_filename(file.filename)
        # uuid keeps two files with the same name from replacing each other
        file_name = str(uuid.uuid4()) + "_" + clean_name
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file_name))
        attachment = url_for("static", filename="uploads/" + file_name)

    if category == "announcement" and not data.is_class_teacher(class_id, email):
        return jsonify({"error": "Only teachers can post announcements"}), 403

    post_id = data.create_post( # returns new post_id
        session['user']['email'],
        class_id,
        title,
        body,
        category,
        show_dojo,
        attachment,
        is_anonymous
    )
    saved_post = data.get_post_data(post_id)
    saved_post = add_display_author(saved_post)
    return jsonify({"post": saved_post})

@app.route("/api/posts/<post_id>/followups")
@login_required
def api_followups(post_id):
    email = session['user']['email']
    data.mark_read(email, post_id)
    followup_ids = data.get_post_followups(post_id)
    if type(followup_ids) == list:
        followup_ids = {
            "answers": [],
            "teacher_responses": [],
            "other": followup_ids,
        }
    followups = {
        "answers": [],
        "teacher_responses": [],
        "other": [],
    }

    for group in followups:
        for followup_id in followup_ids[group]:
            followup = data.get_post_data(followup_id)
            followup = add_display_author(followup)
            followups[group].append(followup)

    return jsonify({"followups": followups})

@app.route("/api/posts/<post_id>/followups", methods=["POST"])
@login_required
def api_create_followup(post_id):
    post = request.get_json() or {}
    body = post.get("body", "").strip()
    is_anonymous = "yes" if post.get("isAnonymous") else "no"

    if body == "":
        return jsonify({"error": "Missing followup body"}), 400

    followup_id = data.create_followup(session['user']['email'], post_id, body, is_anonymous)
    followup = data.get_post_data(followup_id)
    followup = add_display_author(followup)
    return jsonify({"followup": followup})

@app.route("/api/posts/<post_id>/upvote", methods=["POST"])
@login_required
def api_toggle_upvote(post_id):
    email = session['user']['email']
    try:
        post = data.get_post_data(post_id)
    except IndexError:
        return jsonify({"error": "Post not found"}), 404

    if email in post["upvoters"]:
        data.remove_post_upvoter(post_id, email)
    else:
        data.add_post_upvoter(post_id, email)

    post = data.get_post_data(post_id)
    post = add_display_author(post)
    return jsonify({"post": post})

def add_display_author(post):
    email = session['user']['email']
    if post['is_anonymous'] == 'yes':
        post['display_author'] = 'Anonymous'
    else:
        post['display_author'] = data.get_user_name(post['author_email'])
    post['has_upvoted'] = 'user' in session and email in post['upvoters']
    return post

#join/create class:
@app.route("/join_class", methods=["POST"])
@login_required
def join_a_class():
    email = session['user']['email']
    code = request.form.get("class_code")
    if code not in data.get_all_classes():
        flash("Class not found. Ask your teacher for the code.")
        return redirect(url_for("home"))
    data.add_class_member(code, email)
    return redirect(url_for("home"))

@app.route("/create_class_",methods=["POST"])
@login_required
def create_a_class():
    email = session['user']['email']
    class_name = request.form.get("class_name")
    class_created = data.create_class(email, class_name)
    return redirect(url_for("home"))


if __name__ == "__main__":
  #app.debug = True
  app.run()
