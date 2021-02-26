CREATE TABLE `users`
(
 `id`       int NOT NULL AUTO_INCREMENT,
 `username` varchar(50) NOT NULL UNIQUE,
 `password` text NOT NULL ,
 `mod_`      int NOT NULL DEFAULT 0,
 `admin_`    int NOT NULL DEFAULT 0,

PRIMARY KEY (`id`)
);





