import os

REPOS_DIR = 'repos'
LOGGER_DIR = f'logs/{REPOS_DIR}_install_logs_with_make_cmake_gradlew_meson_scons_bazel'

# Check if REPORS_DIR exists
if not os.path.exists(REPOS_DIR):
    # If not, create it
    os.makedirs(REPOS_DIR)

if not os.path.exists(LOGGER_DIR):
    os.makedirs(LOGGER_DIR)
