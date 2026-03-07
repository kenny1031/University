#ifndef LIB_H
#define LIB_H

#include <stdio.h>  // For FILE*
#include <string.h> // For strncpy, etc.
#include <stdlib.h> // For atoi, exit
#include <ctype.h>  // For tolower (if needed for string comparisons)

#define MAX_CHAR_NAME_LENGTH 50
#define MAX_CHARS 10 // Maximum characters we can load

// --- Bit Masks for Status Flags ---
// Using powers of 2 (or left shifts) to represent individual bits
#define STATUS_POISONED (1 << 0)  // Bit 0: 00000001
#define STATUS_PARALYZED (1 << 1) // Bit 1: 00000010
#define STATUS_SHIELDED (1 << 2)  // Bit 2: 00000100
#define STATUS_HIDDEN (1 << 3)    // Bit 3: 00001000
// Add more flags here using subsequent bits (1 << 4, 1 << 5, ...)

// Main character structure
typedef struct
{
    char name[MAX_CHAR_NAME_LENGTH];
    int level;
    int hp;
    int mp;
    unsigned int status_flags; // Integer to hold packed status flags using bitwise operations
} Character;

// --- Function Prototypes ---

// Creates a new character with status_flags = 0
Character create_character(const char *name, int level, int hp, int mp);

// Functions to manipulate status flags using bitwise operators
void set_status_flag(Character *character, unsigned int flag);        // Sets a specific flag (e.g., STATUS_POISONED) using bitwise OR
void clear_status_flag(Character *character, unsigned int flag);      // Clears a specific flag using bitwise AND NOT
int check_status_flag(const Character *character, unsigned int flag); // Checks if a specific flag is set using bitwise AND
void toggle_status_flag(Character *character, unsigned int flag);     // Toggles a specific flag using bitwise XOR

// Saves an array of characters to a text file (e.g., CSV)
// Returns 0 on success, -1 on error.
int save_characters_text(const char *filename, const Character characters[], int count);

// Loads characters from a text file into the provided array.
// Returns the number of characters loaded, or -1 on error.
// Assumes the array `characters` has space for `max_count` characters.
int load_characters_text(const char *filename, Character characters[], int max_count);

// Prints character details, interpreting status_flags using bitwise checks
void print_character(const Character *character);

#endif // LIB_H

