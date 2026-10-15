-- Each user with their roles in one row, so listing users is one query and
-- core/security can read the caller's roles without importing the users
-- domain. role_ids is GROUP_CONCAT's comma-separated string (NULL for no
-- roles, in no guaranteed order): split it with core.security.roles.parse_role_ids.
CREATE VIEW IF NOT EXISTS user_detail_view AS
SELECT
    u.id,
    u.external_user_id,
    u.name,
    u.email,
    u.created_date,
    GROUP_CONCAT(r.role_id) AS role_ids
FROM users u
LEFT JOIN user_roles r ON r.user_id = u.id
GROUP BY u.id;
