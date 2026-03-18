PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
INSERT INTO users VALUES(1,'testuser','test@example.com','pbkdf2:sha256:1000000$A3wkEuJm94FlOPHg$7b215c12d3c301d920da0a8f6629eba4d69e0804a51a0f6f929f8b5fbbef5a60',1769563038,1769563038);
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);
INSERT INTO roles VALUES(1,'admin','系统管理员');
INSERT INTO roles VALUES(2,'user','普通用户');
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);
INSERT INTO permissions VALUES(1,'view_results','查看识别结果');
INSERT INTO permissions VALUES(2,'upload_images','上传图片');
INSERT INTO permissions VALUES(3,'manage_users','管理用户');
INSERT INTO permissions VALUES(4,'manage_roles','管理角色和权限');
INSERT INTO permissions VALUES(5,'view_community','查看社区内容');
INSERT INTO permissions VALUES(6,'create_posts','创建帖子');
INSERT INTO permissions VALUES(7,'comment_posts','评论帖子');
INSERT INTO permissions VALUES(8,'like_posts','点赞帖子');
INSERT INTO permissions VALUES(9,'follow_users','关注用户');
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
);
INSERT INTO user_roles VALUES(1,2);
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);
INSERT INTO role_permissions VALUES(1,1);
INSERT INTO role_permissions VALUES(1,2);
INSERT INTO role_permissions VALUES(1,3);
INSERT INTO role_permissions VALUES(1,4);
INSERT INTO role_permissions VALUES(1,5);
INSERT INTO role_permissions VALUES(1,6);
INSERT INTO role_permissions VALUES(1,7);
INSERT INTO role_permissions VALUES(1,8);
INSERT INTO role_permissions VALUES(1,9);
INSERT INTO role_permissions VALUES(2,1);
INSERT INTO role_permissions VALUES(2,2);
INSERT INTO role_permissions VALUES(2,5);
INSERT INTO role_permissions VALUES(2,6);
INSERT INTO role_permissions VALUES(2,7);
INSERT INTO role_permissions VALUES(2,8);
INSERT INTO role_permissions VALUES(2,9);
CREATE TABLE recognition_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    image_path TEXT,
    result TEXT,
    confidence REAL,
    created_at INTEGER NOT NULL,
    deleted_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    image_url TEXT,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    deleted_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
INSERT INTO posts VALUES(1,1,'测试帖子内容，这是我的第一篇社区帖子！','https://example.com/flower.jpg',1,1,1769563050,1769563050);
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
INSERT INTO comments VALUES(1,1,1,'这是对测试帖子的评论！',1769563065);
CREATE TABLE likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
INSERT INTO likes VALUES(1,1,1,1769563083);
CREATE TABLE follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL,
    following_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    response TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    cover_image TEXT,
    description TEXT,
    image_count INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS album_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL,
    recognition_result_id INTEGER,
    image_path TEXT NOT NULL,
    flower_name TEXT,
    confidence REAL,
    created_at INTEGER NOT NULL,
    deleted_at INTEGER,
    FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE CASCADE,
    FOREIGN KEY (recognition_result_id) REFERENCES recognition_results (id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS recycle_bin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_type TEXT NOT NULL,
    original_id INTEGER NOT NULL,
    item_data TEXT,
    deleted_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
INSERT INTO sqlite_sequence VALUES('roles',2);
INSERT INTO sqlite_sequence VALUES('permissions',9);
INSERT INTO sqlite_sequence VALUES('users',1);
INSERT INTO sqlite_sequence VALUES('posts',1);
INSERT INTO sqlite_sequence VALUES('comments',1);
INSERT INTO sqlite_sequence VALUES('likes',1);
COMMIT;
