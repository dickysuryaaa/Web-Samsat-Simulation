# Database Dump

File dump MySQL untuk project ini:

- `samsatgo_flask.sql`

Cara import (Laragon, root tanpa password):

```bat
"C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe" -uroot -e "CREATE DATABASE IF NOT EXISTS samsatgo_flask CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
"C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe" -uroot samsatgo_flask < samsatgo_flask.sql
```

Setelah import, jalankan aplikasi dan pastikan `.env` mengarah ke:

```env
DATABASE_URL=mysql+pymysql://root:@localhost/samsatgo_flask
```

