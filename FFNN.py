from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_recall_curve, classification_report, confusion_matrix
from keras.models import Sequential
from keras.layers import Dense
import pandas as pd

# Load the dataset
df = pd.read_csv('simulation_results.csv')

#added one hot encoding for ID - IDS are strings 

from sklearn.preprocessing import OneHotEncoder
import joblib  
# Assign ID collumns
IDs = df[['ID']] 
# Assign ID collumns
encoder = OneHotEncoder()
# Fit and transform the 'ID' column
IDs_encoded = encoder.fit_transform(IDs)
# Convert to dense format and then DataFrame
df_encoded = pd.DataFrame(IDs_encoded.toarray(), columns=encoder.get_feature_names_out(['ID']))
# Merge back with the original dataframe after dropping 'ID'
df_encoded = pd.concat([df.drop('ID', axis=1).reset_index(drop=True), df_encoded.reset_index(drop=True)], axis=1)
#test
joblib.dump(encoder, 'encoder.save')

#X = df_encoded.drop(['Anomaly','Speed','Time', 'No. Veh'], axis=1)
X = df_encoded.drop(['Anomaly','Time'], axis=1)
#print(X.head())
print("Shape of the encoded DataFrame:", X.shape)
print(X.head())
#X = df_encoded.drop(['Anomaly', 'Speed', 'No. Veh', 'Time'], axis=1)
y = df_encoded['Anomaly']
ids = df['ID']  # used for checking which roads predicted
times = df['Time']  

# Split the data
X_train, X_test, y_train, y_test, ids_train, ids_test, times_train, times_test = train_test_split(
    X, y, ids, times, test_size=0.2, random_state=42
)
import joblib #for saving scaler
# scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
joblib.dump(scaler, 'scaler.save') #save scaler for real time model

# structure
model = Sequential([
    Dense(64, activation='relu', input_shape=(X_train_scaled.shape[1],)), 
    Dense(32, activation='relu'), 
    Dense(1, activation='sigmoid') 
])
# adam optimizer and binary cross-entropy loss function
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train the model
history = model.fit(X_train_scaled, y_train, epochs=100, batch_size=32, validation_split=0.2)
# Evaluate the model
test_loss, test_acc = model.evaluate(X_test_scaled, y_test)

# Predict on the test set
from sklearn.metrics import f1_score
# Generate prediction probabilities
predictions_prob = model.predict(X_test_scaled).ravel()
# Calculate precision, recall, and thresholds
precisions, recalls, thresholds = precision_recall_curve(y_test, predictions_prob)
# Initialize best score tracking variables
best_f1 = 0
best_threshold = 0
# Iterate through thresholds to find the best based on F1 score
for i in range(len(thresholds)):
    current_f1 = f1_score(y_test, predictions_prob > thresholds[i])
    if current_f1 > best_f1:
        best_f1 = current_f1
        best_threshold = thresholds[i]
print(f"Best F1 Score: {best_f1}")
print(f"Best Threshold: {best_threshold}")

# Save the threshold to a file
threshold_filename = 'best_threshold.txt'
with open(threshold_filename, 'w') as file:
    file.write(str(best_threshold))
    
# Use the best threshold to classify instances
predicted_labels = (predictions_prob > best_threshold).astype(int)
chosen_threshold = best_threshold
# final predictions using the chosen threshold
predicted_labels = (predictions_prob > chosen_threshold).astype(int)

# Code for checking which anomalies were predicted correctly
# Create a dataFrame with test 'ID' and 'Time'
test_ids_times = pd.DataFrame({
    'ID': ids_test.reset_index(drop=True),
    'Time': times_test.reset_index(drop=True),
    'True Anomaly': y_test.reset_index(drop=True),
    'Predicted Anomaly': predicted_labels
})

# Iterate over the DataFrame and print the 'ID' and 'Time' for correctly predicted anomalies
for index, row in test_ids_times.iterrows():
    if row['Predicted Anomaly'] == 1 and row['True Anomaly'] == 1:
        print(f"True Positive: Anomaly correctly predicted for ID: {row['ID']} at Time: {row['Time']}")
    elif row['Predicted Anomaly'] == 1 and row['True Anomaly'] == 0:
        # False Positive
        print(f"False Positive: Anomaly incorrectly predicted for ID: {row['ID']} at Time: {row['Time']}")
    elif row['Predicted Anomaly'] == 0 and row['True Anomaly'] == 1:
        # False Negative
        print(f"False Negative: Anomaly not predicted (but true) for ID: {row['ID']} at Time: {row['Time']}")

# Generate and print the classification report
report = classification_report(y_test, predicted_labels, target_names=['Non-Anomaly', 'Anomaly'], zero_division=0)
print(f"Classification report with threshold {chosen_threshold}:\n{report}")
print(confusion_matrix(y_test, predicted_labels))
#save model for real time analysis
model.save('my_model.keras')
 
 #Create image of models features
from tensorflow.keras.utils import plot_model

plot_model(model, to_file='model.png', show_shapes=True, show_layer_names=True)
