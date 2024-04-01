from google.cloud import pubsub_v1
from keras.models import load_model
import joblib
import numpy as np
import json
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load resources
model_path = 'my_model.keras'
scaler_path = 'scaler.save'
threshold_path = 'best_threshold.txt'
encoder_path = 'encoder.save'

model = load_model(model_path)
scaler = joblib.load(scaler_path)
encoder = joblib.load(encoder_path)
best_threshold = float(open(threshold_path, 'r').read())

detector_to_streets = {
        'e1_0': 'Main Street','e1_1': 'Main Street', 'e1_2': 'Park Road', 'e1_3': 'Park Road', 'e1_4': 'Prosperous Road', 'e1_5': 'Prosperous Road', 'e1_6': 'College Wood Park',
        'e1_7': 'College Wood Park', 'e1_8': 'Kilcock Road', 'e1_9': 'Kilcock Road', 'e1_10': 'Main Street', 'e1_11': 'Main Street', 'e1_12': 'Ring Road', 'e1_13': 'Ring Road',
        'e1_14': 'Ring Road', 'e1_15': 'Ring Road', 'e1_16': 'Millicent Road', 'e1_17': 'Millicent Road', 'e1_18': 'Millicent Road',
        'e1_19': 'Millicent Road', 'e1_20': 'Prosperous Road', 'e1_21': 'Prosperous Road', 'e1_22': 'Dublin Road', 'e1_23': 'Dublin Road',
        'e1_24': 'Dublin Road', 'e1_25': 'Dublin Road', 'e1_26': 'Prosperous Road', 'e1_27': 'Ring Road', 'e1_28': 'Prosperous Road', 'e1_29': 'Ring Road','e1_30': 'Naas Road',
        'e1_31': 'Naas Road','e1_32': 'Main Stree','e1_33': 'Main Street','e1_34': 'Main Street','e1_35': 'Main Street','e1_36': 'College Wood Park',
        'e1_37': 'College Wood Park', 'e1_38': 'Kilcock Road','e1_39': 'Kilcock Road'
    }
def get_street(detector_id):
    return detector_to_streets.get(detector_id)

import smtplib
def sendMail(subject,message):
    # Usser information 
    email = "macconor1234@gmail.com" 
    receiver_email = "conor.mccarthy76@mail.dcu.ie"
    text = f"Subject: {subject}\n\n{message}"
    # SMTP server setup
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    app_password = "zcosrrtudvhauquu" 
    server.login(email, app_password)
    # Send email
    server.sendmail(email, receiver_email, text)
    # Confirmation
    print(f"Email has been sent to {receiver_email}")
    # Quit the server
    server.quit()

def preprocess_data(detector_id, speed, noVeh, time_since_detection, scaler, encoder):
    # Convert detector_id to format expected by the encoder and preprocess the data
    detector_id_encoded = encoder.transform([[detector_id]]).toarray()
    features = np.hstack([[[speed, noVeh, time_since_detection]], detector_id_encoded])
    features_scaled = scaler.transform(features)
    #print(f"Encoded features for detector {detector_id}: {features}")
    return features_scaled

def predict_anomaly(features, model, best_threshold):
    prediction = model.predict(features).flatten()
    return int(prediction[0] > best_threshold)

def callback(message):
    #print(f"Received message:")
    data = json.loads(message.data.decode("utf-8"))
    detector_id = data["detector_id"]
    speed = data["Speed"]
    noVeh = data["No. Veh"]
    time_since_detection = data["time_since_detection"]
    current_time = data["current_time"]
    features = preprocess_data(detector_id, speed, noVeh, time_since_detection, scaler, encoder)
    is_anomaly = predict_anomaly(features, model, best_threshold)
    
    #print(f"Anomaly detected: {is_anomaly} for detector ID: {detector_id} with time since detection: {time_since_detection}")
    if is_anomaly:
        street = get_street(detector_id)
        s = f'Anomaly detected on {street} at detector {detector_id} at time {current_time}'
        print(s)
        sendMail("Alert Crash in Clane!",s)
    message.ack()

def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path('tidy-groove-415214', 'sumoFYP-sub')

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When timeout is unspecified or None, the result method waits indefinitely.
            streaming_pull_future.result()
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.

if __name__ == "__main__":
    main()

