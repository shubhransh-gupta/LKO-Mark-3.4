#include <unistd.h>
#include <stdlib.h>
#include <libgen.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char path[PATH_MAX];
    uint32_t size = sizeof(path);
    if (_NSGetExecutablePath(path, &size) == 0) {
        char *dir = dirname(path);
        // If inside LKO.app/Contents/MacOS
        if (strstr(dir, "Contents/MacOS") != NULL) {
            char root[PATH_MAX];
            snprintf(root, sizeof(root), "%s/../../..", dir);
            chdir(root);
            char py[PATH_MAX];
            snprintf(py, sizeof(py), "%s/.venv/bin/python3", root);
            char *args[] = { "LKO", "app.py", NULL };
            execv(py, args);
        } else {
            chdir(dir);
            char py[PATH_MAX];
            snprintf(py, sizeof(py), "%s/.venv/bin/python3", dir);
            char *args[] = { "LKO", "app.py", NULL };
            execv(py, args);
        }
    }
    return 1;
}
