def combine_skeletons(H1, H2):
    i, j = 0, 0
    H = []
    current_height_H1 = 0
    current_height_H2 = 0

    while i < len(H1) and j < len(H2):
        l1, r1, h1 = H1[i]
        l2, r2, h2 = H2[j]
        
        if r1 < l2:  # No overlap, H1 ends before H2 starts
            if not H or H[-1][1] != l1 or H[-1][2] != h1:
                H.append((l1, r1, h1))
            else:
                H[-1] = (H[-1][0], r1, h1)
            i += 1
        elif r2 < l1:  # No overlap, H2 ends before H1 starts
            if not H or H[-1][1] != l2 or H[-1][2] != h2:
                H.append((l2, r2, h2))
            else:
                H[-1] = (H[-1][0], r2, h2)
            j += 1
        else:  # Overlapping segments
            if l1 < l2:
                max_height = max(current_height_H2, h1)
                if not H or H[-1][1] != l1 or H[-1][2] != max_height:
                    H.append((l1, l2, max_height))
                else:
                    H[-1] = (H[-1][0], l2, max_height)
                current_height_H1 = h1
                i += 1
            elif l2 < l1:
                max_height = max(current_height_H1, h2)
                if not H or H[-1][1] != l2 or H[-1][2] != max_height:
                    H.append((l2, l1, max_height))
                else:
                    H[-1] = (H[-1][0], l1, max_height)
                current_height_H2 = h2
                j += 1
            else:  # l1 == l2
                max_height = max(h1, h2)
                end = min(r1, r2)
                if not H or H[-1][1] != l1 or H[-1][2] != max_height:
                    H.append((l1, end, max_height))
                else:
                    H[-1] = (H[-1][0], end, max_height)
                if r1 < r2:
                    current_height_H1 = h1
                    i += 1
                elif r2 < r1:
                    current_height_H2 = h2
                    j += 1
                else:
                    current_height_H1 = h1
                    current_height_H2 = h2
                    i += 1
                    j += 1

    while i < len(H1):
        l, r, h = H1[i]
        if not H or H[-1][1] != l or H[-1][2] != h:
            H.append((l, r, h))
        else:
            H[-1] = (H[-1][0], r, h)
        i += 1

    while j < len(H2):
        l, r, h = H2[j]
        if not H or H[-1][1] != l or H[-1][2] != h:
            H.append((l, r, h))
        else:
            H[-1] = (H[-1][0], r, h)
        j += 1

    return H

# Example usage
H1 = [(0, 3, 3), (3, 5, 2), (6, 8, 4), (9, 11, 3)]
H2 = [(2, 4, 4), (5, 6, 3), (7, 8, 3), (9, 12, 1)]
H = [(0, 2, 3), (2, 4, 4), (4, 5, 2), (6, 8, 4), (9, 11, 3), (11, 12, 1)]
combined_skeleton = combine_skeletons(H1, H2)
print("Combined Top Skeleton:", combined_skeleton)