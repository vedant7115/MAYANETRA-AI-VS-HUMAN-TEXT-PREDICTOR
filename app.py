import os
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np

# -----------------------------
# App & Config
# -----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'   # creates users.db in project root
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # redirect here if not logged in

# If an AJAX/JSON request is unauthorized, return JSON instead of HTML redirect
@login_manager.unauthorized_handler
def unauthorized():
    wants_json = (
        request.is_json
        or request.headers.get("Content-Type","").startswith("application/json")
        or request.headers.get("Accept","").startswith("application/json")
    )
    if wants_json:
        return jsonify({"error": "Unauthorized. Please log in."}), 401
    return redirect(url_for("login"))

# -----------------------------
# DB Models
# -----------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# (Optional) Future: store predictions per user
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(30), nullable=False)     # "AI" / "Human"
    probability = db.Column(db.Float, nullable=True)     # 0..1 probability of AI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------
# Load ML artifacts (robust to /models or root)
# -----------------------------
def load_artifact(*names):
    for name in names:
        if os.path.exists(name):
            return joblib.load(name)
        alt = os.path.join("models", name)
        if os.path.exists(alt):
            return joblib.load(alt)
    raise FileNotFoundError(f"Could not find any of: {', '.join(names)} in project root or /models")

try:
    model = load_artifact("logistic_regression_model.pkl", "model.pkl")
    vectorizer = load_artifact("tfidf_vectorizer.pkl", "vectorizer.pkl")
    print("Artifacts loaded.")
except Exception as e:
    print("ERROR loading model/vectorizer:", e)
    model = None
    vectorizer = None

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
@login_required
def home():
    # Your animated UI lives in templates/index.html
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    if model is None or vectorizer is None:
        return jsonify({"error": "Model not loaded on server."}), 500

    try:
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"error": "No text provided"}), 400

        X = vectorizer.transform([text])

        # Predict label
        raw_pred = model.predict(X)[0]

        # Predict probabilities if available
        prob_ai = None
        try:
            proba = model.predict_proba(X)[0]  # array of probabilities per class
            # Map to "AI" class index if possible
            if hasattr(model, "classes_"):
                classes = list(model.classes_)
                # Try to find 'AI' class or fallback to best guess
                ai_idx = None
                for i, c in enumerate(classes):
                    if isinstance(c, str) and c.lower().startswith("ai"):
                        ai_idx = i
                        break
                    if c == 1:  # common encoding: 1=AI
                        ai_idx = i
                        break
                if ai_idx is None:
                    ai_idx = int(np.argmax(proba))
            else:
                ai_idx = int(np.argmax(proba))
            prob_ai = float(proba[ai_idx])  # 0..1 probability that text is AI
        except Exception:
            pass

        # Normalize label -> friendly text
        def is_ai_label(lbl):
            if isinstance(lbl, str):
                return lbl.strip().lower().startswith("ai")
            if isinstance(lbl, (int, np.integer)):
                return int(lbl) == 1  # many datasets use 1=AI, 0=Human
            return False

        is_ai = is_ai_label(raw_pred)
        label_out = "🤖 AI Generated" if is_ai else "🧑 Human Written"

        # Save to DB history (optional)
        try:
            p = Prediction(
                user_id=current_user.id,
                text=text,
                label="AI" if is_ai else "Human",
                probability=prob_ai
            )
            db.session.add(p)
            db.session.commit()
        except Exception:
            db.session.rollback()

        resp = {"prediction": label_out}
        if prob_ai is not None:
            resp["probability"] = prob_ai  # 0..1
        return jsonify(resp)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- Auth ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email    = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("signup"))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("signup"))

        hashed = generate_password_hash(password, method="pbkdf2:sha256", salt_length=12)
        user = User(username=username, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for("home"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# Convenience: quick check of current user
@app.route("/me")
@login_required
def me():
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    })

# -----------------------------
# Bootstrap DB & run
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
