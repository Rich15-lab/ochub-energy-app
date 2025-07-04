import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load dataset
df = pd.read_csv('/Users/g-rich/Desktop/ochub-ai-energy-platform/backend/motion_dataset.csv')

# Features and label
X = df[['intensity', 'duration']]
y = df['activity']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Save model
joblib.dump(clf, 'backend/activity_classifier_model_mac.pkl')

print("✅ Model trained and saved successfully.")
