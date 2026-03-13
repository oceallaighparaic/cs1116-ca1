SELECT users.id FROM users 
JOIN permissions ON users.permission = permissions.id 
WHERE permissions.name = 'ADMIN' AND users.id = 1;
