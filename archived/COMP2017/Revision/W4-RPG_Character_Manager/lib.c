#include "lib.h"
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

// Creates a new character with status_flags = 0
Character create_character(const char *name, int level, int hp, int mp) {
    if (name == NULL) {
        perror("Invalid argument for name");
        exit(EXIT_FAILURE);
    }
    Character c;
    strncpy(c.name, name, MAX_CHAR_NAME_LENGTH - 1);
    c.name[MAX_CHAR_NAME_LENGTH - 1] = '\0';
    c.level = level;
    c.hp = hp;
    c.mp = mp;
    c.status_flags = 0;
    return c;
}

// Functions to manipulate status flags using bitwise operators
void set_status_flag(Character *character, unsigned int flag) {
    if (!character) return;
    character->status_flags |= flag;
}

void clear_status_flag(Character *character, unsigned int flag) {
    if (!character) return;
    character->status_flags &= ~flag;
}

int check_status_flag(const Character *character, unsigned int flag) {
    if (!character) return -1;
    return (character->status_flags & flag) != 0;
}


void toggle_status_flag(Character *character, unsigned int flag) {
    if (!character) return;
    character->status_flags ^= flag;
}

// Saves an array of characters to a text file (e.g., CSV)
// Returns 0 on success, -1 on error.
int save_characters_text(const char *filename, const Character characters[], int count) {
    if (!filename || !characters || count <= 0) return -1;
    FILE *fp = fopen(filename, "w");
    if (!fp) {
        perror("Failed to open file for writing");
        return -1;
    }
    fprintf(fp, "name,level,hp,mp,status_flags\n");
    
    for (int i = 0; i < count; i++) {
        fprintf(fp, "%s,%d,%d,%d,%u\n", 
            characters[i].name, 
            characters[i].level, 
            characters[i].hp, 
            characters[i].mp, 
            characters[i].status_flags
        );
    }

    fclose(fp);
    return 0;
}

// Loads characters from a text file into the provided array.
// Returns the number of characters loaded, or -1 on error.
// Assumes the array `characters` has space for `max_count` characters.
int load_characters_text(const char *filename, Character characters[], int max_count) {
    if (!filename || !characters || max_count <= 0) return -1;
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        perror("Failed to open file for reading");
        return -1;
    }
    char line[256];
    int count = 0;

    // Handle the header line
    if (fgets(line, sizeof(line), fp) == NULL) {
        fclose(fp);
        return -1; // file was empty or unreadable
    }

    while (fgets(line, sizeof(line), fp) && count < max_count) {
        Character c;
        int scanned = sscanf(line, "%49[^,],%d,%d,%d,%u",
            c.name,
            &c.level,
            &c.hp,
            &c.mp,
            &c.status_flags
        );
        if (scanned == 5) {
            characters[count++] = c;
        } else {
            fprintf(stderr, "Invalid line skipped: %s", line);
        }
    }

    fclose(fp);
    return count;
}

// Prints character details, interpreting status_flags using bitwise checks
void print_character(const Character *character) {
    if (!character) return;
    printf("Name:  %s\n", character->name);
    printf("Level: %d\n", character->level);
    printf("HP:    %d\n", character->hp);
    printf("MP:    %d\n", character->mp);

    printf("Status: ");
    int any = 0;

    if (check_status_flag(character, STATUS_POISONED)) {
        printf("POISONED ");
        any = 1;
    }

    if (check_status_flag(character, STATUS_PARALYZED)) {
        printf("PARALYZED ");
        any = 1;
    }

    if (check_status_flag(character, STATUS_SHIELDED)) {
        printf("SHIELDED ");
        any = 1;
    }

    if (check_status_flag(character, STATUS_HIDDEN)) {
        printf("HIDDEN ");
        any = 1;
    }

    if (any == 0) printf("None");
    printf("\n");
}
