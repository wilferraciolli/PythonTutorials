-- A user plus their roles in one row. role_ids is a comma-separated list
-- (e.g. 'ADMIN,STANDARD'), NULL when the user has no roles; order is not
-- guaranteed. core/security reads this view, so it can check roles without
-- importing the users domain.
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
