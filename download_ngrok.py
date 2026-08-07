import os
import ssl
import urllib.request
import zipfile

url = 'https://bin.ngrok.com/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip'
dest_dir = os.path.expanduser(r'~\AppData\Local\ngrok')
os.makedirs(dest_dir, exist_ok=True)
zip_path = os.path.join(dest_dir, 'ngrok.zip')

ctx = ssl._create_unverified_context()
with urllib.request.urlopen(url, context=ctx, timeout=120) as response:
    data = response.read()

with open(zip_path, 'wb') as handle:
    handle.write(data)

with zipfile.ZipFile(zip_path) as archive:
    archive.extractall(dest_dir)

bin_path = os.path.join(dest_dir, 'ngrok.exe')
if not os.path.exists(bin_path):
    raise SystemExit('ngrok.exe was not extracted successfully')

print(f'Installed ngrok at {bin_path}')
