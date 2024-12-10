import csv
from sklearn import svm
from sklearn.linear_model import Perceptron
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier

# Initialize models
models = [
    Perceptron(),
    svm.SVC(),
    KNeighborsClassifier(n_neighbors=1),
    GaussianNB()
]

# Read data in from file
with open("banknotes.csv") as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header

    data = []
    for row in reader:
        data.append({
            "evidence": [float(cell) for cell in row[:4]],
            "label": "Authentic" if row[4] == "0" else "Counterfeit"
        })

# Separate data into training and testing groups
evidence = [row["evidence"] for row in data]
labels = [row["label"] for row in data]

X_training, X_testing, y_training, y_testing = train_test_split(
    evidence, labels, test_size=0.4
)

# Store model results
model_results = []

for model in models:
    # Fit model
    model.fit(X_training, y_training)
    # Make predictions on the testing set
    predictions = model.predict(X_testing)
    # Compute performance metrics
    correct = (y_testing == predictions).sum()
    incorrect = (y_testing != predictions).sum()
    total = len(predictions)
    accuracy = 100 * correct / total
    model_results.append((type(model).__name__, correct, incorrect, accuracy))

# Sort models by accuracy
model_results.sort(key=lambda x: x[3], reverse=True)

# Print results in sorted order
for model_name, correct, incorrect, accuracy in model_results:
    print(f"Results for model {model_name}")
    print(f"Correct: {correct}")
    print(f"Incorrect: {incorrect}")
    print(f"Accuracy: {accuracy:.2f}%")

