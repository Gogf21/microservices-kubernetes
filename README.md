
═══════════════════════════════════════════════════════════════════════════════
1. ЗАПУСК MINIKUBE
═══════════════════════════════════════════════════════════════════════════════

minikube start
minikube addons enable ingress
eval $(minikube docker-env)

═══════════════════════════════════════════════════════════════════════════════
2. СБОРКА ОБРАЗОВ
═══════════════════════════════════════════════════════════════════════════════

cd ~/kuber/exam-kyznetsov/services/auth-service
docker build -t auth-service:latest .

cd ~/kuber/exam-kyznetsov/services/profile-service
docker build -t profile-service:latest .

cd ~/kuber/exam-kyznetsov/services/notification-service
docker build -t notification-service:latest .

═══════════════════════════════════════════════════════════════════════════════
3. УСТАНОВКА HELM
═══════════════════════════════════════════════════════════════════════════════

cd ~/kuber/exam-kyznetsov/user-management-chart
helm install user-management . -n exam-kyznetsov --create-namespace -f values-dev.yaml

# Обновление
helm upgrade --install user-management . -n exam-kyznetsov -f values-dev.yaml

# Удаление
helm uninstall user-management -n exam-kyznetsov
kubectl delete all --all -n exam-kyznetsov
kubectl delete pvc --all -n exam-kyznetsov
kubectl delete namespace exam-kyznetsov

═══════════════════════════════════════════════════════════════════════════════
4. ПРОВЕРКА РЕСУРСОВ
═══════════════════════════════════════════════════════════════════════════════

kubectl get pods -n exam-kyznetsov
kubectl get svc -n exam-kyznetsov
kubectl get ingress -n exam-kyznetsov
kubectl get pvc -n exam-kyznetsov
kubectl get jobs -n exam-kyznetsov
kubectl get cronjobs -n exam-kyznetsov
kubectl get configmap -n exam-kyznetsov
kubectl get secret -n exam-kyznetsov

═══════════════════════════════════════════════════════════════════════════════
5. LOGI
═══════════════════════════════════════════════════════════════════════════════

# Auth-service
kubectl logs -n exam-kyznetsov deployment/auth-service --tail=30

# Profile-service
kubectl logs -n exam-kyznetsov deployment/profile-service --tail=30

# Notification-service
kubectl logs -n exam-kyznetsov deployment/notification-service --tail=30

# CronJob (последний запуск)
JOB=$(kubectl get jobs -n exam-kyznetsov -o name | grep log-cronjob | head -1)
kubectl logs -n exam-kyznetsov $JOB

═══════════════════════════════════════════════════════════════════════════════
6. API ТЕСТЫ
═══════════════════════════════════════════════════════════════════════════════

# 6.1 Получить токен
TOKEN=$(curl -s -X POST http://$(minikube ip):30082/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')
echo "Токен: $TOKEN"

# 6.2 Профиль
curl -s -k https://app-06.example.com/api/profile \
  -H "Host: app-06.example.com" \
  --resolve "app-06.example.com:443:$(minikube ip)" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 6.3 Уведомление (через порт-форвард)
kubectl port-forward -n exam-kyznetsov service/notification-service 8081:8081 > /dev/null 2>&1 &
sleep 2
curl -s -X POST http://localhost:8081/api/notify \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "message": "Тест"}' | jq .
pkill -f "port-forward.*notification" 2>/dev/null

# 6.4 История уведомлений
kubectl port-forward -n exam-kyznetsov service/notification-service 8081:8081 > /dev/null 2>&1 &
sleep 2
curl -s http://localhost:8081/api/notifications | jq .
pkill -f "port-forward.*notification" 2>/dev/null

# 6.5 Health checks
curl -s http://$(minikube ip):30082/health | jq .
curl -s -k https://app-06.example.com/health -H "Host: app-06.example.com" --resolve "app-06.example.com:443:$(minikube ip)" | jq .

═══════════════════════════════════════════════════════════════════════════════
7. ДОСТУП В БРАУЗЕРЕ
═══════════════════════════════════════════════════════════════════════════════

# NodePort (работает сразу)
http://$(minikube ip):30082/

# Ingress (нужно добавить в /etc/hosts)
echo "$(minikube ip) app-06.example.com" | sudo tee -a /etc/hosts
https://app-06.example.com

═══════════════════════════════════════════════════════════════════════════════
8. ТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ
═══════════════════════════════════════════════════════════════════════════════

Логин: admin    Пароль: admin123
Логин: user     Пароль: user123

═══════════════════════════════════════════════════════════════════════════════
9. ПРОВЕРКА БД
═══════════════════════════════════════════════════════════════════════════════

kubectl exec -it -n exam-kyznetsov postgres-db-0 -- psql -U admin -d userdb -c "SELECT * FROM users;"

═══════════════════════════════════════════════════════════════════════════════
10. GIT
═══════════════════════════════════════════════════════════════════════════════

cd ~/kuber/exam-kyznetsov
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/Gogf21/microservices-kubernetes.git
git branch -M main
git push -u origin main

═══════════════════════════════════════════════════════════════════════════════
11. ПОЛНАЯ ПЕРЕУСТАНОВКА
═══════════════════════════════════════════════════════════════════════════════

helm uninstall user-management -n exam-kyznetsov
kubectl delete all --all -n exam-kyznetsov
kubectl delete pvc --all -n exam-kyznetsov
kubectl delete namespace exam-kyznetsov
kubectl create namespace exam-kyznetsov

# Пересобрать образы
cd ~/kuber/exam-kyznetsov/services/auth-service && eval $(minikube docker-env) && docker build -t auth-service:latest .
cd ~/kuber/exam-kyznetsov/services/profile-service && docker build -t profile-service:latest .
cd ~/kuber/exam-kyznetsov/services/notification-service && docker build -t notification-service:latest .

# Установить заново
cd ~/kuber/exam-kyznetsov/user-management-chart
helm install user-management . -n exam-kyznetsov --create-namespace -f values-dev.yaml
