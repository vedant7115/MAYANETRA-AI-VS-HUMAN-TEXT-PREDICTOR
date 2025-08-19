from flask import Flask, render_template, request
import joblib

# Load trained model and vectorizer
model = joblib.load("logistic_regression_model.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    text = request.form.get("text", "")

    if not text.strip():
        return render_template("index.html", error="⚠️ Please enter some text.")

    # Transform text and predict
    text_vec = vectorizer.transform([text])
    prediction = model.predict(text_vec)[0]

    # Debug in terminal
    print("DEBUG prediction:", prediction)

    # Map prediction labels
    labels = {
        "human": "📝 Human-written",
        "ai": "🤖 AI-generated"
    }
    result = labels.get(str(prediction).lower(), str(prediction))

    return render_template("index.html", text=text, prediction=result)

if __name__ == "__main__":
    app.run(debug=True)
