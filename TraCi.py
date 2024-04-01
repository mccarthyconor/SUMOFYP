import os
import traci
import csv
import random

# Set the SUMO_HOME environment variable
os.environ["SUMO_HOME"] = "/usr/local/opt/sumo/share/sumo/"

# Define the sumo command line command
#sumoCmd = ["sumo", "-c", "osm.sumocfg"]
sumoCmd = ["sumo-gui", "-c", "osm.sumocfg"]

# Start the simulation
traci.start(sumoCmd)

# Loop detectors
detector_ids = ['e1_0', 'e1_1', 'e1_2', 'e1_3', 'e1_4', 
'e1_5', 'e1_6', 'e1_7','e1_8', 'e1_9','e1_10','e1_11',
'e1_12', 'e1_13', 'e1_14', 'e1_15', 'e1_16', 'e1_17',
'e1_18', 'e1_19','e1_20','e1_21','e1_22','e1_23','e1_24',
'e1_25','e1_26','e1_27','e1_28','e1_29', 'e1_30','e1_31',
'e1_32','e1_33','e1_34','e1_35','e1_36','e1_37', 'e1_38','e1_39']
interval_count = 40  # Number of intervals for data collection
#interval_count = 864 #12 hour simulation
interval_length = 50  # Length of each interval in simulation steps
vehicle_spawn_times = {}

# Dictionary for storing collected data
data_per_inductor = {
    detector_id: {
        'speeds': {f'interval{i+1}': [] for i in range(interval_count)},
        'vehicle_counts': {f'interval{i+1}': 0 for i in range(interval_count)},
        'time_since': {f'interval{i+1}': 0 for i in range(interval_count)},
        'anomaly': {f'interval{i+1}': 0 for i in range(interval_count)},
        'anomaly_counter': {f'interval{i+1}': 0 for i in range(interval_count)}
    } for detector_id in detector_ids
}

anomalies_added = {}

# Function to add anomalies at random edges
def add_anomaly(current_time, step, spawn_probability=0.001):
    if random.random() < spawn_probability:
        vehicle_id = "veh{}_{}".format(current_time, step)
        if vehicle_id not in traci.vehicle.getIDList():
            eds = ['E11', '-E11', 'E6', '-E6', 'E9', '-E9', 'E3', '-E3', 'E4', '-E4', 'E2', '-E2', 'E13', '-E13', 'E14', '-E14', '-399342306',
                '868100855#1', '-68233356#0', '399342307#1', '97506034#2', '-97506034#2', '-E15', 'E15', '-E16', '-E5', 'E16', 'E5',
                '-21362801', '21362801', '-E8', 'E8', '-E1', 'E1', '146800844#0', '-146800844#1', '-96120140#0', '96120140#0', '-E10', 'E10']
            random_edge = random.choice(eds)
            route_id = "route_{}".format(vehicle_id)
            traci.route.add(route_id, [random_edge])
            traci.vehicle.add(vehID=vehicle_id, routeID=route_id, typeID="veh_passenger")
            traci.vehicle.setColor(vehicle_id, (255, 0, 0))
            traci.vehicle.setSpeed(vehicle_id, 0.0)
            removal_time = 500
            for s in range(step, step + removal_time):
                anomalies_added.setdefault(s, []).append(random_edge)
            print(f"Added {vehicle_id} on {random_edge} at {current_time}, to be removed after {removal_time} steps.")

def collect_data(detector_ids, current_time, interval_length, data_per_inductor):
    # Map each detector IDs to the edge ID
    detector_to_edge = {
        'e1_0': '-E11','e1_1': 'E11', 'e1_2': '-E6', 'e1_3': 'E6', 'e1_4': 'E9', 'e1_5': '-E9', 'e1_6': '-E3',
        'e1_7': 'E3', 'e1_8': '-E4', 'e1_9': 'E4', 'e1_10': 'E2', 'e1_11': '-E2', 'e1_12': 'E13', 'e1_13': '-E13',
        'e1_14': '-E14', 'e1_15': 'E14', 'e1_16': '-399342306', 'e1_17': '868100855#1', 'e1_18': '-68233356#0',
        'e1_19': '399342307#1', 'e1_20': '97506034#2', 'e1_21': '-97506034#2', 'e1_22': '-E15', 'e1_23': 'E15',
        'e1_24': '-E16', 'e1_25': 'E16', 'e1_26': '-E10', 'e1_27': '-E5', 'e1_28': 'E10', 'e1_29': 'E5','e1_30': '-21362801',
        'e1_31': '21362801','e1_32': '-E8','e1_33': 'E8','e1_34': '-E1','e1_35': 'E1','e1_36': '146800844#0',
        'e1_37': '-146800844#1', 'e1_38': '-96120140#0','e1_39': '96120140#0'
    }
    for detector_id in detector_ids:
        # Get edge of anomaly
        edge_id = detector_to_edge[detector_id] 
        # Get vehicle IDs
        vehicle_ids = traci.inductionloop.getLastStepVehicleIDs(detector_id)
        # Get vehicle count
        vehicle_count = traci.inductionloop.getLastStepVehicleNumber(detector_id)
        # Get time since detection
        time_since_detection = traci.inductionloop.getTimeSinceDetection(detector_id)
        # Interval key
        interval_index = int((current_time - 1) // interval_length) + 1
        interval_key = f'interval{interval_index}'
        # Define the key for the next interval
        next_interval_key = f'interval{interval_index + 1}' 
        # Check if an anomaly is currently recorded for this step
        current_anomaly_active = int(edge_id in anomalies_added.get(step, []))
        # Initialize or increment the anomaly active counter
        if current_anomaly_active:
            # Increment the counter for the current interval
            data_per_inductor[detector_id]['anomaly_counter'][interval_key] = data_per_inductor[detector_id]['anomaly_counter'].get(interval_key, 0) + 1
        else:
            # Reset the counter for the current interval if no anomaly is active
            data_per_inductor[detector_id]['anomaly_counter'][interval_key] = 0
        # Prepare to record the anomaly for the next interval if more than 1 intervals have passed
        if data_per_inductor[detector_id]['anomaly_counter'][interval_key] > 1: 
            if interval_index < interval_count:
                data_per_inductor[detector_id]['anomaly'][next_interval_key] = 1
        # For the current interval, we need to check if there was an anomaly active in the last interval
        previous_interval_key = f'interval{interval_index - 1}'  # Define the key for the previous interval
        if data_per_inductor[detector_id]['anomaly_counter'].get(previous_interval_key, 0) > 2:
            data_per_inductor[detector_id]['anomaly'][interval_key] = 1
        else:
            # If there was no active anomaly in the previous interval, ensure the current interval is marked as no anomaly
            data_per_inductor[detector_id]['anomaly'][interval_key] = 0
        # Store vehicle count and time since detection
        data_per_inductor[detector_id]['vehicle_counts'][interval_key] += vehicle_count
        data_per_inductor[detector_id]['time_since'][interval_key] = time_since_detection
        # Process each vehicle's speed - lastMeanSpeed not working
        for vehicle_id in vehicle_ids:
            if vehicle_id in traci.vehicle.getIDList():
                speed = traci.vehicle.getSpeed(vehicle_id)
                data_per_inductor[detector_id]['speeds'][interval_key].append(speed)



# Convert collected data to CSV format
def toCSV(filename, data_per_inductor, interval_count, interval_length,start_time):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row
        headers = ['ID', 'Time', 'Speed', 'No. Veh',  'Time Since', 'Anomaly']
        writer.writerow(headers)
        
        # Iterate through each detector first
        for detector_id, data in data_per_inductor.items():
            # Then iterate through each interval for the current detector
            for i in range(interval_count):
                interval_key = f'interval{i+1}'
                interval_time = (i + 1) * interval_length  # Calculate the time for the interval
                if interval_time > start_time:
                    # Calculate average speed
                    avg_speed = (sum(data['speeds'][interval_key]) / len(data['speeds'][interval_key])
                                if data['speeds'][interval_key] else 0.0)
                    # Get vehicle count
                    vehicle_count = data['vehicle_counts'][interval_key]
                    # Get time since detection
                    time_since = data['time_since'][interval_key]
                    # Get anomaly flag
                    anomaly_flag = data['anomaly'][interval_key]
                
                    # Write the data row for the current detector at the current interval
                    row = [detector_id, interval_time, f"{avg_speed:.2f}", vehicle_count, time_since, anomaly_flag]
                    writer.writerow(row)

start_time = 100
for step in range(interval_count * interval_length):
    traci.simulationStep()
    current_time = traci.simulation.getTime()
    if current_time >= start_time:
        add_anomaly(current_time, step)
        collect_data(detector_ids, current_time, interval_length, data_per_inductor)

toCSV('simulation_results.csv', data_per_inductor, interval_count, interval_length, start_time)
print('Simulation Complete')
traci.close()
