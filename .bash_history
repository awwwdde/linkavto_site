ssh root@89.23.97.97 "cd /home && ls -la"
ssh root@89.23.97.97
ssh root@89.23.97.97 "cd /var/www && rm -rf linkavto && mkdir -p linkavto && cd linkavto && tar -xzf /root/linkavto_deploy_20251005_165545.tar.gz && ls -la"
ssh root@89.23.97.97 "cd /var/www/linkavto && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
ssh root@89.23.97.97 "cd /var/www/linkavto && source venv/bin/activate && python manage.py migrate && python manage.py collectstatic --noinput"
ssh root@89.23.97.97 "cd /var/www/linkavto && echo 'djangorestframework==3.15.2' >> requirements.txt && source venv/bin/activate && pip install djangorestframework==3.15.2"
ssh root@89.23.97.97 "cd /var/www/linkavto && source venv/bin/activate && python manage.py migrate && python manage.py collectstatic --noinput"
ssh root@89.23.97.97 "cd /var/www/linkavto && echo 'rapidfuzz==3.6.1' >> requirements.txt && source venv/bin/activate && pip install rapidfuzz==3.6.1"
ssh root@89.23.97.97 "cd /var/www/linkavto && source venv/bin/activate && python manage.py migrate && python manage.py collectstatic --noinput"
ssh root@89.23.97.97 "ls -la /root/*.tar.gz"
ssh root@89.23.97.97
oVdre?8WSo*vTy
ssh root@89.23.97.97
cd /var/www/linkavto
cd /opt/linkavto
source venv/bin/activate
sudo -u postgres psql -d avtolink_django -c "SELECT COUNT(*) FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT COUNT(*) FROM shop_product;"
python delete_superuser.py
nano /opt/linkavto/delete_superuser_by_id.py
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser, is_staff, is_active FROM auth_user;"
python manage.py createsuperuser
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "
INSERT INTO auth_user (username, password, is_superuser, is_staff, is_active, date_joined) 
VALUES ('admin', 'pbkdf2_sha256$600000$xyz...', true, true, true, NOW());
"
sudo -u postgres psql -d avtolink_django -c "SELECT id, username, email, is_superuser FROM auth_user WHERE is_superuser = true;"
sudo -u postgres psql -d avtolink_django -c "DELETE FROM auth_user WHERE is_superuser = true;"
sudo -u postgres psql -d avtolink_django -c "SELECT id, username, email FROM auth_user WHERE is_superuser = true;"
sudo -u postgres psql -d avtolink_django -c "
-- Удаляем связанные записи (замените ID на реальные из предыдущего запроса)
DELETE FROM accounts_address WHERE user_id IN (SELECT id FROM auth_user WHERE is_superuser = true);
DELETE FROM accounts_profile WHERE user_id IN (SELECT id FROM auth_user WHERE is_superuser = true);
DELETE FROM accounts_passwordresetcode WHERE user_id IN (SELECT id FROM auth_user WHERE is_superuser = true);
DELETE FROM auth_user_groups WHERE user_id IN (SELECT id FROM auth_user WHERE is_superuser = true);
DELETE FROM auth_user_user_permissions WHERE user_id IN (SELECT id FROM auth_user WHERE is_superuser = true);
"
sudo -u postgres psql -d avtolink_django -c "DELETE FROM auth_user WHERE is_superuser = true;"
sudo -u postgres psql -d avtolink_django -c "
-- Удаляем связанные записи для пользователя с ID=2
DELETE FROM accounts_address WHERE user_id = 2;
DELETE FROM accounts_profile WHERE user_id = 2;
DELETE FROM accounts_passwordresetcode WHERE user_id = 2;
DELETE FROM auth_user_groups WHERE user_id = 2;
DELETE FROM auth_user_user_permissions WHERE user_id = 2;
"
sudo -u postgres psql -d avtolink_django -c "DELETE FROM auth_user WHERE id = 2;"
sudo -u postgres psql -d avtolink_django -c "
SELECT conname, conrelid::regclass AS table_name 
FROM pg_constraint 
WHERE confrelid = 'auth_user'::regclass AND contype = 'f';
"
sudo -u postgres psql -d avtolink_django -c "
-- Удаляем все связанные записи для пользователя с ID=2
DELETE FROM accounts_address WHERE user_id = 2;
DELETE FROM accounts_profile WHERE user_id = 2;
DELETE FROM accounts_passwordresetcode WHERE user_id = 2;
DELETE FROM auth_user_groups WHERE user_id = 2;
DELETE FROM auth_user_user_permissions WHERE user_id = 2;
DELETE FROM cart_cart WHERE user_id = 2;
DELETE FROM cart_cartitem WHERE user_id = 2;
DELETE FROM favorites_favorite WHERE user_id = 2;
DELETE FROM orders_order WHERE user_id = 2;
"
sudo -u postgres psql -d avtolink_django -c "DELETE FROM auth_user WHERE id = 2;"
sudo -u postgres psql -d avtolink_django -c "
-- Удаляем все связанные записи для пользователя с ID=2
DELETE FROM accounts_address WHERE user_id = 2;
DELETE FROM accounts_profile WHERE user_id = 2;
DELETE FROM accounts_passwordresetcode WHERE user_id = 2;
DELETE FROM auth_user_groups WHERE user_id = 2;
DELETE FROM auth_user_user_permissions WHERE user_id = 2;
DELETE FROM django_admin_log WHERE user_id = 2;
DELETE FROM shop_productclick WHERE user_id = 2;
DELETE FROM shop_productview WHERE user_id = 2;
DELETE FROM shop_review WHERE user_id = 2;
DELETE FROM shop_reviewfeedback WHERE user_id = 2;
DELETE FROM cart_cart WHERE user_id = 2;
DELETE FROM favorites_favorite WHERE user_id = 2;
DELETE FROM orders_historicalorder WHERE history_user_id = 2;
DELETE FROM orders_order WHERE user_id = 2;
DELETE FROM search_searchquery WHERE user_id = 2;
"
sudo -u postgres psql -d avtolink_django -c "DELETE FROM auth_user WHERE id = 2;"
sudo -u postgres psql -d avtolink_django -c "DELETE FROM auth_user WHERE id = 2 CASCADE;"
sudo -u postgres psql -d avtolink_django -c "
-- Временно отключаем триггеры и внешние ключи
SET session_replication_role = replica;

-- Удаляем пользователя
DELETE FROM auth_user WHERE id = 2;

-- Включаем обратно
SET session_replication_role = DEFAULT;
"
sudo -u postgres psql -d avtolink_django -c "SELECT id, username, email FROM auth_user WHERE id = 2;"
python manage.py createsuperuser
nano /var/www/linkavto/avtolink/settings.py
nano /opt/linkavto/avtolink/settings.py
python manage.py createsuperuser
nano /opt/linkavto/avtolink/settings.py
python manage.py migrate
python manage.py shell
find /opt/linkavto -name "*.sqlite3"
rm -f /var/www/linkavto/db.sqlite3
sudo -u postgres psql -d avtolink_django -c "SELECT version();"
sudo -u postgres psql -d avtolink_django -c "\dt"
python manage.py migrate accounts
python manage.py migrate auth
python manage.py migrate contenttypes
python manage.py createsuperuser --username admin --email admin@linkavto.ru --noinput
python manage.py shell
systemctl status postgresql
systemctl status gunicorn_avtolink
systemctl status nginx
python manage.py createsuperuser --username admin --email admin@linkavto.ru --noinput
python manage.py shell
sudo -u postgres psql -d avtolink_django -c "SELECT id, username, email, is_superuser FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "\dt"
nano /opt/linkavto/avtolink/settings.py
python manage.py dumpdata --exclude=contenttypes --exclude=auth.Permission --indent=2 > /tmp/sqlite_dump.json
nano /opt/linkavto/avtolink/settings.py
python manage.py migrate
python manage.py loaddata /tmp/sqlite_dump.json
python manage.py createsuperuser --username admin --email admin@linkavto.ru --noinput
python manage.py createsuperuser --username admin_dag --email admin@linkavto.ru --noinput
python manage.py shell
sudo -u postgres psql -d avtolink_django -c "SELECT COUNT(*) FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT COUNT(*) FROM shop_product;"
sudo -u postgres psql -d avtolink_django -c "\dt"
systemctl restart gunicorn_avtolink
curl -I https://linkavto.ru
cp /opt/linkavto/db.sqlite3 /tmp/db.sqlite3.backup
rm -f /opt/linkavto/db.sqlite3
cd /opt/linkavto
source venv/bin/activate
sudo -u postgres psql -d avtolink_django -c "SELECT COUNT(*) FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT id, username, email, is_superuser, is_staff FROM auth_user;"
python manage.py shell
cp /opt/linkavto/db.sqlite3 /tmp/db.sqlite3.backup
rm -f /var/www/linkavto/db.sqlite3
rm -f /opt/linkavto/db.sqlite3
nano /var/www/linkavto/avtolink/settings.py
nano /opt/linkavto/avtolink/settings.py
python manage.py migrate
sudo -u postgres psql -d avtolink_django -c "SELECT id, username, email, is_superuser, is_staff FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT german69g@yandex.ru FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT username FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "UPDATE auth_user SET is_superuser = true, is_staff = true WHERE german69g@yandex.ru = 'german69g@yandex.ru';"
python manage.py createsuperuser --username admin --email admin@linkavto.ru --noinput
python manage.py shell
systemctl restart gunicorn_avtolink
sudo -u postgres psql -d avtolink_django -c "SELECT username FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "UPDATE auth_user SET is_superuser = true, is_staff = true WHERE username = 'german69g@yandex.ru';"
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser, is_staff FROM auth_user WHERE is_superuser = true;"
python manage.py shell
nano /opt/linkavto/avtolink/settings.py
rm -f /var/www/linkavto/db.sqlite3
rm -f /opt/linkavto/db.sqlite3
python manage.py migrate
python manage.py createsuperuser
sudo -u postgres psql -d avtolink_django -c "SELECT username FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser, is_staff FROM auth_user WHERE is_superuser = true;"
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser FROM auth_user;"
python manage.py shell -c "
from django.contrib.auth.models import User
print('Пользователей в Django:', User.objects.count())
for user in User.objects.all():
    print(f'{user.username} - {user.email} - superuser: {user.is_superuser}')
"
python manage.py createsuperuser
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser, is_staff FROM auth_user WHERE is_superuser = true;"
python manage.py shell -c "
from django.contrib.auth.models import User
print('Пользователей в Django:', User.objects.count())
for user in User.objects.all():
    print(f'{user.username} - {user.email} - superuser: {user.is_superuser}')
"
python manage.py createsuperuser
python manage.py shell
python manage.py shell -c "
from django.contrib.auth.models import User
for user in User.objects.all():
    print(f'{user.username} - {user.email} - superuser: {user.is_superuser}')
"
cd..
cd /var/www/linkavto
cd /opt/linkavto
source venv/bin/activate
python manage.py shell
python manage.py shell -c "
from django.contrib.auth.models import User
for user in User.objects.all():
    print(f'{user.username} - {user.email} - superuser: {user.is_superuser}')
"
python manage.py shell
python manage.py createsuperuser --username newadmin --email newadmin@linkavto.ru --noinput
python manage.py shell
sudo -u postgres psql -d avtolink_django -c "SELECT username, email, is_superuser, is_staff, is_active FROM auth_user;"
python manage.py shell
nano avtolink/settings.py
rm -f /opt/linkavto/db.sqlite3
python manage.py shell -c "
from django.conf import settings
print('Database ENGINE:', settings.DATABASES['default']['ENGINE'])
print('Database NAME:', settings.DATABASES['default']['NAME'])
"
python manage.py migrate
python manage.py createsuperuser --username admin --email admin@linkavto.ru --noinput
python manage.py shell
python manage.py shell -c "
from django.conf import settings
from django.contrib.auth.models import User

print('Database ENGINE:', settings.DATABASES['default']['ENGINE'])
print('Пользователей в Django:', User.objects.count())

# Должны увидеть пользователей из PostgreSQL
for user in User.objects.all():
    print(f'{user.username} - {user.email}')
"
https://linkavto.ru/admin
lynx https://linkavto.ru/admin
apt install lynx
lynx https://linkavto.ru/admin
apt install lynx
lynx https://linkavto.ru/admin
cd /opt/linkavto
source venv/bin/activate
python manage.py createsuperuser
cd /opt/linkavto
source venv/bin/activate
python manage.py createsuperuser
cd /opt/linkavto
source venv/bin/activate
python manage.py createsuperuser
ssh root@89.23.97.97 "systemctl restart linkavto.service && systemctl status linkavto.service | head -10"
cd /opt/linkavto
source venv/bin/activate
tar -czf linkavto_backup_$(date +%Y%m%d).tar.gz linkavto/
cd /opt
tar -czf linkavto_backup_$(date +%Y%m%d).tar.gz linkavto/
ls -lh linkavto_backup_*.tar.gz
scp -r root@193.227.241.158:/opt/linkavto ./
cd /opt/linkavto
source venv/bin/activate
cd /opt
ls -lh linkavto_backup_*.tar.gz
scp -r root@89.23.97.97:/opt/linkavto ./
cd /opt
tar -tzf linkavto_backup_20250928.tar.gz | head -20
tar -czf linkavto_backup_$(date +%Y%m%d).tar.gz linkavto/
ls -lh linkavto_backup_*.tar.gz
cd /opt/linkavto
source venv/bin/activate
cd /opt
tar -czf linkavto_backup_$(date +%Y%m%d).tar.gz linkavto/
ls -lh linkavto_backup_*.tar.gz
scp root@193.227.241.158:/opt/linkavto_backup_20251105.tar.gz ./
scp root@89.23.97.97:/opt/linkavto_backup_20251105.tar.gz ./
scp -r root@89.23.97.97:/opt/linkavto ./ C:\Program Files
scp root@89.23.97.97:/opt/linkavto_backup_20251105.tar.gz ./
scp -r root@89.23.97.97:/opt/linkavto ./
tar -czf linkavto_1212_$(date +%Y%m%d).tar.gz linkavto/
ls -lh linkavto_1212_*.tar.gz
pip install djangorestframework==3.16.1]
source venv/bin/activate
cd /opt/linkavto
source venv/bin/activate
pip install djangorestframework==3.16.1
pip install rapidfuzz==3.14.3
pip install pandas==2.3.3
python manage.py makemigrations accounts
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
systemctl restart gunicorn
systemctl restart nginx
cd /path/to/linkavto-main
pip install djangorestframework==3.16.1
pip install rapidfuzz==3.14.3
pip install pandas==2.3.3
python manage.py makemigrations accounts
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn
systemctl restart nginx
systemctl list-units | grep -i django
supervisorctl status
systemctl list-units | grep -i uwsgi
ps aux | grep python
systemctl list-units --type=service | grep -E 'linkavto|django'
sudo systemctl restart linkavto
sudo systemctl status linkavto
cat /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html | grep -i "самовывоз"
ls -lh /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
stat /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
cat /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html | grep -i "самовывоз"
sudo systemctl restart linkavto
python manage.py collectstatic --noinput
scp accounts/templates/accounts/modals/address_map_modal.html root@твой_ip:/opt/linkavto/accounts/templates/accounts/modals/
cd /opt/linkavto
source venv/bin/activate
scp accounts/templates/accounts/modals/address_map_modal.html root@твой_ip:/opt/linkavto/accounts/templates/accounts/modals/
sudo systemctl restart linkavto
bybit:page provider inject code 
(index):9519  GET https://linkavto.ru/media/products/default.png 404 (Not Found)
orders.js:22 Uncaught SyntaxError: Unexpected token '%' (at orders.js:22:10)
(index):18077  GET https://linkavto.ru/static/js/address_list_modal.js net::ERR_ABORTED 404 (Not Found)
(index):18078  GET https://linkavto.ru/static/js/address_list_partial.js net::ERR_ABORTED 404 (Not Found)
(index):4604 Auth modals script loaded
(index):8658 Found address dropdown buttons: 0
(index):18092 Found sort options: 0
(index):18093 Found sort input: null
(index):18094 Found mobile sort input: null
(index):18320 No sort options found
(index):18911 Initializing mobile autocomplete...
(index):18071  GET https://linkavto.ru/static/images/hero1.jpg 404 (Not Found)
(index):10307  GET https://linkavto.ru/media/products/default.png 404 (Not Found)
(index):19012 Mobile autocomplete elements: {mobileSearchInput: true, mobileAutocompleteDropdown: true, mobileSearchForm: true}
(index):6579 Yandex Maps API ready
(index):8427  GET https://linkavto.ru/accounts/login/?next=/account/get-default-address/ 404 (Not Found)
updateHeaderAddress @ (index):8427
(anonymous) @ (index):8905
(index):8494 Error updating header address: SyntaxError: Unexpected token '<', "
(anonymous) @ (index):8494
Promise.catch
updateHeaderAddress @ (index):8493
(anonymous) @ (index):8905
(index):8910 === initAddressModal CALLED ===
(index):8911 Current URL: https://linkavto.ru/
(index):8918 Initializing dropdowns in address modal...
(index):8658 Found address dropdown buttons: 0
(index):8929 Initializing address events...
(index):8934 Re-initializing dropdowns after delay...
(index):8658 Found address dropdown buttons: 0
(index):8427  GET https://linkavto.ru/accounts/login/?next=/account/get-default-address/ 404 (Not Found)
updateHeaderAddress @ (index):8427
initAddressModal @ (index):8914
trigger @ event-handler.js:289
show @ modal.js:101
toggle @ modal.js:93
(anonymous) @ modal.js:365
n @ event-handler.js:118
(index):8494 Error updating header address: SyntaxError: Unexpected token '<', "
(anonymous) @ (index):8494
Promise.catch
updateHeaderAddress @ (index):8493
initAddressModal @ (index):8914
trigger @ event-handler.js:289
show @ modal.js:101
toggle @ modal.js:93
(anonymous) @ modal.js:365
n @ event-handler.js:118
(index):8957 Address modal fully shown, re-initializing dropdowns...
(index):8658 Found address dropdown buttons: 0
3(index):7645 Page scroll restored
(index):8427  GET https://linkavto.ru/accounts/login/?next=/account/get-default-address/ 404 (Not Found)
updateHeaderAddress @ (index):8427
(anonymous) @ (index):8965
trigger @ event-handler.js:289
(anonymous) @ modal.js:254
g @ index.js:226
(anonymous) @ backdrop.js:93
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_emulateAnimation @ backdrop.js:145
hide @ backdrop.js:91
_hideModal @ modal.js:250
(anonymous) @ modal.js:138
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_queueCallback @ base-component.js:49
hide @ modal.js:138
(anonymous) @ modal.js:360
n @ event-handler.js:118
(index):8494 Error updating header address: SyntaxError: Unexpected token '<', "
(anonymous) @ (index):8494
Promise.catch
updateHeaderAddress @ (index):8493
(anonymous) @ (index):8965
trigger @ event-handler.js:289
(anonymous) @ modal.js:254
g @ index.js:226
(anonymous) @ backdrop.js:93
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_emulateAnimation @ backdrop.js:145
hide @ backdrop.js:91
_hideModal @ modal.js:250
(anonymous) @ modal.js:138
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_queueCallback @ base-component.js:49
hide @ modal.js:138
(anonymous) @ modal.js:360
n @ event-handler.js:118
hero3.jpg:1  GET https://linkavto.ru/static/images/hero3.jpg 404 (Not Found)
/static/images/hero2.jpg:1  GET https://linkavto.ru/static/images/hero2.jpg 404 (Not Found)
bybit:page provider inject code 
(index):9519  GET https://linkavto.ru/media/products/default.png 404 (Not Found)
orders.js:22 Uncaught SyntaxError: Unexpected token '%' (at orders.js:22:10)
(index):18077  GET https://linkavto.ru/static/js/address_list_modal.js net::ERR_ABORTED 404 (Not Found)
(index):18078  GET https://linkavto.ru/static/js/address_list_partial.js net::ERR_ABORTED 404 (Not Found)
(index):4604 Auth modals script loaded
(index):8658 Found address dropdown buttons: 0
(index):18092 Found sort options: 0
(index):18093 Found sort input: null
(index):18094 Found mobile sort input: null
(index):18320 No sort options found
(index):18911 Initializing mobile autocomplete...
(index):18071  GET https://linkavto.ru/static/images/hero1.jpg 404 (Not Found)
(index):10307  GET https://linkavto.ru/media/products/default.png 404 (Not Found)
(index):19012 Mobile autocomplete elements: {mobileSearchInput: true, mobileAutocompleteDropdown: true, mobileSearchForm: true}
(index):6579 Yandex Maps API ready
(index):8427  GET https://linkavto.ru/accounts/login/?next=/account/get-default-address/ 404 (Not Found)
updateHeaderAddress @ (index):8427
(anonymous) @ (index):8905
(index):8494 Error updating header address: SyntaxError: Unexpected token '<', "
(anonymous) @ (index):8494
Promise.catch
updateHeaderAddress @ (index):8493
(anonymous) @ (index):8905
(index):8910 === initAddressModal CALLED ===
(index):8911 Current URL: https://linkavto.ru/
(index):8918 Initializing dropdowns in address modal...
(index):8658 Found address dropdown buttons: 0
(index):8929 Initializing address events...
(index):8934 Re-initializing dropdowns after delay...
(index):8658 Found address dropdown buttons: 0
(index):8427  GET https://linkavto.ru/accounts/login/?next=/account/get-default-address/ 404 (Not Found)
updateHeaderAddress @ (index):8427
initAddressModal @ (index):8914
trigger @ event-handler.js:289
show @ modal.js:101
toggle @ modal.js:93
(anonymous) @ modal.js:365
n @ event-handler.js:118
(index):8494 Error updating header address: SyntaxError: Unexpected token '<', "
(anonymous) @ (index):8494
Promise.catch
updateHeaderAddress @ (index):8493
initAddressModal @ (index):8914
trigger @ event-handler.js:289
show @ modal.js:101
toggle @ modal.js:93
(anonymous) @ modal.js:365
n @ event-handler.js:118
(index):8957 Address modal fully shown, re-initializing dropdowns...
(index):8658 Found address dropdown buttons: 0
3(index):7645 Page scroll restored
(index):8427  GET https://linkavto.ru/accounts/login/?next=/account/get-default-address/ 404 (Not Found)
updateHeaderAddress @ (index):8427
(anonymous) @ (index):8965
trigger @ event-handler.js:289
(anonymous) @ modal.js:254
g @ index.js:226
(anonymous) @ backdrop.js:93
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_emulateAnimation @ backdrop.js:145
hide @ backdrop.js:91
_hideModal @ modal.js:250
(anonymous) @ modal.js:138
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_queueCallback @ base-component.js:49
hide @ modal.js:138
(anonymous) @ modal.js:360
n @ event-handler.js:118
(index):8494 Error updating header address: SyntaxError: Unexpected token '<', "
(anonymous) @ (index):8494
Promise.catch
updateHeaderAddress @ (index):8493
(anonymous) @ (index):8965
trigger @ event-handler.js:289
(anonymous) @ modal.js:254
g @ index.js:226
(anonymous) @ backdrop.js:93
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_emulateAnimation @ backdrop.js:145
hide @ backdrop.js:91
_hideModal @ modal.js:250
(anonymous) @ modal.js:138
g @ index.js:226
a @ index.js:247
s @ index.js:71
(anonymous) @ index.js:253
setTimeout
_ @ index.js:251
_queueCallback @ base-component.js:49
hide @ modal.js:138
(anonymous) @ modal.js:360
n @ event-handler.js:118
hero3.jpg:1  GET https://li
sudo systemctl restart linkavto
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
ls -lh /opt/linkavto/staticfiles/js/pickup_points*
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
cd /opt/linkavto
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
ls -lh /opt/linkavto/staticfiles/js/ | grep pickup
python manage.py collectstatic --clear --noinput
sudo systemctl restart linkavto
ls -lh /opt/linkavto/staticfiles/js/ | grep pickup
ls -lh /opt/linkavto/accounts/static/js/
cd /opt/linkavto
source venv/bin/activate
ls -lh /opt/linkavto/accounts/static/js/pickup*
ls -lh /opt/linkavto/accounts/static/js/pickup
cp /root/staticfiles/js/pickup_points.js /opt/linkavto/accounts/static/js/
cd /opt/linkavto
nano .env
cd /opt/linkavto
source venv/bin/activate
python manage.py collectstatic --clear --noinput
sudo systemctl restart linkavto
sudo systemctl status linkavto
sudo journalctl -u linkavto -n 50 -f
sudo tail -f /var/log/nginx/error.log
grep -c "Яндекс.Доставка" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
stat /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html | grep Modify
ls -lh /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
grep -c "yandex-delivery-widget" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
grep "YANDEX_DELIVERY_TOKEN" /opt/linkavto/avtolink/settings.py
grep "YANDEX_DELIVERY_TOKEN" /opt/linkavto/.env
echo "=== ПРОВЕРКА ФАЙЛОВ ==="
echo ""
echo "1. Яндекс.Доставка в шаблоне:"
grep -c "Яндекс.Доставка" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
echo ""
echo "2. Виджет Яндекс в шаблоне:"
grep -c "yandex-delivery-widget" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
echo ""
echo "3. Размер и дата файла:"
ls -lh /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
echo ""
echo "4. YANDEX_DELIVERY_TOKEN в settings.py:"
grep "YANDEX_DELIVERY_TOKEN" /opt/linkavto/avtolink/settings.py
echo ""
echo "5. YANDEX_DELIVERY_TOKEN в .env:"
grep "YANDEX_DELIVERY_TOKEN" /opt/linkavto/.env
echo ""
echo "=== КОНЕЦ ПРОВЕРКИ ==="
scp accounts/templates/accounts/modals/address_map_modal.html root@89.23.97.97:/opt/linkavto/accounts/templates/accounts/modals/
scp avtolink/settings.py root@89.23.97.97:/opt/linkavto/avtolink/
scp accounts/context_processors.py root@89.23.97.97:/opt/linkavto/accounts/
# Проверить, что файлы обновились
echo "=== ПРОВЕРКА ПОСЛЕ ЗАГРУЗКИ ==="
grep -c "Яндекс.Доставка" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
grep "YANDEX_DELIVERY_TOKEN" /opt/linkavto/avtolink/settings.py
# Собрать статику
python manage.py collectstatic --clear --noinput
# Перезапустить Django
sudo systemctl restart linkavto
# Проверить статус
sudo systemctl status linkavto
cd /opt/linkavto
source venv/bin/activate
echo "=== ПРОВЕРКА ЗАГРУЖЕННЫХ ФАЙЛОВ ==="
echo ""
echo "1. Яндекс.Доставка в шаблоне (должно быть > 0):"
grep -c "Яндекс.Доставка" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
echo ""
echo "2. Виджет Яндекс в шаблоне (должно быть > 0):"
grep -c "yandex-delivery-widget" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
echo ""
echo "3. Размер файла (должен быть ~140KB):"
ls -lh /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
echo ""
echo "4. YANDEX_DELIVERY_TOKEN в settings.py:"
grep "YANDEX_DELIVERY_TOKEN" /opt/linkavto/avtolink/settings.py
echo ""
echo "5. Context processor обновлен:"
grep "YANDEX_DELIVERY_TOKEN" /opt/linkavto/accounts/context_processors.py
echo ""
echo "=== ПЕРЕЗАПУСК СЕРВИСОВ ==="
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
sudo systemctl status linkavto --no-pager
echo ""
echo "✅ ГОТОВО! Проверьте сайт: https://linkavto.ru"
cd /opt/linkavto
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
exit
cd /opt/linkavto
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
cd /opt/linkavto
source venv/bin/activate
sudo systemctl restart linkavto
cd /opt/linkavto
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
sudo systemctl status linkavto --no-pager
exit
cd /opt/linkavto
source venv/bin/activate
python manage.py collectstatic --noinput && sudo systemctl restart linkavto"
python manage.py collectstatic --noinput && sudo systemctl restart linkavto
sudo systemctl restart
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
find /root/linkavto -name 'address_map_modal.html' -type f
"find /root/linkavto -name 'address_map_modal.html' -type f"
cd /opt/linkavto
source venv/bin/activate
find . -name "address_map_modal.html" -type f
grep -n "accounts:save_address" accounts/templates/accounts/modals/address_map_modal.html
grep -n "/account/save_address" accounts/templates/accounts/modals/address_map_modal.html
sudo systemctl restart linkavto
sudo systemctl status linkavto
sudo pkill -f gunicorn
sudo systemctl start linkavto
clear
grep -r "/account/save_address" /opt/linkavto/staticfiles/
rm -rf /opt/linkavto/staticfiles/
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
sudo rm -rf /var/cache/nginx/*
sudo systemctl restart nginx
clear
# На сервере
grep -r "pickup_points.js" /opt/linkavto/accounts/templates/
grep -r "pickup_points_init.js" /opt/linkavto/accounts/templates/
grep -r "address_list_modal.js" /opt/linkavto/accounts/templates/
grep -r "address_list_partial.js" /opt/linkavto/accounts/templates/
clear
ls -lh /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
grep -A 5 "fetch.*save_address" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html | head -20
stat /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
grep -n "pickup_points.js\|pickup_points_init.js" /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
grep -n "address_list_modal.js\|address_list_partial.js" /opt/linkavto/accounts/templates/accounts/dashboard.html
clear
grep -r "save_address" /opt/linkavto/accounts/urls.py
grep -n "app_name\|namespace" /opt/linkavto/accounts/urls.py
cat /opt/linkavto/accounts/urls.py
cat /opt/linkavto/accounts/urls.py | grep -A 2 -B 2 "save_address"
clear
exit
cd /opt/linkavto
source venv/bin/activate
cat /opt/linkavto/accounts/urls.py | grep -A 2 -B 2 "save_address"
clear
cat /opt/linkavto/avtolink/urls.py | grep -i accounts
cat /opt/linkavto/avtolink/urls.py
sudo systemctl restart linkavto
sudo systemctl status linkavto'
sudo systemctl status linkavto
clear
nano /opt/linkavto/avtolink/urls.py
cat /opt/linkavto/avtolink/urls.py | grep -i accounts
sudo systemctl restart linkavto
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
сдуфк
clear
cat /opt/linkavto/avtolink/urls.py | grep -i accounts
cd /opt/linkavto
ource venv/bin/activate
source venv/bin/activate
grep -n "login" /opt/linkavto/accounts/urls.py
path('login/', views.login_view, name='login'),
grep "LOGIN_URL" /opt/linkavto/avtolink/settings.py
grep -A 10 "def save_address" /opt/linkavto/accounts/views.py | head -15
clear
grep -B 5 "def save_address" /opt/linkavto/accounts/views.py | grep -E "@login_required|@require"
nano /opt/linkavto/avtolink/settings.py
rep "LOGIN_URL" /opt/linkavto/avtolink/settings.py
grep "LOGIN_URL" /opt/linkavto/avtolink/settings.py
sudo systemctl restart linkavto
clear
python manage.py shell
nano manage.py 
ckear
python manage.py changepassword admin
sudo systemctl restart linkavto
python manage.py createsuperuser
clear
python manage.py shell
clear
scp "accounts/templates/accounts/dashboard.html" root@89.23.97.97:/opt/linkavto/accounts/templates/accounts/
scp "accounts/templates/accounts/modals/address_list_modal.html" root@89.23.97.97:/opt/linkavto/accounts/templates/accounts/modals/
exit
quit
cd /opt/linkavto
sudo systemctl restart linkavto'
sudo systemctl restart linkavto
exit
cd /opt/linkavto
source venv/bin/activate\
source venv/bin/activate
sudo systemctl restart linkavto
clear
tail -50 logs/gunicorn-error.log
journalctl -u linkavto -n 50 --no-pager
clear
source venv/bin/activate
python manage.py makemigrations accounts
python manage.py migrate accounts
clear
python manage.py shell
clear
exit
cd /opt/linkavto
source venv/bin/activate
grep -n "delivery_type" accounts/models.py
python manage.py makemigrations accounts
python manage.py migrate accounts
python manage.py shell
sudo systemctl restart linkavto
cleaar
clear
cd /opt/linkavto
source venv/bin/activate
clear
grep -n "callbackFunction" accounts/templates/accounts/modals/address_map_modal.html
grep -n "YaNddWidgetPointSelected" accounts/templates/accounts/modals/address_map_modal.html
grep -A 5 "YaNddWidgetPointSelected" accounts/templates/accounts/modals/address_map_modal.html | grep "console.log"
clear
# Открой файл
nano accounts/templates/accounts/modals/address_map_modal.html
clear
find /opt/linkavto -type f -name "*.pyc" -delete
find /opt/linkavto -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
sudo pkill -9 gunicorn
sudo systemctl start linkavto
sudo systemctl status linkavto
# Посмотрим строку 184-220 где должна быть функция initPochtaWidget
sed -n '180,220p' accounts/templates/accounts/modals/address_map_modal.html
# Найдём где начинается функция
grep -n "function initPochtaWidget" accounts/templates/accounts/modals/address_map_modal.html
clear
sed -n '169,230p' accounts/templates/accounts/modals/address_map_modal.html
clear
exot
exit
cd /opt/linkavto
pB-T+h^6NgRJ+J
source venv/bin/activate
journalctl -u linkavto -n 100 --no-pager
python manage.py runserver 0.0.0.0:8000
clear
cd /opt/linkavto
source venv/bin/activate
clear
sudo pkill -9 gunicorn
sudo systemctl start linkavto
exit
cd /opt/linkavto
source venv/bin/activate
sudo pkill -9 gunicorn && sleep 2 && sudo systemctl start linkavto
clear
exit
cd /opt/linkavto
source venv/bin/activate
clear
sudo pkill -9 gunicorn
sudo systemctl start linkavto
sudo systemctl status linkavto
clear
exit
cd /opt/linkavto
source venv/bin/activate
cleat
clear
python manage.py makemigrations accounts
python manage.py migrate
sudo systemctl restart linkavto
sudo systemctl status linkavto
clear
sudo -u postgres psql linkavto_db
postgres psql linkavto_db
-u postgres psql linkavto_db
cat avtolink/settings.py | grep -A 10 "DATABASES"
clear
cat avtolink/settings.py | grep -A 10 "DATABASES"
clear
sqlite3 db.sqlite3 "PRAGMA table_info(accounts_address);"
apt install sqlite3
sqlite3 db.sqlite3 "PRAGMA table_info(accounts_address);"
python manage.py dbshell
clear
journalctl -u linkavto -n 50 --no-pager | grep -A 20 "ERROR"
journalctl -u linkavto -n 30 --no-pager
clear
find /opt/linkavto -name "*.sqlite3" -type f
find /root -name "*.sqlite3" -type f 2>/dev/null
cat gunicorn.conf.py
cat /etc/systemd/system/linkavto.service
clear
find /opt/linkavto -name "production.py" -type f
ls -la avtolink/settings/
python manage.py shell
clear
sudo pkill -9 gunicorn
sudo systemctl start linkavto
sudo systemctl status linkavto
ps aux | grep gunicorn
clear
journalctl -u linkavto -n 50 --no-pager | tail -30
cat accounts/models.py | grep -A 30 "class Address"
clear
find /opt/linkavto -type f -name "*.pyc" -delete
find /opt/linkavto -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
sudo systemctl restart linkavto
sudo systemctl status linkavto
cat avtolink/settings/production.py | grep -A 10 "DATABASES"
clear
sudo -u postgres psql avtolink_django
# Указать production settings
python manage.py migrate --settings=avtolink.settings.production
clear
cd /opt/linkavto && cat accounts/templates/accounts/modals/address_map_modal.html | grep -A 5 'selectedPickupPoint.address' | head -20
clear
cat accounts/templates/accounts/modals/address_map_modal.html | grep -B 30 -A 5 "initPochtaWidget"
grep -n "addressInput.disabled = false" accounts/templates/accounts/modals/address_map_modal.html
python manage.py migrate --settings=avtolink.settings.production
clear
cat accounts/templates/accounts/modals/address_map_modal.html | grep -A 50 "function initPochtaWidget" | head -60
cat accounts/templates/accounts/modals/address_map_modal.html | grep -A 50 "function initYandexDeliveryWidget" | head -60
clear
cat accounts/templates/accounts/modals/address_map_modal.html | grep -A 30 "YaNddWidgetPointSelected"
cat accounts/templates/accounts/modals/address_map_modal.html | grep -B 5 -A 15 "addressInput.disabled = true"
clear
ls -lh accounts/templates/accounts/modals/address_map_modal.html
python manage.py collectstatic --noinput
sudo systemctl restart linkavto
clear
ls -lh accounts/templates/accounts/modals/address_map_modal.html
sudo pkill -9 gunicorn
sudo systemctl start linkavto
sudo systemctl status linkavto
clear
cd /opt/linkavto
source venv/bin/activate
clear
sudo pkill -9 gunicorn && sleep 2 && sudo systemctl start linkavto
find /opt/linkavto -type f -name "*.pyc" -delete
ls -lh /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html
head -200 /opt/linkavto/accounts/templates/accounts/modals/address_map_modal.html | tail -50
sudo systemctl stop linkavto
sudo systemctl start linkavto
sudo systemctl status linkavto
clear
exit
cd /opt/linkavto
source venv/bin/activate
find /opt/linkavto -type f -name "*.pyc" -delete
find /opt/linkavto -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
sudo systemctl stop linkavto
sudo systemctl start linkavto
sudo systemctl status linkavto
clear
exit
sudo pkill -9 gunicorn && sleep 2 && sudo systemctl start linkavto
cd /opt/linkavto
udo pkill -9 gunicorn && sleep 2 && sudo systemctl start linkavto && sudo systemctl status linkavto --no-pager
sudo pkill -9 gunicorn && sleep 2 && sudo systemctl start linkavto && sudo systemctl status linkavto --no-pager
clear
source venv/bin/activate
sudo pkill -9 gunicorn && sleep 2 && sudo systemctl start linkavto && sudo systemctl status linkavto --no-pager
grep -A 5 'window.addres = function' accounts/templates/accounts/modals/address_map_modal.html | head -10
clear
sudo pkill -9 gunicorn && sleep 2 && sudo systemctl start linkavto
clear
exit
cd /opt/linkavto
source venv/bin/activate
clear
systemctl status
ckear
clear
udo journalctl -u linkavto -n 30 --no-pager
clear
sudo journalctl -u linkavto -n 30 --no-pager
grep -A 5 'Error\|Exception\|Traceback
sudo journalctl -u linkavto -n 30 --no-pager | grep -A 5 'Error\|Exception\|Traceback
rep -n 'sellers' shop/templates/shop/base.html
grep -n 'sellers' shop/templates/shop/base.html
clear
grep -r \"sellers:\" --include='*.html' shop/templates/ accounts/templates/
echo '=== ПОИСК sellers В PYTHON ===' && grep -r 'sellers' --include='*.py' . | grep -v '.pyc' | grep -v 'migrations' | head -20
clear
echo '=== 1. ОЧИСТКА ВСЕХ КЕШЕЙ ===' && find . -type f -name '*.pyc' -delete && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && echo '✅ Python кеш удалён' && echo '' && echo '=== 2. ОСТАНОВКА ВСЕХ GUNICORN ===' && ps aux | grep gunicorn | grep -v grep && sudo killall -9 gunicorn 2>/dev/null || true && sleep 2 && echo '✅ Все процессы убиты' && echo '' && echo '=== 3. ЗАПУСК СЕРВИСА ===' && sudo systemctl start linkavto && sleep 3 && sudo systemctl status linkavto --no-pager | head -12
sudo journalctl -u linkavto --since '1 minute ago' --no-pager | tail -40
(venv) root@5746229-mp55247:/opt/linkavto# sudo journalctl -u linkavto --since '1 minute ago' --no-pager | tail -40
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/shortcuts.py", line 25, in render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     content = loader.render_to_string(template_name, context, request, using=using)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/loader.py", line 62, in render_to_string
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return template.render(context, request)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/backends/django.py", line 107, in render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return self.template.render(context)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/base.py", line 171, in render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return self._render(context)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/base.py", line 163, in _render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return self.nodelist.render(context)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/base.py", line 1008, in render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return SafeString("".join([node.render_annotated(context) for node in self]))
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/base.py", line 969, in render_annotated
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return self.render(context)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/loader_tags.py", line 159, in render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return compiled_parent._render(context)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/base.py", line 163, in _render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return self.nodelist.render(context)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/base.py", line 1008, in render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return SafeString("".join([node.render_annotated(context) for node in self]))
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/base.py", line 969, in render_annotated
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     return self.render(context)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:            ^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/template/defaulttags.py", line 480, in render
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     url = reverse(view_name, args=args, kwargs=kwargs, current_app=current_app)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:   File "/opt/linkavto/venv/lib/python3.12/site-packages/django/urls/base.py", line 82, in reverse
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]:     raise NoReverseMatch("%s is not a registered namespace" % key)
Nov 26 12:11:40 5746229-mp55247 gunicorn[2079151]: django.urls.exceptions.NoReverseMatch: 'sellers' is not a registered namespace
(venv) root@5746229-mp55247:/opt
clear
grep -C 3 'sellers' shop/templates/shop/base.html
clear
find . -name 'base.html' -type f | grep -v venv
grep -r 'sellers:' . --include='*.html' 2>/dev/null | grep -v '.pyc'
cho '=== ПОЛНЫЙ РЕСТАРТ ===' && sudo systemctl stop linkavto && sleep 2 && sudo killall -9 gunicorn 2>/dev/null || true && sleep 1 && ps aux | grep gunicorn | grep -v grep && echo 'Нет процессов' || echo 'Есть процессы!' && sudo systemctl daemon-reload && sudo systemctl start linkavto && sleep 3 && echo '✅ Запущено' && curl -s http://localhost:8000/ | head -5
clear
curl -H 'Host: linkavto.ru' http://localhost:8000/ 2>&1 | head -20
grep -n 'sellers' shop/templates/shop/index.html
clear
echo '=== УДАЛЕНИЕ ВСЕХ КЕШЕЙ ШАБЛОНОВ ===' && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && find . -name '*.pyc' -delete && find . -name '*.pyo' -delete && echo '✅ Удалено' && echo '' && echo '=== ИЗМЕНЯЕМ TIMESTAMP ШАБЛОНА ===' && touch shop/templates/shop/base.html && ls -l shop/templates/shop/base.html && echo '' && echo '=== ПЕРЕЗАПУСК ===' && sudo systemctl restart linkavto && sleep 3 && sudo systemctl status linkavto --no-pager | head -8
systemctl status
curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -30
clear
sudo journalctl -u linkavto --since '12:18:33' --no-pager | grep -B 2 -A 2 'NoReverseMatch\|sellers' | head -30
clear
d5sum shop/templates/shop/base.html
md5sum shop/templates/shop/base.html
clear
sudo journalctl -u linkavto --since '12:18:40' --no-pager | grep -A 50 'Traceback' | head -60
find staticfiles -name 'base.html' 2>/dev/null
echo 'Creating sellers stub' && mkdir -p sellers && echo 'from django.urls import path

app_name = \"sellers\"

urlpatterns = [
    # Stub for sellers namespace
]' > sellers/urls.py && echo 'urlpatterns = []' > sellers/__init__.py && cat sellers/urls.py
clear
echo '# Sellers stub app' > sellers/views.py && echo 'from django.apps import AppConfig

class SellersConfig(AppConfig):
    default_auto_field = \"django.db.models.BigAutoField\"
    name = \"sellers\"' > sellers/apps.py && echo '=== ДОБАВЛЯЮ В settings.py ===' && grep -q 'sellers' avtolink/settings.py || sed -i \"/INSTALLED_APPS = \\[/a\\    'sellers',\" avtolink/settings.py && echo '✅ Добавлено в INSTALLED_APPS' && echo '' && echo '=== ДОБАВЛЯЮ В urls.py ===' && grep -q 'sellers' avtolink/urls.py || sed -i \"/urlpatterns = \\[/a\\    path('sellers/', include('sellers.urls', namespace='sellers')),\" avtolink/urls.py && echo '✅ Добавлено в urls.py'
clear
echo '# Sellers stub app' > views.py && cat > apps.py << 'EOF'
from django.apps import AppConfig

class SellersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sellers'
EOF

echo '✅ Файлы созданы' && ls -la
clear
mv apps.py views.py sellers/ && ls -la sellers/
echo '=== ПРОВЕРЯЕМ settings.py ===' && grep -n INSTALLED_APPS avtolink/settings.py | head -15
clear
sed -n '32,50p' avtolink/settings.py
clear
sed -i \"/search.apps.SearchConfig/a\\    'sellers',\" avtolink/settings.py && echo '✅ sellers добавлен в INSTALLED_APPS' && grep -A 2 'search.apps.SearchConfig' avtolink/settings.py
clear
sed -i '/search.apps.SearchConfig/a\    '\"'sellers'\"',' avtolink/settings.py && echo '✅ sellers добавлен' && grep -A 2 SearchConfig avtolink/settings.py
grep -n 'urlpatterns' avtolink/urls.py | head -3
clear
grep -n '^urlpatterns' avtolink/urls.py
clear
ed -n '22,35p' avtolink/urls.py
sed -n '22,35p' avtolink/urls.py
clear
sed -i \"/path('search\//a\\    path('sellers/', include('sellers.urls', namespace='sellers')),\" avtolink/urls.py && echo '✅ sellers добавлен в urls' && sed -n '22,35p' avtolink/urls.py
at >> avtolink/urls_tmp.txt << 'EOF'
    path('sellers/', include('sellers.urls', namespace='sellers')),
EOF

sed -i \"/path('search'/r avtolink/urls_tmp.txt\" avtolink/urls.py && rm avtolink/urls_tmp.txt && echo '✅ sellers добавлен' && sed -n '22,35p' avtolink/urls.py
clear
cat >> avtolink/urls_tmp.txt << 'EOF'
    path('sellers/', include('sellers.urls', namespace='sellers')),
EOF

sed -i \"/path('search'/r avtolink/urls_tmp.txt\" avtolink/urls.py && rm avtolink/urls_tmp.txt && echo '✅ sellers добавлен' && sed -n '22,35p' avtolink/urls.py
clear
python3 -c \"
with open('avtolink/urls.py', 'r') as f:
for i, line in enumerate(lines):
with open('avtolink/urls.py', 'w') as f:
print('✅ Добавлено')
\" && sed -n '22,35p' avtolink/urls.py
clear
exit
clear
cd /opt/linkavto
source venv/bin/activate
sudo journalctl -u linkavto --since '12:55' --no-pager
tail -f /var/log/nginx/access.log
clear
echo '=== ОТКАТ ИЗМЕНЕНИЙ ===' && sed -i '/\"sellers\",/d' avtolink/settings.py && sed -i \"/path('sellers'/d\" avtolink/urls.py && rm -rf sellers/ && echo '✅ sellers удалён' && echo '' && echo '=== ПЕРЕЗАПУСК ===' && sudo systemctl restart linkavto && sleep 3 && curl -H 'Host: linkavto.ru' http://localhost:8000/ 2>&1 | head -20
python3 << 'EOF'
# Удаляем sellers из settings.py
with open('avtolink/settings.py', 'r') as f:
    lines = f.readlines()
with open('avtolink/settings.py', 'w') as f:
    for line in lines:
        if 'sellers' not in line:
            f.write(line)

# Удаляем sellers из urls.py  
with open('avtolink/urls.py', 'r') as f:
    lines = f.readlines()
with open('avtolink/urls.py', 'w') as f:
    for line in lines:
        if 'sellers' not in line:
            f.write(line)

print('✅ Откат завершён')
EOF

rm -rf sellers/ && sudo systemctl restart linkavto && sleep 3 && echo '✅ Сервис перезапущен'"

rm -rf sellers/ && sudo systemctl restart linkavto && sleep 3 && echo '✅ Перезапущено' && curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -20
sudo journalctl -u linkavto --since '13:00' --no-pager | tail -40
clear
grep -n 'sellers' shop/templates/shop/base.html
clear
ed -i '1981d' shop/templates/shop/base.html && echo '✅ Строка удалена' && grep -C 2 -n 'Стать продавцом' shop/templates/shop/base.html || echo 'Строка не найдена' && sudo systemctl restart linkavto && sleep 3 && curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -20
sed -i '1981d' shop/templates/shop/base.html && echo '✅ Строка удалена' && grep -C 2 -n 'Стать продавцом' shop/templates/shop/base.html || echo 'Строка не найдена' && sudo systemctl restart linkavto && sleep 3 && curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -20"
clear
sed -i '1981d' shop/templates/shop/base.html && echo '✅ Строка удалена' && sudo systemctl restart linkavto && sleep 3 && echo '✅ Перезапущено' && curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -15"

clear
sed -i '1981d' shop/templates/shop/base.html && echo '✅ Строка удалена' && sudo systemctl restart linkavto && sleep 3 && echo '✅ Перезапущено' && curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -15
clear
exit
cd /opt/linkavto
source venv/bin/activate
sed -i '1981d' shop/templates/shop/base.html && echo '✅ Строка удалена' && sudo systemctl restart linkavto && sleep 3 && echo '✅ Перезапущено' && curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -15
cd /opt/linkavto
source venv/bin/activate
clear
sed -i '1981d' shop/templates/shop/base.html && echo '✅ Строка удалена' && sudo systemctl restart linkavto && sleep 3 && echo '✅ Перезапущено' && curl -H 'Host: linkavto.ru' -s http://localhost:8000/ | head -15
cd /opt/linkavto
source venv/bin/activate
clear
echo '=== 1. ОЧИСТКА ВСЕХ КЕШЕЙ ===' && find . -type f -name '*.pyc' -delete && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && echo '✅ Python кеш удалён' && echo '' && echo '=== 2. ОСТАНОВКА ВСЕХ GUNICORN ===' && ps aux | grep gunicorn | grep -v grep && sudo killall -9 gunicorn 2>/dev/null || true && sleep 2 && echo '✅ Все процессы убиты' && echo '' && echo '=== 3. ЗАПУСК СЕРВИСА ===' && sudo systemctl start linkavto && sleep 3 && sudo systemctl status linkavto --no-pager | head -12
cd /opt/linkavto
source venv/bin/activate
systemctl status postgresql
systemctl status gunicorn_avtolink
systemctl status nginx
sudo -u postgres psql -d avtolink_django -c "\dt"
git pull origin main
ls -la /opt/linkavto/
git init
git add .
git config --global --add safe.directory /opt/linkavto
git commit -m "Сохранение текущего состояния сервера"
git remote add origin git@gitlab.com:ilyafeoktistov005/linkavto.git
git fetch origin
git pull origin main
git remote add origin git@gitlab.com:ilyafeoktistov005/linkavto.git
git fetch origin
cd /opt/linkavto
source venv/bin/activate
git pull origin main
ls -la ~/.ssh/
ssh-keygen -t ed25519 -C "gitlab@linkavto.ru"
cat ~/.ssh/id_ed25519.pub
ssh -T git@gitlab.com
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn_avtolink
systemctl restart nginx
curl -I https://linkavto.ru
reboot now
cd /opt/linkavto
source venv/bin/activate
systemctl restart gunicorn_avtolink
systemctl restart nginx
systemctl status postgresql
systemctl status nginx
git branch
git log -1 --oneline
git status
git branch -a
git checkout main
git branch
git status
git log -1 --oneline
mkdir /tmp/linkavto_backup_$(date +%Y%m%d)
cp -r /opt/linkavto/* /tmp/linkavto_backup_$(date +%Y%m%d)/ 2>/dev/null || true
find . -maxdepth 1 ! -name '.git' ! -name '.' -exec rm -rf {} \;
ls -la
git checkout main
git branch
git status
git log -1 --oneline
cp /tmp/linkavto_backup_*/avtolink/settings.py /opt/linkavto/avtolink/ 2>/dev/null || echo "Settings not found in backup"
cp -r /tmp/linkavto_backup_*/media/* /opt/linkavto/media/ 2>/dev/null || echo "Media not found in backup"
pip install -r requirements.txt
python manage.py collectstatic --noinput
git pull origin main
pip install -r requirements.txt
pip install django djangorestframework psycopg2-binary gunicorn
python -c "import django; print(django.__version__)"
which python
which pip
pip install django==4.2
apt install
python3-xyz
pip install django==4.2
pip install djangorestframework
echo $VIRTUAL_ENV
source venv/bin/activate
which pip
which python
mv /opt/linkavto /opt/linkavto_backup_$(date +%Y%m%d)
cd /opt
git clone git@gitlab.com:ilyafeoktistov005/linkavto.git
cp /opt/linkavto_backup*/avtolink/settings.py /opt/linkavto/avtolink/ 2>/dev/null || true
cd /opt/linkavto
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
git branch
git log -1 --oneline
python manage.py collectstatic --noinput
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn_avtolink
systemctl restart nginx
curl -I https://linkavto.ru
reboot now
cd /opt/linkavto
source venv/bin/activate
curl -I https://linkavto.ru
journalctl -u gunicorn_avtolink -n 30 --no-pager
tail -f debug.log
systemctl status gunicorn_avtolink
ls -la /opt/linkavto/linkavto.sock
systemctl restart gunicorn_avtolink
sleep 5
nano /etc/systemd/system/gunicorn_avtolink.service
nano /etc/systemd/system/gunicorn_linkavto.service
systemctl status nginx
systemctl status gunicorn_avtolink
nano /etc/systemd/system/gunicorn_avtolink.service
chmod 644 /etc/systemd/system/gunicorn_avtolink.service
systemctl daemon-reload
systemctl start gunicorn_avtolink
systemctl enable gunicorn_avtolink
systemctl status gunicorn_avtolink
ls -la /opt/linkavto/linkavto.sock
systemctl restart gunicorn_avtolink
journalctl -u gunicorn_avtolink -n 20 --no-pager
curl -I https://linkavto.ru
ls -la /opt/linkavto/venv/bin/gunicorn
/opt/linkavto/venv/bin/python --version
/opt/linkavto/venv/bin/gunicorn --version
pip install gunicorn
which gunicorn
gunicorn --version
nano /etc/systemd/system/gunicorn_avtolink.service
systemctl daemon-reload
systemctl restart gunicorn_avtolink
systemctl status gunicorn_avtolink
systemctl status nginx
systemctl status gunicorn_avtolink
curl -I https://linkavto.ru
ls -la /opt/linkavto/linkavto.sock
journalctl -u gunicorn_avtolink -n 10 --no-pager
pip install gunicorn
which gunicorn
gunicorn --version
nano /etc/systemd/system/gunicorn_avtolink.service
ls -la /opt/linkavto/avtolink/wsgi.py
head -20 /opt/linkavto/avtolink/wsgi.py
systemctl stop gunicorn_avtolink
gunicorn --workers 1 --bind unix:/opt/linkavto/linkavto.sock --log-level debug --error-logfile /tmp/gunicorn_error.log avtolink.wsgi:application
ls -la /opt/linkavto/linkavto.sock
curl --unix-socket /opt/linkavto/linkavto.sock http://localhost
cat /tmp/gunicorn_error.log
systemctl restart gunicorn_avtolink
systemctl status gunicorn_avtolink
nano /etc/systemd/system/gunicorn_avtolink.service
/opt/linkavto/venv/bin/gunicorn --workers 2 --threads 2 --worker-class=gthread --bind unix:/opt/linkavto/linkavto.sock avtolink.wsgi:application
pip install rapidfuzz
python -c "import rapidfuzz; print('rapidfuzz version:', rapidfuzz.__version__)"
pip install -r requirements.txt
ls -la /opt/linkavto/requirements.txt
cat /opt/linkavto/requirements.txt
pip install -r requirements.txt
python manage.py check
pip install rest_framework
pip install djangorestframework django-filter django-cors-headers
pip install rapidfuzz
python manage.py check
pip install pandas
python manage.py check
systemctl restart gunicorn_avtolink
systemctl daemon-reload
systemctl restart gunicorn_avtolink
systemctl restart nginx
curl -I https://linkavto.ru
cat /opt/linkavto/requirements.txt
pip install -r requirements.txt
python manage.py check
python manage.py showmigrations
systemctl stop gunicorn_avtolink
ls -la /opt/linkavto/linkavto.sock
systemctl stop gunicorn_avtolink
gunicorn --workers 1 --bind 0.0.0.0:8000 --log-level debug avtolink.wsgi:application
systemctl status gunicorn_avtolink
ls -la /opt/linkavto/linkavto.sock
nano /etc/systemd/system/gunicorn_avtolink.service
journalctl -u gunicorn_avtolink -n 30 --no-pager
ls -la venv/
python --version
python -c "import django; print(django.get_version())"
pip install -r requirements.txt
pip install gunicorn
ls -la
ls -la manage.py
ls -la avtolink/settings.py
gunicorn --workers 1 --bind 0.0.0.0:8000 --log-level debug avtolink.wsgi:application
python manage.py showmigrations
python manage.py migrate
python manage.py createsuperuser
nano /opt/linkavto/avtolink/settings.py
gunicorn --workers 1 --bind 0.0.0.0:8000 --log-level debug avtolink.wsgi:application
nano /opt/linkavto/avtolink/settings.py
gunicorn --workers 1 --bind 0.0.0.0:8000 --log-level debug avtolink.wsgi:application
find /opt/linkavto -name "*.db" -o -name "*.sqlite3" -delete
find /opt/linkavto -name "db.sqlite3" -delete
systemctl status postgresql
sudo -u postgres psql -c "\l" | grep avtolink_django
python manage.py shell -c "
from django.conf import settings
print('Database engine:', settings.DATABASES['default']['ENGINE'])
print('Database name:', settings.DATABASES['default']['NAME'])
"
python manage.py migrate --run-syncdb
find /opt/linkavto -name "*.db" -o -name "*.sqlite3" -delete
gunicorn --workers 1 --bind 0.0.0.0:8000 --log-level debug avtolink.wsgi:application
systemctl restart gunicorn_avtolink
systemctl restart nginx
systemctl status postgresql
systemctl status gunicorn_avtolink
systemctl status nginx
ls -la /opt/linkavto/linkavto.sock
journalctl -u gunicorn_avtolink -n 30 --no-pager
ls -la /opt/linkavto/linkavto.sock
chown www-data:www-data /opt/linkavto/linkavto.sock
chmod 660 /opt/linkavto/linkavto.sock
nano /etc/nginx/sites-available/avtolink.conf
nano /etc/nginx/sites-available/linkavto.conf
source venv/bin/activate
pip install gunicorn
pip install -r requirements.txt
pip list | grep gunicorn
python -c "import gunicorn; print('Gunicorn version:', gunicorn.__version__)"
apt update
apt install -y dpkg-dev gcc python3-dev
systemctl stop gunicorn_avtolink
rm -f /opt/linkavto/linkavto.sock
systemctl start gunicorn_avtolink
systemctl status gunicorn_avtolink
sleep 5
ls -la /opt/linkavto/linkavto.sock
curl --unix-socket /opt/linkavto/linkavto.sock http://localhost
systemctl stop gunicorn_avtolink
gunicorn --workers 1 --bind unix:/opt/linkavto/linkavto.sock --log-level debug avtolink.wsgi:application
pip list
curl -I https://linkavto.ru
rm -rf venv
python3 -m venv venv
pip install -r requirements.txt
pip install gunicorn
systemctl restart gunicorn_avtolink
curl -I https://linkavto.ru
journalctl -u gunicorn_avtolink -n 10 --no-pager
pip install rapidfuzz
pip install -r requirements.txt
pip list | grep rapidfuzz
python -c "import rapidfuzz; print('rapidfuzz version:', rapidfuzz.__version__)"
systemctl restart gunicorn_avtolink
systemctl status gunicorn_avtolink
journalctl -u gunicorn_avtolink -n 10 --no-pager
systemctl restart gunicorn_avtolink
systemctl status gunicorn_avtolink
ls -la /opt/linkavto/linkavto.sock
curl --unix-socket /opt/linkavto/linkavto.sock http://localhost
curl -I https://linkavto.ru
journalctl -u gunicorn_avtolink -n 20 --since "1 minute ago"
nano /opt/linkavto/avtolink/settings.py
systemctl restart gunicorn_avtolink
curl --unix-socket /opt/linkavto/linkavto.sock http://localhost
python manage.py check --database default
pip install rest_framework
pip install djangorestframework
pip install -r requirements.txt
python manage.py check --database default
pip install pandas
python manage.py check --database default
systemctl restart gunicorn_avtolink
systemctl restart nginx
systemctl status postgresql
systemctl status gunicorn_avtolink
systemctl status nginx
ls -la /opt/linkavto/linkavto.sock
nano /etc/nginx/sites-available/avtolink.conf
nano /etc/nginx/sites-available/linkavto.conf
journalctl -u gunicorn_avtolink -n 20 --no-pager
lsof /opt/linkavto/linkavto.sock
python manage.py runserver 0.0.0.0:8000
curl -I http://localhost:8000
systemctl stop gunicorn_avtolink
python manage.py migrate
python manage.py showmigrations
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
curl -I http://localhost:8000
systemctl daemon-reload
systemctl start gunicorn_avtolink
systemctl restart nginx
systemctl status gunicorn_avtolink
systemctl status nginx
curl -I http://localhost
curl -I https://linkavto.ru
journalctl -u gunicorn_avtolink -n 10
tail -f /var/log/nginx/error.log
lsof /opt/linkavto/linkavto.sock
journalctl -u gunicorn_avtolink -n 20 --no-pager
python manage.py runserver 0.0.0.0:8000
htop
tail -f /var/log/nginx/error.log
ps -aux
tail -n 100 /var/log/nginx/linkavto.ru.error.log
tail -n 100 /var/log/nginx/linkavto.ru.error.log -f
ls /etc/systemd/system/
journalctl -u gunicorn_avtolink.service -e
source /opt/linkavto/venv/bin/activate
pip install rapidfuzz
exit
cd /opt/linkavto
source venv/bin/activate
curl -I https://linkavto.ru
tail -f debug.log
cd /opt/linkavto
source venv/bin/activate
nano /opt/linkavto/avtolink/settings.py
tail -f debug.log
cd /opt/linkavto
source venv/bin/activate
tail -f debug.log
nano /opt/linkavto/avtolink/settings.py
tail -f debug.log
nano /opt/linkavto/avtolink/settings.py
tail -f debug.log
nano /opt/linkavto/avtolink/settings.py
python -m py_compile avtolink/settings.py
sudo -u postgres psql -c "\l" | grep avtolink_django
python manage.py check --database default
python manage.py migrate
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
curl -I http://localhost:8000
sudo -u postgres psql -d avtolink_django -c "\dt"
sudo -u postgres psql -d avtolink_django -c "SELECT COUNT(*) FROM auth_user;"
sudo -u postgres psql -d avtolink_django -c "SELECT COUNT(*) FROM shop_product;"
systemctl restart gunicorn_avtolink
systemctl daemon-reload
cd /opt/linkavto
source venv/bin/activate
python manage.py createsuperuser
cat /etc/systemd/system/gunicorn_avtolink.service
ls -ld /opt/linkavto/venv/lib/python3.12/site-packages/rapidfuzz
sudo -u www-data /opt/linkavto/venv/bin/python -c "import rapidfuzz; print('Success')"
systemctl restart gunicorn_avtolink.service
systemctl status gunicorn_avtolink.service
journalctl -u gunicorn_avtolink.service -e
systemctl status gunicorn_avtolink.service
tail -n 100 /var/log/nginx/linkavto.ru.error.log -f
netstat -tunlp | grep 8000
ss -lntu
nano /etc/nginx/sites-enabled/linkavto.ru 
nginx -t
systemctl reload nginx
cat /opt/linkavto/avtolink/set
ls -ld /opt/linkavto/db.sqlite3 
ls -ld /opt/linkavto/
cat /etc/systemd/system/gunicorn_avtolink.service
nano /etc/systemd/system/gunicorn_avtolink.service
systemctl daemon-reload
systemctl restart gunicorn_avtolink.service 
tail -n 100 /var/log/nginx/linkavto.ru.error.log
tail -n 100 /var/log/nginx/linkavto.ru.error.log -f
chown -R www-data:www-data /opt/linkavto
chmod 775 /opt/linkavto
chmod 664 /opt/linkavto/db.sqlite3
systemctl restart gunicorn_avtolink.service 
journalctl -u gunicorn_avtolink.service -e
systemctl restart gunicorn_avtolink.service 
journalctl -u gunicorn_avtolink.service -e
tail -n 100 /var/log/nginx/linkavto.ru.error.log -f
ls -ld /opt/linkavto/staticfiles/js/
source /opt/linkavto/venv/bin/activate
ls
cat DATABASE_STRUCTURE.md 
ls
cat debug.log 
cat debug.log -f
tail -n 100 debug.log -f
ды
ls
python manage.py showmigrations
cat .env 
ls avtolink
cat avtolink/settings.py 
ls shop/
ls
cd avtolink/
ls
cat settings_backup.py 
cat settings/production.py 
ufw status 
pg_dump -U avtolink_django -h localhost avtolink_django > backup_$(date +%F).sql
ls
cd ../
python manage.py migrate
source /opt/linkavto/venv/bin/activate
python manage.py migrate
python manage.py showmigrations
cat debug.log 
ls
ls -l
ls -l db.sqlite3 
psql -U avtolink_django -d avtolink_django
sudo -u postgres psql -d avtolink_django
sqlite3 db.sqlite3 "SELECT count(*) FROM shop_product;"
ды
ls
ls avtolink
ls shop/
nano avtolink/settings/base.py 
nano avtolink/settings/development.py 
ls
nano gunicorn.conf.py 
nano production_db.json 
cd /opt/linkavto
source venv/bin/activate
sudo -u postgres pg_dump avtolink_django > /opt/linkavto/avtolink_django_backup_$(date +%Y%m%d).sql
ls -lh /opt/linkavto/*.sql /opt/linkavto/*.dump 2>/dev/null
sudo -u postgres psql -d avtolink_django -c "\dt"
sudo -u postgres psql -d avtolink_django -c "SELECT schemaname,tablename FROM pg_tables WHERE schemaname = 'public';"
sudo -u postgres psql -d avtolink_django -c "SELECT pg_size_pretty(pg_database_size('avtolink_django'));"
crontab -e
nano /opt/linkavto/backup_database.sh
chmod +x /opt/linkavto/backup_database.sh
cd /opt/linkavto
source venv/bin/activate
ps aux | grep python | grep -v grep
sudo systemctl list-units --type=service | grep -E "linkavto|django|gunicorn"
cd /opt/linkavto && source venv/bin/activate && python manage.py migrate --settings=avtolink.settings.production
cd /opt/linkavto && source venv/bin/activate && python manage.py collectstatic --noinput --settings=avtolink.settings.production
sudo systemctl restart gunicorn_avtolink.service && sudo systemctl restart linkavto.service && sudo systemctl status gunicorn_avtolink.service
sudo systemctl status linkavto.service
sudo journalctl -xeu linkavto.service -n 50 --no-pager
sudo systemctl stop linkavto.service && sudo systemctl restart gunicorn_avtolink.service && sudo systemctl restart nginx && sudo systemctl status gunicorn_avtolink.service
cd /opt/linkavto
source venv/bin/activate
ython manage.py runserver --settings=avtolink.settings.development
clear
python manage.py migrate --settings=avtolink.settings.production
python manage.py collectstatic --noinput --settings=avtolink.settings.production
sudo systemctl restart gunicorn
sudo systemctl restart django
sudo systemctl restart uwsgi'
sudo systemctl restart uwsgi
sudo systemctl restart
