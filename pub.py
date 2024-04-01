import os
import traci
import numpy as np
import random
import json
from google.cloud import pubsub_v1
vehicle_spawn_times = {}
# Set up Google Cloud Pub/Sub publisher
publisher = pubsub_v1.PublisherClient()
#topic_path = publisher.topic_path('your-gcp-project-id', 'your-pubsub-topic') projects/tidy-groove-415214/topics/sumoFYP
#topic_path = publisher.topic_path('tidy-groove-415214', 'sumoFYP') s
topic_path = publisher.topic_path('tidy-groove-415214', 'sumoFYP')
'''
def add_anomaly(current_time, step):
    #if current_time in [500, 1500, 2500]:
    if current_time in [500,1500,2500,3500,4500,5500,6500,7500,8500,9500,10500]:
        vehicle_id = "veh{}_{}".format(current_time, step)
        if vehicle_id not in traci.vehicle.getIDList():
            #edges = [ 'E11','-E11','E6','-E6','E9','-E9','E3','-E3','E4','-E4','E2','-E2', 'E13','-E13','E14','-E14','-399342306',
            #'868100855#1','-68233356#0','399342307#1','97506034#2','-97506034#2','-E15','E15','-E16','-E5','E16', 'E5',
            #'-21362801', '21362801','-E8','E8','-E1','E1','146800844#0','-146800844#1','-96120140#0','96120140#0','-E10','E10']
            edges = [ 'E11','-E11','E6','-E6','E9','-E9','E3','-E3','E4','-E4','E2','-E2', 'E13','-E13','E14','-E14','-399342306',
            '868100855#1','-68233356#0','399342307#1','97506034#2','-97506034#2','-E15','E15','-E16','E16', 'E5',
            '-21362801', '21362801','-E8','-E1','E1','146800844#0','-146800844#1','-96120140#0','96120140#0','-E10','E10']
            #random_edge = random.choice(edges)
            random_edge = 'E11'
            print(f"Anomaly added on {random_edge} at {current_time}")
            route_id = "route_{}".format(vehicle_id)
            traci.route.add(route_id, [random_edge])
            traci.vehicle.add(vehID=vehicle_id, routeID=route_id, typeID="veh_passenger")
            traci.vehicle.setColor(vehicle_id, (255, 0, 0))
            traci.vehicle.setSpeed(vehicle_id, 0.0)
'''
def add_anomaly(current_time, step, spawn_probability=0.005, vehicle_removal_times=(300, 400, 500), probabilities=(0.2, 0.4, 0.4)):
    # Use spawn_probability to determine whether to add an anomaly
    if random.random() < spawn_probability:
        vehicle_id = "veh{}_{}".format(current_time, step)
        if vehicle_id not in traci.vehicle.getIDList():
            # List of main roads in Clane
            eds = ['E11', '-E11', 'E6', '-E6', 'E9', '-E9', 'E3', '-E3', 'E4', '-E4', 'E2', '-E2', 'E13', '-E13', 'E14', '-E14', '-399342306',
                   '868100855#1', '-68233356#0', '399342307#1', '97506034#2', '-97506034#2', '-E15', 'E15', '-E16', '-E5', 'E16', 'E5',
                   '-21362801', '21362801', '-E8', 'E8', '-E1', 'E1', '146800844#0', '-146800844#1', '-96120140#0', '96120140#0', '-E10', 'E10']
            random_edge = random.choice(eds)  # Choose a random edge from the list
            route_id = "route_{}".format(vehicle_id)
            traci.route.add(route_id, [random_edge])
            traci.vehicle.add(vehID=vehicle_id, routeID=route_id, typeID="veh_passenger")
            traci.vehicle.setColor(vehicle_id, (255, 0, 0))  # Set the color of the vehicle to red
            traci.vehicle.setSpeed(vehicle_id, 0.0)  # Set the speed to 0 to simulate a blockage

            # Choose a removal time based on the defined probabilities
            removal_time = random.choices(vehicle_removal_times, probabilities)[0]
            
            # Record the spawn time and removal time for the vehicle
            vehicle_spawn_times[vehicle_id] = (step, removal_time)
            print(f"Added {vehicle_id} on {random_edge} at {current_time}, to be removed after {removal_time} steps.")

def publish_data(detector_id, speed, noVeh, time_since_detection, current_time):
    data = json.dumps({
        "Speed": speed,
        "No. Veh": noVeh,
        "time_since_detection": time_since_detection,
        "detector_id": detector_id,
        "current_time": current_time
    })
    # Data must be a bytestring
    data = data.encode("utf-8")
    # Publish a message
    future = publisher.publish(topic_path, data=data)
    #print(f"Published data for detector {detector_id} to {topic_path}: {data}")
    print(f"Published Message")

def run_simulation(sumo_cmd):
    # Start the SUMO simulation
    traci.start(sumo_cmd)
    start_time = 100
    interval_length = 100
    detector_ids = [f'e1_{i}' for i in range(0, 39)]  # Assuming IDs start from e1_0 to e1_41

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        current_time = traci.simulation.getTime()

        # Add anomaly at specific times
        add_anomaly(current_time, int(current_time))

        if current_time >= start_time and current_time % interval_length == 0:
            for detector_id in detector_ids:
                time_since_detection = traci.inductionloop.getTimeSinceDetection(detector_id)
                noVeh = traci.inductionloop.getLastStepVehicleNumber(detector_id)
                vehicle_ids = traci.inductionloop.getLastStepVehicleIDs(detector_id)
                speed = traci.inductionloop.getLastStepMeanSpeed(detector_id)
                # Publish the data
                publish_data(detector_id, speed, noVeh, time_since_detection, current_time)
                
    traci.close()

if __name__ == "__main__":
    sumoCmd = ["sumo-gui", "-c", "osm.sumocfg"]  # Ensure this path is correct
    run_simulation(sumoCmd)

