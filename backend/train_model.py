from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import joblib

DATASET = [
    ("multi vehicle pileup fire explosion highway", "CRITICAL"),
    ("car trapped under truck driver fatal", "CRITICAL"),
    ("vehicle overturned passengers trapped bleeding", "CRITICAL"),
    ("bus caught fire passengers injured trapped", "CRITICAL"),
    ("two car collision injuries reported intersection", "HIGH"),
    ("motorcycle hit by bus rider bleeding", "HIGH"),
    ("truck overturned driver injured highway", "HIGH"),
    ("pedestrian struck by car injured", "HIGH"),
    ("car stalled blocking lane no injuries", "MEDIUM"),
    ("broken glass on road minor hazard", "MEDIUM"),
    ("oil spill on road surface hazard", "MEDIUM"),
    ("traffic signal damaged at junction", "MEDIUM"),
    ("minor fender bender no injuries parking lot", "LOW"),
    ("scratch on parked vehicle no damage", "LOW"),
    ("broken tail light vehicle parked roadside", "LOW"),
]

X, y = [], []
for text, label in DATASET * 6:
    X.append(text); y.append(label)

model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2)),
    LogisticRegression(max_iter=1000)
)
model.fit(X, y)
joblib.dump(model, "severity_model.joblib")
print(" Model saved: severity_model.joblib")