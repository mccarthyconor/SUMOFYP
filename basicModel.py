import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Load the dataset
df = pd.read_csv('simulation_results.csv')
anomalies = []

for id_group, group_df in df.groupby('ID'):
    
    # Find where speed is 0
    low_speed_mask = group_df['Speed'] == 0
    # Find consecutive intervals with speed 0
    cluster_starts = group_df[low_speed_mask & ~low_speed_mask.shift(1).fillna(False)].index
    cluster_ends = group_df[low_speed_mask & ~low_speed_mask.shift(-1).fillna(False)].index
    # Iterate over the clusters and select those that span at least 5 intervals
    for start, end in zip(cluster_starts, cluster_ends):
        if (end - start + 1) >= 5:
            # Find 'No. Veh' for the last interval of the anomaly
            last_anomaly_veh = group_df.loc[end, 'No. Veh']
            # Find 'No. Veh' for the post anomlay interval 
            first_post_anomaly_veh = group_df.loc[end + 1, 'No. Veh'] if (end + 1) < group_df.index[-1] else 0
            # Calculate the absolute difference in 'No. Veh' count
            veh_difference = abs(last_anomaly_veh - first_post_anomaly_veh)
            # Store results
            anomalies.append((id_group, group_df.loc[start, 'Time'], group_df.loc[end, 'Time'], veh_difference, end - start + 1))

# Convert the anomalies list to a DataFrame
anomalies_df = pd.DataFrame(anomalies, columns=['ID', 'Start_Time', 'End_Time', 'Veh_Difference', 'Duration'])

if not anomalies_df.empty:
    # Sort the anomalies DataFrame by 'Veh_Difference' in descending order
    anomalies_df_sorted_by_veh_diff = anomalies_df.sort_values(by='Veh_Difference', ascending=False)
    # Select the top 3 loop inductors with the biggest change in vehicle count
    top_candidates = anomalies_df_sorted_by_veh_diff.head(3)
  
    # Select longest duration of zeros, if tie - the higher 'Veh_Difference' will be considered
    root_cause = top_candidates.sort_values(by=['Duration', 'Veh_Difference'], ascending=False).iloc[0]
    # Verify if the root cause is correct by checking the 'Anomaly' column
    root_cause_group_df = df[df['ID'] == root_cause['ID']]
    anomaly_check = root_cause_group_df[(root_cause_group_df['Time'] >= root_cause['Start_Time']) & (root_cause_group_df['Time'] <= root_cause['End_Time'])]
    is_correct = anomaly_check['Anomaly'].any()  # Check if correct - should be 1 
    print("")
    print(f"Root cause sensor: {root_cause['ID']} from {root_cause['Start_Time']} to {root_cause['End_Time']},")
    print(f"Vehicle difference: {root_cause['Veh_Difference']}, Duration: {root_cause['Duration']}, Correctly Identified: {is_correct}")
    # The rest are secondary causes
    secondary_causes = anomalies_df_sorted_by_veh_diff[~anomalies_df_sorted_by_veh_diff['ID'].isin([root_cause['ID']])]
    if not secondary_causes.empty:
        print("Secondary causes:")
        print(secondary_causes.to_string(index=False))
    else:
        print("No secondary causes found.")
else:
    print("No anomalies found.")












