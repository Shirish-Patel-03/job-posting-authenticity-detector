# src/evaluate_model.py — records model performance for comparison across versions.
# Run after any retrain to check whether a change actually helped.

import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

from preprocessing import load_and_clean, combine_text_fields, build_training_features, build_request_features

MODEL_DIR = Path("../models")

# --- Part 1: formal test-set metrics (same split logic as training) ---
df = load_and_clean("../data/emscad_core.csv")
df = combine_text_fields(df)
X = build_training_features(df)
y = df["fraudulent"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

pipeline = joblib.load(MODEL_DIR / "fraud_pipeline.joblib")
y_pred = pipeline.predict(X_test)

print("=" * 60)
print("FORMAL TEST SET METRICS")
print("=" * 60)
print(classification_report(y_test, y_pred, target_names=["genuine", "fraudulent"]))
print("Confusion matrix (rows=actual, cols=predicted):")
print(confusion_matrix(y_test, y_pred))

# --- Part 2: hand-built sanity check set (modern, obvious examples) ---
# Structured fields set to "unknown" for all of these — this tests what a
# real user pasting text with no structured info would actually experience.
sanity_examples = [
    ("Earn $5000/week from home! No experience needed, just pay a $50 registration fee via Bitcoin to get started. Contact us on Telegram.", 1),
    ("We're hiring a Senior Software Engineer with 5+ years of Python experience. Competitive salary, full benefits, hybrid work model. Apply via our careers page.", 0),
    ("Earn $8,000 every week from your phone! No skills or experience required. Send a $100 activation fee in Bitcoin and start earning today!", 1),

("Work from home and make $3,000-$7,000 per day simply by liking videos. Limited spots available! Pay a refundable $25 verification fee to begin.", 1),

("Congratulations! You have been selected for a remote job paying $10,000/month. To receive your offer letter, send your passport and a $75 processing fee through Telegram.", 1),

("URGENT HIRING!!! Amazon is hiring 500 people to work from home. Earn $500/day with zero experience. WhatsApp us now and pay a small registration fee.", 1),

("Make $2,500 daily using our secret AI system! Guaranteed income with no experience. Only 20 seats left. Pay $49 in crypto to unlock your account.", 1),

("You have been shortlisted for an international work-from-home position. Please purchase a $200 gift card and send us the code to verify your identity.", 1),

("Earn money by receiving packages at home and forwarding them to our customers. Earn $1,000 per week. No interview required. Contact our Telegram recruiter.", 1),

("Remote data entry job — earn $6,000 per month with just 2 hours of work each day. Registration costs only $30. Payment accepted exclusively in cryptocurrency.", 1),

("We are urgently looking for 50 people to review products online. Earn $400 per review with guaranteed payment. No interview required. Message our recruiter on WhatsApp.", 1),

("Your profile has been selected for a high-paying remote position. Send your bank details and a copy of your ID to receive your salary advance immediately.", 1),

("We're hiring a Backend Software Engineer with 3+ years of experience in Python and Django. The role involves designing APIs, improving system reliability, and collaborating with frontend and infrastructure teams.", 0),

("We are looking for a Customer Support Specialist to join our remote team. Candidates should have strong written communication skills and experience working with customers. Full-time position with health benefits.", 0),

("We're hiring a Data Analyst with experience in SQL, Python, and Tableau. You will work with product and business teams to build dashboards and analyze customer behavior. Remote work available.", 0),

("Senior DevOps Engineer — 5+ years of experience with AWS, Docker, Kubernetes, and Terraform required. Responsibilities include maintaining production infrastructure and improving CI/CD pipelines. Competitive compensation and paid time off.", 0),

("Our company is seeking a Junior UX Designer to support research, wireframing, prototyping, and usability testing. Experience with Figma is preferred. This is a full-time hybrid position.", 0),

("We're looking for an experienced Marketing Manager to develop digital campaigns, analyze performance metrics, and manage external agencies. Bachelor's degree and 4+ years of marketing experience preferred.", 0),

("Hiring a Financial Accountant with experience in monthly close, reconciliations, and financial reporting. Proficiency with Excel and accounting software required. Position includes medical insurance and retirement benefits.", 0),

("We are seeking a Machine Learning Engineer to build and deploy production ML models. Experience with Python, PyTorch or TensorFlow, and cloud-based ML platforms is preferred. Apply through our official careers portal.", 0),

("Part-time Content Writer needed to create technical articles and product documentation. Strong English writing skills and familiarity with software development concepts required. Flexible working hours.", 0),

("We're hiring a Project Manager to coordinate software development projects across engineering, design, and product teams. Candidates should have experience with Agile methodologies and project management tools.", 0),
("fake this is a scam dont apply ",1),
]

print("\n" + "=" * 60)
print("SANITY CHECK SET (hand-written, modern examples)")
print("=" * 60)
correct = 0
for text, true_label in sanity_examples:
    row = build_request_features(text)  # all structured fields default to "unknown"
    pred = pipeline.predict(row)[0]
    proba = pipeline.predict_proba(row)[0][1]
    status = "✓" if pred == true_label else "✗"
    correct += (pred == true_label)
    print(f"{status} expected={true_label} predicted={pred} (score={proba:.2f}) | {text[:60]}...")

print(f"\nSanity check accuracy: {correct}/{len(sanity_examples)}")