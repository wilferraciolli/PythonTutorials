-- Optional media on a post: one Unsplash photo, one Giphy GIF or one YouTube video.
-- See docs/social-groups.md "Post media".
-- media_type NULL means no media. media_id is the provider's id (the 11-character
-- video id for YouTube). The rest is filled by the server, never taken from the client:
-- media_url from Unsplash's API or built from the Giphy id (NULL for YouTube: the UI
-- builds the embed from the id); media_title is the image's alt text; the author
-- columns are the Unsplash photographer credit.
ALTER TABLE posts ADD COLUMN media_type TEXT CHECK (media_type IN ('UNSPLASH', 'GIPHY', 'YOUTUBE'));
ALTER TABLE posts ADD COLUMN media_id TEXT;
ALTER TABLE posts ADD COLUMN media_url TEXT;
ALTER TABLE posts ADD COLUMN media_title TEXT;
ALTER TABLE posts ADD COLUMN media_author_name TEXT;
ALTER TABLE posts ADD COLUMN media_author_url TEXT;
