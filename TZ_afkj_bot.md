# ТЗ: AFK Journey — авто-пушер AFK Stages

## 1. Назначение

Консольная утилита под Windows, автоматически проходящая стейджи в режиме **AFK Stages** нативного Windows-клиента AFK Journey. Использует чужие формации из Records (формации игроков с других серверов, прошедших стейдж), с перебором по позициям при поражениях.

## 2. Окружение и стек

| Параметр | Значение |
|---|---|
| ОС | Windows 10/11 |
| Клиент | Нативный Windows AFK Journey |
| Режим окна | Borderless windowed (требование к пользователю) |
| Язык | Python 3.11+ |
| Захват экрана | `mss` |
| Поиск окна | `pygetwindow` |
| Ввод | `pydirectinput` (синтез ввода через SendInput, проходит в DirectX-окна) |
| Распознавание | `opencv-python` (`cv2.matchTemplate` с `TM_CCOEFF_NORMED`) |
| Numerics | `numpy` |
| Конфиг | `configparser` |
| CLI | `argparse` |

**requirements.txt:**

```
mss
pygetwindow
pydirectinput
opencv-python
numpy
```

## 3. Запуск

```
python main.py --mode {phantimal|battle} [--debug]
```

- `--mode phantimal` — стартовый тап по вкладке Phantimal Challenge.
- `--mode battle` — стартовый тап по вкладке Battle.
- `--debug` — сохранять скриншоты каждого шага автомата в `debug/`.

## 4. Предусловие

Игра запущена. Пользователь находится на экране **AFK Stages** с видимыми вкладками Battle / Phantimal Challenge. Бот не отвечает за навигацию откуда-либо ещё.

## 5. Бизнес-логика

```
current_formation = 0           # позиция в списке Records (0-based)
fail_counter = 0                # поражения подряд текущей формации

INIT:
    тап вкладки {phantimal | battle} согласно --mode
    тап «Battle» (запуск экрана выбора формации)

LOOP (на экране формации):
    тап «Records»
    в Records: current_formation тапов по стрелке «вправо»
    тап «Copy»                                         # копирует чужую формацию в твой слот
    тап «Battle»                                       # запуск боя
    ждать исход (victory | defeat | timeout)

    if VICTORY:
        fail_counter = 0
        current_formation = 0
        тап «Battle» (на экране победы — сразу новый бой)
        # после этого игра возвращает на экран формации
        continue LOOP

    if DEFEAT:
        fail_counter += 1
        тап «Retry»
        # Retry возвращает на экран формации (не сразу в бой)
        if fail_counter < 3:
            continue LOOP                              # та же формация
        else:
            fail_counter = 0
            current_formation += 1
            if current_formation > 2:
                STOP                                   # 3 формации × 3 поражения исчерпаны
            continue LOOP                              # следующая формация
```

**Инварианты:**

- Победа сбрасывает оба счётчика. На следующем стейдже снова стартуем с первой формации (Records на новом стейдже пересортирован сервером).
- `current_formation` растёт только в рамках сессии, до победы или до STOP.
- Любой неожиданный экран дольше `stuck_timeout_sec` → STOP с ошибкой.
- Records всегда открывается с формации №0 — никаких ресетов в начало делать не надо.

## 6. Out of scope

- Навигация откуда-либо, кроме экрана AFK Stages.
- Дейлики, мейл, награды, ивенты, баннеры, попапы.
- Восстановление после вылета, потери фокуса, обновлений клиента.
- Платные ретраи, докупка попыток.
- GUI, трей, нотификации.
- Несколько разрешений или языков клиента — фиксируем одно (то, под которое нарезаны шаблоны).
- Эксклюзивный fullscreen.
- Запуск самой игры, логин.

## 7. Архитектура

```
┌──────────────────────────────────────────────┐
│                   main.py                    │
│  argparse + configparser → создаёт компоненты│
│  → StageRunner(mode).run()                   │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│                StageRunner                   │
│  • state machine                             │
│  • счётчики current_formation, fail_counter  │
│  • высокоуровневые шаги                      │
└──────────────────────────────────────────────┘
        │                │                │
        ▼                ▼                ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ WindowAgent │  │ScreenMatcher │  │   Templates  │
│             │  │              │  │              │
│ attach()    │  │ find()       │  │ PNG-кропы    │
│ get_rect()  │  │ wait_for()   │  │ из реальных  │
│ screenshot()│  │ wait_for_any │  │ скриншотов   │
│ tap_*       │  │              │  │ клиента      │
└─────────────┘  └──────────────┘  └──────────────┘
```

### 7.1 `WindowAgent`

Отвечает за физическое взаимодействие с окном игры. Игровой логики не знает.

```
class WindowAgent:
    def __init__(self, window_title: str)
    def attach(self) -> None
        # находит окно по title через pygetwindow, сохраняет hwnd
    def get_rect(self) -> tuple[int, int, int, int]
        # (x, y, w, h) в экранных координатах; читать заново при каждом вызове —
        # окно могло сдвинуться
    def screenshot(self) -> np.ndarray
        # mss, кроп по rect окна, BGR
    def tap_abs(self, x: int, y: int) -> None
        # абсолютные экранные координаты
    def tap_rel(self, x: int, y: int) -> None
        # относительно левого верхнего угла окна
    def tap_normalized(self, nx: float, ny: float) -> None
        # nx, ny ∈ [0..1] — устойчиво к ресайзу
```

**Замечания:**

- `pydirectinput.click(x, y)` синтезирует движение мыши + клик — мышь физически дёрнется. Это осознанный компромисс: пользователь подтвердил, что приемлемо.
- Между скриншотом и тапом окно могло сдвинуться, поэтому `tap_rel` всегда заново читает rect.
- При borderless windowed `mss` отдаёт корректный кадр даже без фокуса окна.

### 7.2 `ScreenMatcher`

Отвечает за распознавание UI на скриншоте. Игровой логики не знает.

```
class ScreenMatcher:
    def __init__(self, templates_dir: Path, default_threshold: float = 0.85)

    def find(self, name: str, screenshot: np.ndarray) -> Match | None
        # Match: x, y (центр найденного элемента), confidence

    def wait_for(self, name: str, agent: WindowAgent,
                 timeout: float, interval: float = 0.5) -> Match | None
        # поллинг скриншотов до появления или таймаута

    def wait_for_any(self, names: list[str], agent: WindowAgent,
                     timeout: float, interval: float = 0.5)
                     -> tuple[str, Match] | None
        # ждёт первое совпадение из списка
        # ключевой метод для разрешения VICTORY vs DEFEAT
```

Шаблоны лежат в `templates/` как PNG-кропы из реальных скриншотов клиента в целевом разрешении. Опциональный JSON-сайдкар на каждый шаблон может переопределять порог уверенности и регион поиска (чтобы не сканировать весь экран и не путать одинаковые иконки в разных контекстах).

### 7.3 `StageRunner`

Единственное место, где живёт игровая логика. Не знает про OpenCV и pydirectinput напрямую — только через `WindowAgent` и `ScreenMatcher`.

```
class StageRunner:
    def __init__(self, agent, matcher, config,
                 mode: Literal["phantimal","battle"])
    def run(self) -> ExitReason

    # приватные шаги
    _enter_mode()                # тап вкладки + тап Battle
    _open_records()              # тап Records
    _pick_formation(idx: int)    # idx тапов по стрелке вправо
    _copy_and_fight()            # тап Copy → ждать FORMATION_SCREEN → тап Battle
    _wait_outcome() -> Literal["victory","defeat","timeout"]
    _on_victory()                # тап Battle на экране победы
    _on_defeat()                 # тап Retry
```

## 8. Конечный автомат

| Состояние | Что ожидается на экране | Действие | Переход |
|---|---|---|---|
| `INIT` (стартовое) | экран AFK Stages с вкладками | тап вкладки по `--mode`, затем тап Battle | → `FORMATION_SCREEN` |
| `FORMATION_SCREEN` | экран твоей формации с кнопкой Records | тап Records | → `RECORDS` |
| `RECORDS` | первая чужая формация в Records (стрелки ← / → и кнопка Copy) | `current_formation` тапов по стрелке «вправо» | → `RECORDS_PICKED` |
| `RECORDS_PICKED` | выбранная формация в Records с кнопкой Copy | тап Copy | → `READY_TO_FIGHT` |
| `READY_TO_FIGHT` | экран формации с загруженной чужой формацией | тап Battle | → `IN_BATTLE` |
| `IN_BATTLE` | бой идёт | `wait_for_any(["screen_victory","screen_defeat"], timeout=battle_timeout_sec)` | → `VICTORY` / `DEFEAT` / `STUCK` |
| `VICTORY` | экран победы | сброс счётчиков, тап Battle | → `FORMATION_SCREEN` |
| `DEFEAT` | экран поражения | `fail_counter += 1`; тап Retry; пересчёт счётчиков по §5 | → `FORMATION_SCREEN` или `STOPPED` |
| `STOPPED` | — | финальный лог, exit 0 | — |
| `STUCK` | — | дамп скриншота в `debug/`, exit 1 | — |

## 9. Шаблоны

PNG-кропы из реальных скриншотов клиента, в целевом разрешении.

| Имя | Назначение | Регион поиска |
|---|---|---|
| `tab_phantimal` | вкладка Phantimal Challenge | верхняя треть |
| `tab_battle` | вкладка Battle | верхняя треть |
| `btn_battle_main` | кнопка Battle на экране стейджа (запуск выбора формации) | нижняя треть |
| `btn_records` | кнопка Records на экране формации | нижняя треть |
| `btn_arrow_right` | стрелка «следующая формация» в Records | правый край Records |
| `btn_copy` | кнопка Copy в Records | центр/низ |
| `btn_battle_start` | кнопка Battle для запуска боя на экране формации | нижняя треть |
| `screen_victory` | визуальный якорь экрана победы | центр |
| `screen_defeat` | визуальный якорь экрана поражения | центр |
| `btn_battle_after_victory` | кнопка Battle на экране победы | нижняя треть |
| `btn_retry` | кнопка Retry на экране поражения | нижняя треть |

**Замечания по шаблонам:**

- `btn_battle_main`, `btn_battle_start`, `btn_battle_after_victory` могут оказаться визуально одинаковыми. Логически это разные кнопки в разных контекстах — храним как отдельные шаблоны (даже с одинаковым PNG, если они идентичны). Это даёт независимый контроль порогов и регионов поиска и нулевой риск ложного срабатывания не в том состоянии.
- При обновлении клиента и изменении UI достаточно перенарезать шаблоны — код не трогается.

## 10. Конфиг (`config.ini`)

```ini
[window]
title = AFK Journey

[timing]
poll_interval_sec = 0.5
short_wait_sec = 5
long_wait_sec = 15
battle_timeout_sec = 300
stuck_timeout_sec = 60

[records]
arrow_settle_sec = 0.4

[strategy]
max_failures_per_formation = 3
max_formations = 3

[matching]
default_threshold = 0.85

[paths]
templates_dir = ./templates
debug_dir = ./debug
log_file = ./bot.log
```

Захардкоженных «магических чисел» в коде быть не должно — всё через конфиг.

## 11. Поведение при ошибках

Принцип: **бот не пытается ничего чинить**.

| Ситуация | Поведение |
|---|---|
| Окно игры не найдено при старте | exit 1, сообщение в лог |
| `wait_for` ожидаемого экрана истёк | сохранить `debug/stuck_<timestamp>.png`, exit 1 |
| Бой длится дольше `battle_timeout_sec` | сохранить скриншот, exit 1 |
| 3 формации × 3 поражения исчерпаны | exit 0 (нормальное завершение) |
| Ctrl+C | мгновенный graceful exit |

## 12. Логирование

На каждый переход автомата:

- Текущее состояние, `current_formation`, `fail_counter`.
- Какой шаблон сматчился и с какой confidence.
- Время фазы (для тюнинга таймингов).

Уровень `INFO` по умолчанию. `--debug` повышает до `DEBUG` и включает сохранение скриншотов каждого шага в `debug/`.

## 13. Структура проекта

```
afkj-bot/
├── main.py
├── config.ini
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── window_agent.py
│   ├── screen_matcher.py
│   ├── stage_runner.py
│   └── config.py
├── templates/
│   ├── tab_phantimal.png
│   ├── tab_battle.png
│   ├── btn_battle_main.png
│   ├── btn_records.png
│   ├── btn_arrow_right.png
│   ├── btn_copy.png
│   ├── btn_battle_start.png
│   ├── screen_victory.png
│   ├── screen_defeat.png
│   ├── btn_battle_after_victory.png
│   └── btn_retry.png
└── debug/                  # gitignore'ить
```

## 14. Definition of Done

1. С `--mode phantimal` бот тапает Phantimal → Battle → Records → Copy → Battle и доходит до экрана победы или поражения хотя бы на одном бое.
2. То же с `--mode battle`.
3. После победы корректно крутится цикл (≥3 победы подряд без выхода из FORMATION_SCREEN).
4. При искусственном проигрыше первой формации 3 раза подряд бот тапает стрелку «вправо» один раз и продолжает с новой формацией. Визуально в Records видно, что отображается уже вторая формация.
5. После 3 формаций × 3 поражения — exit 0 с финальным сообщением.
6. На STUCK — exit 1 со скриншотом последнего экрана в `debug/`.
7. Каждый запуск стартует с экрана AFK Stages (предусловие §4) и не оставляет игру в промежуточном состоянии после завершения.
