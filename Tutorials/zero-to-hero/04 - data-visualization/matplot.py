import matplotlib.pyplot as plt

players = ['Wil', 'George', 'Maria', 'Olivia']
wins = [8, 5, 6, 1]

# prepare the graph
plt.title('Wins by player')
plt.bar(players, wins)
plt.ylabel('Number of wins')

# display graph
plt.show()
