import os
import json

error_message = "ERROR No supported build system"

# The directory containing the log files 
log_directory = "/home/returningdiver/c_killer/logs/logs_with_make_cmake_gradlew_meson_scons_bazel"

# List to store log files with the error
logs_with_error = []

# Walk through the files in the current directory
for root, dirs, files in os.walk(log_directory):
    for file in files:
        if file.endswith(".log"):
            file_path = os.path.join(root, file)
            try:
                # Open the file and search for the error message
                with open(file_path, 'r') as f:
                    content = f.read()
                    if error_message in content:
                        logs_with_error.append(file)
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

# Define the output JSON file
output_json = "logs_with_no_build_error.json"

# Save the list of log files with the error to a JSON file
with open(output_json, 'w') as json_file:
    json.dump(logs_with_error, json_file, indent=4)

print(f"the list length is: {len(logs_with_error)}")

print(f"Log files with no build error have been saved to {output_json}")
