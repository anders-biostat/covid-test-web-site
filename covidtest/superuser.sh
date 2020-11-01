#!/bin/sh
echo "Create Superuser if not existing"
cat <<EOF | python manage.py shell
from django.contrib.auth import get_user_model

User = get_user_model()  # get the currently active user model,

User.objects.filter(username='$DJANGO_ADMIN_USER').exists() or \
    User.objects.create_superuser('$DJANGO_ADMIN_USER', '$DJANGO_ADMIN_EMAIL', '$DJANGO_ADMIN_PASSWORD')
EOF

