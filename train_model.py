import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Load the dataset
df = pd.read_csv('motion_dataset.csv')

# Features and target
X = df[['intensity', 'duration']]
y = df['activity']

# Train the model
clf = DecisionTreeClassifier()
clf.fit(X, y)

# Save the model
joblib.dump(clf, 'activity_classifier_model_mac.pkl')

print("✅ Model retrained and saved successfully.")
