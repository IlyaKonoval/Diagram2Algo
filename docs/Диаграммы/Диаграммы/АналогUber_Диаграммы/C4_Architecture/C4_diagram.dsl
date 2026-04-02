workspace "Система заказа поездок" "C2 + C3 виды с компонентами Trip Service" {

  model {

    // People
    passenger = person "Пассажир" "Вызывает поездки, оплачивает"
    driver = person "Водитель" "Принимает заказы, отправляет GPS"
    support = person "Служба поддержки" "Обрабатывает тикеты и возвраты"
    securityDept = person "Отдел безопасности" "Обрабатывает жалобы"

    // External systems
    paymentExt = softwareSystem "Платёжный шлюз" "Stripe"
    mapsExt = softwareSystem "Гео API" "Картография, ETA, маршруты"
    smsExt = softwareSystem "SMS-шлюз" "Отправка OTP"
    pushExt = softwareSystem "Push-сервис" "FCM"
    emailExt = softwareSystem "Email-сервис" "Отправка писем"
    idpExt = softwareSystem "Identity Provider" "OAuth вход"
    telematicsExt = softwareSystem "Телеметрия" "GPS-потоки"
    analyticsExt = softwareSystem "Analytics/BI" "Метрики и отчёты"
    externalFraud = softwareSystem "External Fraud Service" "Сервис продвинутой оценки мошенничества"

    // Our system
    ridesys = softwareSystem "Система заказа поездок" "Платформа вызова такси" {

      // Frontends / Clients
      mobilePassenger = container "Passenger Mobile App" "Мобильное приложение пассажира" "Flutter"
      mobileDriver    = container "Driver Mobile App" "Мобильное приложение водителя" "Flutter"
      webApp          = container "Web App" "Веб-клиент" "React / TypeScript"
      desktopApp      = container "Desktop App" "Десктоп-клиент" "Electron"
      adminUI         = container "Admin UI" "Панель операторов" "React / TypeScript"

      // Edge / Orchestration
      apiGateway = container "API Gateway" "Входная точка: маршрутизация, rate-limit, auth" "NGINX"
      backendOrchestrator = container "Backend Orchestrator" "Оркестрация потоков, агрегация ответов" "Java / Spring Boot"

      // Microservices (each owns its DB)
      userService = container "User Service" "Управление аккаунтами, профилями" "Java / Spring Boot"
      
      paymentService = container "Payment Service" "Платежи и возвраты" "Java / Spring Boot"
      driverLocationService = container "Driver Location Service" "Приём и хранение GPS, поиск nearby" "Node.js / WebSockets"
      notificationService = container "Notification Service" "Push/SMS/Email уведомления" "Node.js"
      fraudService = container "Fraud Service" "Антифрод скоринг" "Python / FastAPI"
      analyticsCollector = container "Analytics Collector" "Сбор событий для аналитики" "Go / Kafka Producer"
      
      // Databases
      userDB = container "UserDB" "Пользователи и профили" "PostgreSQL" {
        tags "Database"
      }
      tripDB = container "TripDB" "Поездки, статусы, тарифы" "PostgreSQL" {
        tags "Database"
      }
      paymentDB = container "PaymentDB" "Транзакции и квитанции" "PostgreSQL" { 
        tags "Database"
      }
      locationDB = container "LocationDB" "История треков, таймсерии GPS" "TimescaleDB" {
        tags "Database"
      }
      notificationDB = container "NotificationDB" "Шаблоны и статусы уведомлений" "PostgreSQL" {
        tags "Database"
      }
      fraudDB = container "FraudDB" "Поведенческие данные для антифрода" "MongoDB" {
        tags "Database"
      }

      // Infrastructure
      cache    = container "Redis Cache" "Кэш: ETA, сессии" "Redis"
      eventBus = container "Event Bus" "Асинхронные события" "Kafka"
      
      tripService = container "Trip Service" "Создание и управление поездками, расчёт ETA" "Java / Spring Boot" {
        // C3: Components inside Trip Service
        tripController = component "TripController" "REST API контроллер для поездок" "Spring MVC"
        tripManager = component "TripManager" "Бизнес-логика создания, отмены, управления поездками" "Spring Service"
        etaCalculator = component "ETACalculator" "Расчёт маршрутов и ETA" "Java Service"
        tripRepository = component "TripRepository" "CRUD для поездок в TripDB" "Spring Data JPA"
        tripEventPublisher = component "TripEventPublisher" "Публикация событий поездок в Event Bus" "Kafka Producer"
        mapsAdapter = component "MapsAdapter" "Интеграция с внешним Geo API" "REST Client"
        tripFraudChecker = component "TripFraudChecker" "Проверка мошенничества" "REST Client / Python"

        // C3 relationships
        tripController -> tripManager "Делегирует запросы"
        tripManager -> tripRepository "Сохраняет поездки"
        tripManager -> etaCalculator "Запрашивает ETA"
        tripManager -> tripFraudChecker "Проверяет мошенничество"
        etaCalculator -> mapsAdapter "Запрашивает маршруты/ETA"
        tripManager -> tripEventPublisher "Публикует события поездок"
        tripRepository -> tripDB "JDBC"
        mapsAdapter -> mapsExt "HTTPS"
        tripEventPublisher -> eventBus "Публикует события"
      }

      // Relationships (C2)
      passenger -> mobilePassenger "Использует"
      passenger -> webApp "Использует"
      passenger -> desktopApp "Использует"
      driver -> mobileDriver "Использует"
      support -> adminUI "Работает с тикетами"
      securityDept -> adminUI "Обрабатывает жалобы"

      mobilePassenger -> apiGateway "HTTPS/JSON"
      mobileDriver -> apiGateway "HTTPS/JSON + WebSocket"
      webApp -> apiGateway "HTTPS/JSON"
      desktopApp -> apiGateway "HTTPS/JSON"
      adminUI -> apiGateway "HTTPS/JSON (Admin API)"

      apiGateway -> backendOrchestrator "Перенаправляет API запросы"
      backendOrchestrator -> userService "Вызывает REST API для получения данных пользователя"
      backendOrchestrator -> tripService "Вызывает REST API для создания/управления поездками"
      backendOrchestrator -> paymentService "Вызывает REST API для инициации платежей"
      backendOrchestrator -> driverLocationService "Запросы по ближайшим водителям"
      backendOrchestrator -> notificationService "Запросы доставки уведомлений"
      backendOrchestrator -> fraudService "Запросы скоринга мошенничества"
      backendOrchestrator -> analyticsCollector "Публикует события"

      userService -> userDB "Чтение/Запись"
      tripService -> tripDB "Чтение/Запись"
      paymentService -> paymentDB "Чтение/Запись"
      driverLocationService -> locationDB "Запись GPS данных / Чтение последних треков"
      notificationService -> notificationDB "Чтение/Запись шаблонов и статусов"
      fraudService -> fraudDB "Чтение/Запись"

      tripService -> cache "Сохраняет ETA / краткоживущие данные"
      driverLocationService -> cache "Сохраняет текущие местоположения водителей"
      userService -> eventBus "Публикует события"
      paymentService -> eventBus "Публикует события"
      driverLocationService -> eventBus "Публикует события"
      notificationService -> eventBus "Публикует события"
      fraudService -> eventBus "Публикует события"
      analyticsCollector -> eventBus "Потребляет события"
      analyticsCollector -> analyticsExt "Отправляет агрегированные события"

      tripService -> mapsExt "Запрашивает маршруты/ETA"
      paymentService -> paymentExt "Инициирует платежи"
      paymentExt -> paymentService "Отправляет вебхуки"
      notificationService -> smsExt "Отправляет SMS"
      notificationService -> pushExt "Отправляет Push уведомления"
      notificationService -> emailExt "Отправляет письма"
      userService -> idpExt "OAuth вход"
      driverLocationService -> telematicsExt "Опциональная GPS лента"
      fraudService -> externalFraud "Опциональный продвинутый скоринг"
    }

    // C1 system-level
    passenger -> ridesys "Вызывает поездки"
    driver -> ridesys "Обслуживает поездки"
    ridesys -> paymentExt "Интеграция с платежами"
    ridesys -> mapsExt "Использует картографию"
  }

  views {
    systemContext ridesys "C1_SystemContext" {
      include *
      autolayout lr
    }
    container ridesys "C2_Container" {
      include *
      autolayout lr
    }
    component tripService "C3_TripService" {
      include *
      autolayout tb
    }

    // Styling
    styles {
      element "Person" {
        shape person
        background "#084C61"
        color "#FFFFFF"
      }
      element "Software System" {
        background "#177E89"
        color "#FFFFFF"
      }
      element "Container" {
        background "#45B69C"
        color "#0B0B0B"
      }
      element "Component" {
        background "#BCD8C1"
        color "#0B0B0B"
      }
      element "Database" {
        shape cylinder
        background "#F2D7D5"
        color "#000000"
      }
    }
  }
}
