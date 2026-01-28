BEGIN TRANSACTION;
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);
INSERT INTO "permissions" VALUES(1,'view_results','查看识别结果');
INSERT INTO "permissions" VALUES(2,'upload_images','上传图片');
INSERT INTO "permissions" VALUES(3,'manage_users','管理用户');
INSERT INTO "permissions" VALUES(4,'manage_roles','管理角色和权限');
CREATE TABLE recognition_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    image_path TEXT,
    result TEXT,
    confidence REAL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);
INSERT INTO "role_permissions" VALUES(1,1);
INSERT INTO "role_permissions" VALUES(1,2);
INSERT INTO "role_permissions" VALUES(1,3);
INSERT INTO "role_permissions" VALUES(1,4);
INSERT INTO "role_permissions" VALUES(2,1);
INSERT INTO "role_permissions" VALUES(2,2);
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);
INSERT INTO "roles" VALUES(1,'admin','系统管理员');
INSERT INTO "roles" VALUES(2,'user','普通用户');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('roles',2);
INSERT INTO "sqlite_sequence" VALUES('permissions',4);
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
);
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
COMMIT;
