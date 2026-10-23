import matplotlib.pyplot as plt
import numpy as np

column_count = 3
bar_width = 0.1

korea_scores = (554, 536, 538)
canada_scores = (518, 523, 525)
china_scores = (613, 570, 580)
france_scores = (495, 505, 499)

index = np.arange(column_count)

k1 = plt.bar(index, korea_scores, bar_width, alpha=.4, label='Korea')
c1 = plt.bar(index + 0.2, canada_scores, bar_width, alpha=.4, label='Canada')
ch1 = plt.bar(index + 0.4, china_scores, bar_width, alpha=.3, label='China')
f1 = plt.bar(index + 0.6, france_scores, bar_width, alpha=.4, label='France')


def create_labels(data):
    for item in data:
        height = item.get_height()
        plt.text(item.get_x() + item.get_width() / 2, height * 1.05,
                 '%d' % int(height),
                 ha='center',
                 va='bottom')


create_labels(k1)
create_labels(c1)
create_labels(ch1)
create_labels(f1)

plt.ylabel('Score')
plt.xlabel('Subjects')
plt.title('Country Scores')

plt.xticks(index + .3 / 2, ('Maths', 'Reading', 'Science'))
plt.legend(handles=[k1, c1, ch1, f1])
plt.grid(True)

plt.show()
