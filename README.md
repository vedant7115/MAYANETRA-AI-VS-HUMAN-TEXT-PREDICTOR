🌐 MAYANETRA – AI vs Human Text Predictor

MAYANETRA is a web application that detects whether a given text is AI-generated or Human-written.
Built with Flask (Python) for the backend and powered by a Logistic Regression model + TF-IDF vectorizer.

🚀 Features

✅ Detects if text is AI or Human written
✅ Simple Flask API with /predict endpoint
✅ User-friendly web interface (HTML/CSS/JS)
✅ Easy to deploy on GitHub + Render/Heroku

🛠️ Tech Stack

Python 3.10+

Flask – Web framework

Scikit-learn – Model training

Joblib/Pickle – Model serialization

HTML + CSS – Frontend UI

📂 Project Structure
MAYANETRA/
│── app.py                # Flask backend  
│── logistic_model.pkl     # Trained Logistic Regression model  
│── tfidf_vectorizer.pkl   # TF-IDF vectorizer  
│── templates/  
│   └── index.html         # Frontend UI  
│── README.md              # Project documentation  

⚡ Installation & Usage
1️⃣ Clone the Repository
git clone https://github.com/vedant7115/MAYANETRA-AI-VS-HUMAN-TEXT-PREDICTOR.git
cd MAYANETRA-AI-VS-HUMAN-TEXT-PREDICTOR

2️⃣ Create Virtual Environment (Optional but Recommended)
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate   # On Mac/Linux

3️⃣ Install Requirements
pip install -r requirements.txt

4️⃣ Run the Flask App
python app.py


Now open http://127.0.0.1:5000/
 in your browser 🎉

📡 API Usage
Endpoint: /predict

Method: POST
Payload Example:

{
  "text": "This is a sample sentence written by a human."
}


Response Example:

{
  "input_text": "This is a sample sentence written by a human.",
  "prediction": "human"
}

🌍 Deployment

You can deploy this project easily on platforms like:

Render

Railway

Heroku

📜 License

This project is licensed under the MIT License – feel free to use & modify.

✨ Developed with ❤️ by Vedant Saubhri