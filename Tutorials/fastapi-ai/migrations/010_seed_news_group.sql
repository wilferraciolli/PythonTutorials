-- Seed data: a public "News" group with no owner (only admins manage it), some
-- posts spread over the last weeks, and a few comments and replies, so a fresh
-- database has something to show. Authors are NULL = "System".
--
-- Idempotent: fixed ids and INSERT OR IGNORE. Posts and comments are only
-- inserted if the News group row with this id exists (if a user already
-- created their own "News" group, the unique name makes the group insert a
-- no-op and nothing else is seeded).
-- Dates are relative to when the migration runs, so they stay inside the
-- timeline's 1-year window.
--
-- One INSERT per row on purpose: D1 rejects a long `SELECT ... UNION ALL ...`
-- ("too many terms in compound SELECT"), so there are no compound SELECTs here.

INSERT OR IGNORE INTO groups (id, name, description, visibility, owner_id, created_by, created_date)
VALUES (
    '00000000-0000-4000-8000-000000000001',
    'News',
    'Announcements and interesting things from around the web.',
    'PUBLIC',
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-60 days')
);

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000001', NULL,
       'Welcome to News',
       'This is the place for announcements. Follow the group to see new posts in your timeline.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-45 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-45 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000102', '00000000-0000-4000-8000-000000000001', NULL,
       'City approves new cycle lanes',
       'The council voted to add 12 km of protected cycle lanes across the city centre, with work starting next spring.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-38 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-38 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000103', '00000000-0000-4000-8000-000000000001', NULL,
       'Python 3.15 released',
       'The new release brings faster startup, better error messages and a handful of new standard library modules.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-31 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-31 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000104', '00000000-0000-4000-8000-000000000001', NULL,
       'Local library extends opening hours',
       'From next month the central library will open until 9pm on weekdays and all day on Sundays.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-25 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-25 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000105', '00000000-0000-4000-8000-000000000001', NULL,
       'Weekend weather: sunshine at last',
       'Forecasters expect clear skies and highs of 24C on Saturday, with showers returning on Monday.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-19 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-19 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000106', '00000000-0000-4000-8000-000000000001', NULL,
       'New farmers market opens in the old station',
       'Around forty stalls with local produce, bread and coffee, every Saturday morning from 8am.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-14 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-14 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000107', '00000000-0000-4000-8000-000000000001', NULL,
       'Tips for staying focused when working from home',
       'A short list that works for many people: a fixed start time, a separate desk, and a walk at lunch.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-9 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-9 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000108', '00000000-0000-4000-8000-000000000001', NULL,
       'Marathon road closures this Sunday',
       'Roads along the river will be closed from 7am to 2pm. Buses will be diverted; check the transport site.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-5 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-5 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000109', '00000000-0000-4000-8000-000000000001', NULL,
       'What are you reading this month?',
       'Share a book you are enjoying and why. Fiction, non-fiction, anything goes.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-2 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-2 days')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO posts (id, group_id, author_id, title, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000110', '00000000-0000-4000-8000-000000000001', NULL,
       'Site maintenance tonight',
       'The app may be unavailable for a few minutes around midnight while we deploy updates.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-6 hours'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-6 hours')
WHERE EXISTS (SELECT 1 FROM groups WHERE id = '00000000-0000-4000-8000-000000000001');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000201', '00000000-0000-4000-8000-000000000102', NULL, NULL,
       'Great news, the ring road has been dangerous for years.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-37 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-37 days')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000102');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000202', '00000000-0000-4000-8000-000000000102', '00000000-0000-4000-8000-000000000201', NULL,
       'Agreed. I hope they add bike parking at the station too.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-36 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-36 days')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000102');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000203', '00000000-0000-4000-8000-000000000102', NULL, NULL,
       'Does anyone know which streets are first?',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-35 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-35 days')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000102');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000204', '00000000-0000-4000-8000-000000000103', NULL, NULL,
       'The error messages alone make it worth upgrading.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-30 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-30 days')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000103');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000205', '00000000-0000-4000-8000-000000000109', NULL, NULL,
       'Rereading The Hobbit with my kids. Still wonderful.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-1 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-1 days')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000109');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000206', '00000000-0000-4000-8000-000000000109', '00000000-0000-4000-8000-000000000205', NULL,
       'Such a good one to read aloud.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-1 days', '+3 hours'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-1 days', '+3 hours')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000109');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000207', '00000000-0000-4000-8000-000000000109', NULL, NULL,
       'Working through a history of the printing press. Surprisingly gripping.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-20 hours'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-20 hours')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000109');

INSERT OR IGNORE INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date)
SELECT '00000000-0000-4000-8000-000000000208', '00000000-0000-4000-8000-000000000108', NULL, NULL,
       'Thanks for the heads up, I will take the train.',
       strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-4 days'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-4 days')
WHERE EXISTS (SELECT 1 FROM posts WHERE id = '00000000-0000-4000-8000-000000000108');
