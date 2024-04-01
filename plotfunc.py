import pandas as pd
import matplotlib.pyplot as plt

def plot_edge_speed_vehicles_and_time_since(df, detector_id, std_dev_threshold=1):
    # Filter the DataFrame for the specified detector ID
    df_detector = df[df['ID'] == detector_id].copy()

    # Calculate the mean and standard deviation of the speed and vehicles
    mean_speed = df_detector['Speed'].mean()
    std_dev_speed = df_detector['Speed'].std()
    mean_vehicles = df_detector['No. Veh'].mean()
    std_dev_vehicles = df_detector['No. Veh'].std()

    # Assuming 'Time Since' is a column in df_detector, calculate its mean for reference (no std dev calculation for simplicity)
    mean_time_since = df_detector['Time Since'].mean()

    # Initialize the Anomaly column for speed
    df_detector['Anomaly'] = False

    # Loop through the DataFrame to check for anomalies in speed
    for i in range(1, len(df_detector) - 1):
        current_speed = df_detector.iloc[i]['Speed']
        prev_speed = df_detector.iloc[i - 1]['Speed']
        next_speed = df_detector.iloc[i + 1]['Speed'] if i + 1 < len(df_detector) else prev_speed  # Adjusted to avoid index error
        
        # Check if the current point and either the previous or next point are below the threshold
        if (current_speed < mean_speed - std_dev_threshold * std_dev_speed) and \
           (prev_speed < mean_speed - std_dev_threshold * std_dev_speed or
            next_speed < mean_speed - std_dev_threshold * std_dev_speed):
            df_detector.at[df_detector.index[i], 'Anomaly'] = True

    # Create subplots for speed, vehicle count, and time since
    fig, axs = plt.subplots(1, 3, figsize=(30, 5))  # 1 row, 3 columns

    # Plot for speed
    axs[0].plot(df_detector['Time'], df_detector['Speed'], label='Speed', color='blue')
    axs[0].scatter(df_detector['Time'][df_detector['Anomaly']], df_detector['Speed'][df_detector['Anomaly']], color='red', label='Anomaly')
    axs[0].fill_between(df_detector['Time'], mean_speed - std_dev_speed, mean_speed + std_dev_speed, color='blue', alpha=0.2)
    axs[0].set_title(f'Speed of Detector {detector_id} Over Time')
    axs[0].set_xlabel('Time')
    axs[0].set_ylabel('Speed')
    axs[0].legend()
    axs[0].grid(True)

    # Plot for number of vehicles
    axs[1].plot(df_detector['Time'], df_detector['No. Veh'], label='No. Veh', color='green')
    axs[1].fill_between(df_detector['Time'], mean_vehicles - std_dev_vehicles, mean_vehicles + std_dev_vehicles, color='green', alpha=0.2)
    axs[1].set_title(f'Number of Vehicles for Detector {detector_id} Over Time')
    axs[1].set_xlabel('Time')
    axs[1].set_ylabel('No. Veh')
    axs[1].legend()
    axs[1].grid(True)

    # Plot for Time Since
    axs[2].plot(df_detector['Time'], df_detector['Time Since'], label='Time Since', color='orange')
    axs[2].set_title(f'Time Since Last Detection for {detector_id}')
    axs[2].set_xlabel('Time')
    axs[2].set_ylabel('Time Since (s)')
    axs[2].axhline(y=mean_time_since, color='r', linestyle='--', label=f'Mean Time Since: {mean_time_since:.2f}s')
    axs[2].legend()
    axs[2].grid(True)

    # Display the plots
    plt.show()
if __name__ == "__main__":
    df1 = pd.read_csv('/usr/local/opt/sumo/share/sumo/tools/SimulationFileCopy/simulation_results.csv')
    anomaly_counts = {}
    
    for i in range(40):  
        detector_id = f'e1_{i}'
        anomalies_count = plot_edge_speed_vehicles_and_time_since(df1, detector_id, std_dev_threshold=1)
        anomaly_counts[detector_id] = anomalies_count
