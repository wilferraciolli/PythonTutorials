import { Post, formatPeople, taggedNames } from './social.models';

describe('formatPeople', () => {
  it('reads naturally for one, two, three and more people', () => {
    expect(formatPeople([])).toBe('');
    expect(formatPeople(['Olive'])).toBe('With Olive');
    expect(formatPeople(['Olive', 'Sam'])).toBe('With Olive and Sam');
    expect(formatPeople(['Olive', 'Sam', 'Ana'])).toBe('With Olive, Sam and Ana');
    expect(formatPeople(['Olive', 'Sam', 'Ana', 'Bo', 'Cy'])).toBe('With Olive, Sam and 3 others');
  });
});

describe('taggedNames', () => {
  const post = { taggedUserIds: ['u2', 'gone', 'u1'] } as Post;

  it('names the tagged ids from the metadata, in the post’s order, skipping unknown ids', () => {
    const people = [
      { id: 'u1', value: 'Olive Branch' },
      { id: 'u2', value: 'Sam Rivera' },
    ];
    expect(taggedNames(post, people)).toEqual(['Sam Rivera', 'Olive Branch']);
  });

  it('copes with a post from an API that has no tags yet', () => {
    expect(taggedNames({} as Post, [])).toEqual([]);
  });
});
