def count_substring(string, sub_string):
    """
    Counts the number of occurrences of 'sub_string' in 'string' 
    by traversing the string from left to right.
    """
    count = 0
    # Lengths of the strings
    len_string = len(string)
    len_sub = len(sub_string)
    
    # We loop from the start (0) up to the point where the sub_string
    # can no longer fit in the remaining part of the main string.
    # The loop should go from 0 up to (len_string - len_sub) inclusive.
    # range() excludes the stop value, so we use (len_string - len_sub + 1)
    # The constraint image mentions range(0, 5) excludes 5.
    for i in range(len_string - len_sub + 1):
        # Extract a slice of the main string starting at index i, 
        # with a length equal to the sub_string length.
        slice_of_string = string[i : i + len_sub]
        
        # Check if the extracted slice matches the sub_string
        if slice_of_string == sub_string:
            count += 1
            
    return count

if __name__ == '__main__':
    string = input().strip()
    sub_string = input().strip()
    
    count = count_substring(string, sub_string)
    print(count)