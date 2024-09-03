import os

REPOS_DIR = 'repos'
LOGGER_DIR = 'logs_with_make_cmake_gradlew'

# Check if REPORS_DIR exists
if not os.path.exists(REPOS_DIR):
    # If not, create it
    os.makedirs(REPOS_DIR)

if not os.path.exists(LOGGER_DIR):
    os.makedirs(LOGGER_DIR)
