#include <assert.h>
#include <stdio.h>
#include "lib.h"

void test_status_flag_operations() {
    Character c = create_character("TestChar", 10, 100, 50);

    // Initially no flags
    assert(check_status_flag(&c, STATUS_POISONED) == 0);

    // Set POISONED
    set_status_flag(&c, STATUS_POISONED);
    assert(check_status_flag(&c, STATUS_POISONED) == 1);

    // Set SHIELDED
    set_status_flag(&c, STATUS_SHIELDED);
    assert(check_status_flag(&c, STATUS_SHIELDED) == 1);

    // Clear POISONED
    clear_status_flag(&c, STATUS_POISONED);
    assert(check_status_flag(&c, STATUS_POISONED) == 0);
    assert(check_status_flag(&c, STATUS_SHIELDED) == 1);

    // Toggle HIDDEN
    toggle_status_flag(&c, STATUS_HIDDEN);
    assert(check_status_flag(&c, STATUS_HIDDEN) == 1);

    // Toggle again → OFF
    toggle_status_flag(&c, STATUS_HIDDEN);
    assert(check_status_flag(&c, STATUS_HIDDEN) == 0);
}

void test_print_character() {
    Character c = create_character("Alice", 5, 80, 25);
    set_status_flag(&c, STATUS_POISONED);
    set_status_flag(&c, STATUS_PARALYZED);

    printf("=== Print Test: Alice ===\n");
    print_character(&c);  // Should display POISONED and PARALYZED
}

int main() {
    test_status_flag_operations();
    test_print_character();

    printf("All status flag tests passed!\n");
    return 0;
}

