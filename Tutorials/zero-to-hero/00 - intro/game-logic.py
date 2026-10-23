'''
    Program: Game
    Author: WilFerraciolli
'''
import random

class Enemy:
    hp = 200

    def __init__(self, min_attack: int, max_attack: int):
        self.min_attack = min_attack
        self.max_attack = max_attack

    def get_attack(self):
        print('Attack is', self.min_attack)

    def get_health(self):
        print('Hp is', self.hp)

enemy1 = Enemy(40, 49)
enemy1.get_attack()
enemy1.get_health()

enemy2 = Enemy(75, 90)
enemy2.get_attack()
enemy2.get_health()



player_hp = 260
min_damage = 60
max_damage = 80

while player_hp > 0:
    damage = random.randrange(min_damage, max_damage)
    player_hp -= damage

    if player_hp <= 30:
        player_hp = 30

    print('Enemy strikes for', damage, 'points of damage. Current HP is', player_hp)

    if player_hp > 30:
        continue

    print('You hae low health. Youve have been teleported to the nearest inn')
    break