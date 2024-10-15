#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <tree_sitter/api.h>

// Declare the function provided by the C parser library
extern const TSLanguage *tree_sitter_c(void);

// Function to parse a file and print its syntax tree
void parse_file(const char *filepath, TSParser *parser) {
    FILE *file = fopen(filepath, "r");
    if (!file) {
        fprintf(stderr, "Could not open file: %s\n", filepath);
        return;
    }

    fseek(file, 0, SEEK_END);
    long length = ftell(file);
    fseek(file, 0, SEEK_SET);

    char *source_code = (char *)malloc(length + 1);
    fread(source_code, 1, length, file);
    source_code[length] = '\0';
    fclose(file);

    TSTree *tree = ts_parser_parse_string(parser, NULL, source_code, length);
    TSNode root_node = ts_tree_root_node(tree);

    printf("\nParsed %s:\n", filepath);

    // Iterate through top-level children
    uint32_t child_count = ts_node_child_count(root_node);
    for (uint32_t i = 0; i < child_count; i++) {
        TSNode child = ts_node_child(root_node, i);
        const char *type = ts_node_type(child);
        printf(" - Node: %s\n", type);
    }

    // Clean up
    free(source_code);
    ts_tree_delete(tree);
}


// Recursive function to walk through directories and parse .c and .h files
void walk_directory(const char *path, TSParser *parser) {
    DIR *dir = opendir(path);
    if (!dir) {
        fprintf(stderr, "Could not open directory: %s\n", path);
        return;
    }

    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_DIR) {
            // Skip . and .. directories
            if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
                continue;
            }

            // Build the new path and recurse
            char new_path[1024];
            snprintf(new_path, sizeof(new_path), "%s/%s", path, entry->d_name);
            walk_directory(new_path, parser);
        } else {
            // Check if the file has a .c or .h extension
            if (strstr(entry->d_name, ".c") || strstr(entry->d_name, ".h")) {
                char filepath[1024];
                snprintf(filepath, sizeof(filepath), "%s/%s", path, entry->d_name);
                parse_file(filepath, parser);
            }
        }
    }

    closedir(dir);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <directory>\n", argv[0]);
        return 1;
    }

    // Create a parser and set the language to C
    TSParser *parser = ts_parser_new();
    ts_parser_set_language(parser, tree_sitter_c());

    // Walk through the given directory and parse files
    walk_directory(argv[1], parser);

    // Clean up
    ts_parser_delete(parser);
    return 0;
}
