from classes.game import Person, bcolors

magic = [
    {"name": "Fire", "cost": 10, "dmg": 60},
    {"name": "Thunder", "cost": 10, "dmg": 80},
    {"name": "Blizzard", "cost": 10, "dmg": 60}
]

player: Person = Person(460, 65, 60, 34, magic)
enemy: Person = Person(1200, 65, 45, 25, magic)

running = True
i = 0

print(bcolors.FAIL + bcolors.BOLD + 'An enemy attacks!' + bcolors.ENDC)

while running:
    print('============================================')
    player.choose_action()
    choice = input('Choose an action:')
    index = int(choice) - 1

    if index == 0:
        dmg = player.generate_damage()
        enemy.take_damage(dmg)
        print('You attacked for', dmg, 'enemy hp is now', enemy.get_hp())
    elif index == 1:
        player.choose_magic()
        magic_choice = int(input('Choose a magic:')) - 1
        magic_dmg = player.generate_spell(magic_choice)
        spell = player.get_spell_name(magic_choice)
        cost = player.get_spell_mp_cost(magic_choice)

        current_mp = player.get_mp()

        if cost > current_mp:
            print(bcolors.FAIL + '\nNot enough MP\n' + bcolors.ENDC)
            continue

        player.reduce_mp(cost)
        enemy.take_damage(magic_dmg)
        print(bcolors.OKBLUE + 'spell')

    enemy_choice = 1

    enemy_dmg = enemy.generate_damage()
    player.take_damage(enemy_dmg)
    print('enemy attacked for', enemy_dmg, 'player hp is now', player.get_hp())

    if enemy.get_hp() == 0:
        print(bcolors.OKGREEN + 'You win!' + bcolors.ENDC)
        running = False
    elif player.get_hp() == 0:
        print(bcolors.FAIL + 'You lose!' + bcolors.ENDC)
        running = False
