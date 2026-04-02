IMAGE_PROMPT = """Ты анализируешь изображение диаграммы процесса. Это может быть BPMN, flowchart, UML sequence, или произвольная схема.

Твоя задача: извлечь пошаговый алгоритм из диаграммы.

Текст с диаграммы (OCR):
{ocr_text}

ПОШАГОВЫЙ АНАЛИЗ:
1. Сначала определи тип диаграммы (BPMN, sequence, flowchart, activity, other)
2. Найди начальную точку (Start, начало стрелок, первый элемент)
3. Проследи поток по стрелкам/связям от начала к концу
4. Для каждого элемента определи: кто действует (actor), что делает (action), на что направлено (target)
5. Пронумеруй шаги в порядке выполнения
6. Учти ветвления и условия (отметь в note)

ВАЖНО:
- Сохраняй ОРИГИНАЛЬНЫЙ язык текста с диаграммы (русский, английский и т.д.)
- НЕ переводи текст
- Извлекай ВСЕ шаги, которые видишь
- Роль/актор — это КТО выполняет действие (участник, система, пользователь)
- Если роль не указана явно, поставь null

Ответь ТОЛЬКО валидным JSON в формате:
{{
  "diagram_type": "sequence|flowchart|activity|bpmn|other",
  "steps": [
    {{"number": 1, "actor": "роль или null", "action": "описание действия", "target": "цель или null", "note": "примечание или null"}}
  ],
  "confidence": 0.0-1.0
}}

ПРИМЕРЫ:

Пример 1 (BPMN процесс):
{{
  "diagram_type": "bpmn",
  "steps": [
    {{"number": 1, "actor": "Инициатор", "action": "Создание запроса", "target": null, "note": null}},
    {{"number": 2, "actor": "Координатор", "action": "Внесение технологии в тех. стек", "target": "Технологический стек", "note": "статус Consideration"}},
    {{"number": 3, "actor": "Совет по технологиям", "action": "Принятие решения", "target": null, "note": null}}
  ],
  "confidence": 0.85
}}

Пример 2 (Flowchart):
{{
  "diagram_type": "flowchart",
  "steps": [
    {{"number": 1, "actor": null, "action": "Начало", "target": null, "note": null}},
    {{"number": 2, "actor": null, "action": "Наполнить чайник", "target": null, "note": null}},
    {{"number": 3, "actor": null, "action": "Включить чайник", "target": null, "note": null}},
    {{"number": 4, "actor": null, "action": "Ждать закипания", "target": null, "note": "условие: чайник закипел?"}},
    {{"number": 5, "actor": null, "action": "Чай готов", "target": null, "note": null}}
  ],
  "confidence": 0.9
}}

Пример 3 (Sequence diagram):
{{
  "diagram_type": "sequence",
  "steps": [
    {{"number": 1, "actor": "Клиент", "action": "Отправляет запрос", "target": "Сервер", "note": null}},
    {{"number": 2, "actor": "Сервер", "action": "Проверяет данные", "target": "База данных", "note": null}},
    {{"number": 3, "actor": "База данных", "action": "Возвращает результат", "target": "Сервер", "note": null}},
    {{"number": 4, "actor": "Сервер", "action": "Отправляет ответ", "target": "Клиент", "note": null}}
  ],
  "confidence": 0.95
}}

Теперь проанализируй изображение и верни JSON."""


IMAGE_PROMPT_NO_OCR = """Ты анализируешь изображение диаграммы процесса. Это может быть BPMN, flowchart, UML sequence, или произвольная схема.

Твоя задача: извлечь пошаговый алгоритм из диаграммы.

ПОШАГОВЫЙ АНАЛИЗ:
1. Сначала определи тип диаграммы (BPMN, sequence, flowchart, activity, other)
2. Найди начальную точку (Start, начало стрелок, первый элемент)
3. Проследи поток по стрелкам/связям от начала к концу
4. Для каждого элемента определи: кто действует (actor), что делает (action), на что направлено (target)
5. Пронумеруй шаги в порядке выполнения
6. Учти ветвления и условия (отметь в note)

ВАЖНО:
- Сохраняй ОРИГИНАЛЬНЫЙ язык текста с диаграммы (русский, английский и т.д.)
- НЕ переводи текст
- Извлекай ВСЕ шаги, которые видишь
- Роль/актор — это КТО выполняет действие (участник, система, пользователь)
- Если роль не указана явно, поставь null

Ответь ТОЛЬКО валидным JSON в формате:
{
  "diagram_type": "sequence|flowchart|activity|bpmn|other",
  "steps": [
    {"number": 1, "actor": "роль или null", "action": "описание действия", "target": "цель или null", "note": "примечание или null"}
  ],
  "confidence": 0.0-1.0
}

Проанализируй изображение и верни JSON."""


TEXT_PROMPT = """Ты анализируешь текстовое описание диаграммы (PlantUML код, Structurizr DSL, метки из XML или текстовое описание).

Извлеки пошаговый алгоритм процесса.

Содержимое:
{content}

ПОШАГОВЫЙ АНАЛИЗ:
1. Определи формат (PlantUML, BPMN XML, DrawIO XML, Structurizr DSL, текст)
2. Найди все элементы/узлы (участники, задачи, события)
3. Найди все связи/переходы между элементами
4. Определи порядок выполнения по связям
5. Для каждого шага выдели: actor, action, target
6. Учти условия и ветвления

Ответь ТОЛЬКО валидным JSON в формате:
{{
  "diagram_type": "sequence|flowchart|activity|state|bpmn|other",
  "steps": [
    {{"number": 1, "actor": "участник или null", "action": "описание действия", "target": "цель или null", "note": "примечание или null"}}
  ],
  "confidence": 0.0-1.0
}}

Правила:
1. Парси имена элементов, метки и значения
2. Следуй по связям/стрелкам для определения порядка шагов
3. Включай участников, задачи, развилки, события
4. Сохраняй оригинальный язык текста

Верни JSON."""


SIMPLE_IMAGE_PROMPT = """Перечисли все шаги с этой диаграммы, по одному на строку.
Формат: [номер]. [роль, если есть] -> [действие] -> [цель, если есть]

ВАЖНО: Сохраняй оригинальный язык текста с диаграммы. НЕ переводи.

Пример:
1. Инициатор -> Создание запроса
2. Координатор -> Внесение технологии в стек -> Технологический стек
3. Совет -> Принятие решения

Теперь перечисли шаги с изображения:"""


SIMPLE_TEXT_PROMPT = """Перечисли все шаги/действия из этого описания диаграммы, по одному на строку.
Формат: [номер]. [роль, если есть] -> [действие] -> [цель, если есть]

Пример:
1. Пользователь -> Отправляет запрос -> Сервер
2. Сервер -> Обрабатывает данные -> База данных"""


IMAGE_PROMPT_EN = """You are analyzing a process diagram image. It could be BPMN, flowchart, UML sequence, activity diagram, or any custom scheme.

Your task: extract the step-by-step algorithm from the diagram.

OCR text extracted from the diagram:
{ocr_text}

STEP-BY-STEP ANALYSIS:
1. Identify diagram type (BPMN, sequence, flowchart, activity, other)
2. Find the starting point (Start event, first arrow, first element)
3. Trace the flow along arrows/connections from start to end
4. For each element identify: who acts (actor), what they do (action), what they target (target)
5. Number steps in execution order
6. Note branches and conditions in the "note" field

IMPORTANT:
- PRESERVE the original language of text on the diagram (Russian, English, etc.) — do NOT translate
- Extract ALL visible steps, do not skip any
- "actor" = WHO performs the action (participant, system, user). Use null if not shown
- "target" = WHO or WHAT receives the action. Use null if not applicable
- Return ONLY the JSON object below. No markdown fences, no explanation, no extra text
- Output must be parseable by json.loads() in Python

{{
  "diagram_type": "sequence|flowchart|activity|bpmn|other",
  "steps": [
    {{"number": 1, "actor": "role or null", "action": "action description", "target": "target or null", "note": "note or null"}}
  ],
  "confidence": 0.0-1.0
}}"""


IMAGE_PROMPT_EN_NO_OCR = """You are analyzing a process diagram image. It could be BPMN, flowchart, UML sequence, activity diagram, or any custom scheme.

Your task: extract the step-by-step algorithm from the diagram.

STEP-BY-STEP ANALYSIS:
1. Identify diagram type (BPMN, sequence, flowchart, activity, other)
2. Find the starting point (Start event, first arrow, first element)
3. Trace the flow along arrows/connections from start to end
4. For each element identify: who acts (actor), what they do (action), what they target (target)
5. Number steps in execution order
6. Note branches and conditions in the "note" field

IMPORTANT:
- PRESERVE the original language of text on the diagram (Russian, English, etc.) — do NOT translate
- Extract ALL visible steps, do not skip any
- "actor" = WHO performs the action (participant, system, user). Use null if not shown
- Return ONLY the JSON object below. No markdown fences, no explanation, no extra text
- Output must be parseable by json.loads() in Python

{
  "diagram_type": "sequence|flowchart|activity|bpmn|other",
  "steps": [
    {"number": 1, "actor": "role or null", "action": "action description", "target": "target or null", "note": "note or null"}
  ],
  "confidence": 0.0-1.0
}"""


TEXT_PROMPT_EN = """You are analyzing a text-based diagram description (PlantUML code, Structurizr DSL, DrawIO XML labels, or BPMN XML).

Extract the step-by-step process algorithm.

STEP-BY-STEP ANALYSIS:
1. Detect the format (PlantUML, BPMN XML, DrawIO XML, Structurizr DSL, text)
2. Extract all elements/nodes (participants, tasks, events)
3. Find all connections/transitions between elements
4. Determine execution order from connections
5. For each step identify: actor, action, target
6. Note conditions and branches

IMPORTANT:
- Preserve the original language of element labels — do NOT translate
- Return ONLY the JSON object below. No markdown fences, no explanation
- Output must be parseable by json.loads() in Python

{{{{
  "diagram_type": "sequence|flowchart|activity|state|bpmn|other",
  "steps": [
    {{{{"number": 1, "actor": "participant or null", "action": "action description", "target": "target or null", "note": "note or null"}}}}
  ],
  "confidence": 0.0-1.0
}}}}"""


PLANTUML_SEQUENCE_PROMPT = """Convert these steps to PlantUML sequence diagram syntax.

Steps:
{steps}

Output valid PlantUML code starting with @startuml and ending with @enduml.
Use proper sequence diagram syntax with -> arrows.
Include all actors/participants mentioned in the steps."""


PLANTUML_ACTIVITY_PROMPT = """Convert these steps to PlantUML activity diagram syntax.

Steps:
{steps}

Output valid PlantUML code starting with @startuml and ending with @enduml.
Use proper activity diagram syntax with :action; format.
Include decision points if implied by the steps."""
