# はじめにやること
-  ```python -m venv venv```
-  ```git pull https://github.com/ShunsukeNaka/digital-signage-be.git master```
-  仮想環境をアクティベート（コマンドは開発環境によって様々なので各自で）
-  ```git pull``` してきたら```digital-signage-be```ディレクトリができているはずなので入る。 ```cd digital-signage-be```
-  ```.env```ファイルを管理者からもらって、```digital-signage-be```ディレクトリ内に配置する
-  ```pip install -r requirements.txt```でライブラリを一括インストール
-  ```digital-signage-be```ディレクトリに```app.py```があるので、仮想環境をアクティベートした状態で```python app.py```

以上の手順でサーバーが起動するはずです。サーバーは59888番ポートで起動します。
