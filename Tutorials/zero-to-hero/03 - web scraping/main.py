weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

# Lists can be split and negative indexes goes end to beginning of the list
print('Original list', weekdays)
print('By index:', weekdays[1])
print('First 3 starting at index 0:', weekdays[0:3])

print('First 3 starting at index 1:', weekdays[1:3])

print('First 3 starting at none:', weekdays[:3])
print('All starting at index 3:', weekdays[3:])

print('First 2 items:', weekdays[:2])
print('Last 2 items:', weekdays[-2:])
print('All the items except for first and last:', weekdays[1:-1])

print('15 items starting at none:', weekdays[:15])

print('Every 1 item:', weekdays[::1])
print('Every 2 items:', weekdays[::2])
print('Every 3 items:', weekdays[::3])

print('Every 1 item reversed:', weekdays[::-1])
print('Every 2 items reversed:', weekdays[::-2])
print('Every 3 items reversed:', weekdays[::-3])
