

import random
import string
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, join_room, leave_room, emit

from questions import QUESTIONS

app = Flask(__name__)
app.config["SECRET_KEY"] = "quiz-battle-secret-key"

socketio = SocketIO(
    app,
    async_mode="threading",
    cors_allowed_origins="*"
)

rooms = {}

QUESTION_COUNT = 10
QUESTION_TIME = 15
POINTS_PER_ANSWER = 100


HTML = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quiz Battle</title>
<script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    min-height: 100vh;
    padding: 20px;
    font-family: Arial, sans-serif;
    color: white;
    background: linear-gradient(135deg,#151020,#30204c,#171126);
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    width: 100%;
    max-width: 580px;
    padding: 30px;
    background: #ffffff0d;
    border: 1px solid #ffffff20;
    border-radius: 24px;
    box-shadow: 0 20px 70px #0006;
}

.logo { font-size: 42px; text-align: center; }

h1 { text-align: center; font-size: 34px; }
h1 span { color: #c49aff; }

.subtitle {
    text-align: center;
    color: #c4b7d8;
    margin-bottom: 25px;
}

input, select {
    width: 100%;
    padding: 15px;
    margin: 8px 0;
    border-radius: 12px;
    border: 1px solid #765a9b;
    background: #241a35;
    color: white;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 15px;
    margin: 7px 0;
    border: 0;
    border-radius: 12px;
    background: linear-gradient(90deg,#9562e5,#c18aff);
    color: white;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

button:hover { filter: brightness(1.12); }
button:disabled { opacity: .45; cursor: not-allowed; }
.secondary { background: #493461; }

.hidden { display: none !important; }

#message {
    color: #d5baff;
    text-align: center;
    margin-top: 15px;
}

.room-code {
    font-size: 36px;
    font-weight: bold;
    letter-spacing: 7px;
    color: #d0aaff;
    text-align: center;
    margin: 18px;
}

.player, .score-row {
    padding: 13px;
    margin: 8px 0;
    border-radius: 12px;
    background: #ffffff12;
}

.player small {
    float: right;
    color: #c49aff;
}

.status {
    color: #c9b5e8;
    text-align: center;
    font-size: 14px;
}

.question-box {
    padding: 22px;
    margin: 20px 0;
    background: #ffffff10;
    border-radius: 18px;
    font-size: 22px;
    text-align: center;
    line-height: 1.4;
}

.answer {
    text-align: left;
    background: #493461;
    border: 2px solid transparent;
}

.answer.selected {
    border-color: #d0aaff;
    background: #7046a2;
}

.answer.correct { background: #287d52; }
.answer.wrong { background: #923d50; }

.timer {
    font-size: 28px;
    font-weight: bold;
    text-align: center;
    color: #d0aaff;
    margin: 15px;
}

.progress {
    height: 9px;
    background: #ffffff20;
    border-radius: 10px;
    overflow: hidden;
}

#progressBar {
    height: 100%;
    width: 0;
    background: #c18aff;
    transition: width .3s;
}

.category-label {
    color: #c49aff;
    text-align: center;
    margin: 10px;
}

#feedback {
    text-align: center;
    margin: 15px 0;
    color: #d5baff;
    font-weight: bold;
}
</style>
</head>

<body>
<div class="container">

    <div class="logo">⚔️</div>
    <h1>QUIZ <span>BATTLE</span></h1>
    <div class="subtitle">Сражайся знаниями!</div>

    <section id="menu">
        <input id="nickname" maxlength="20"
               placeholder="Твой никнейм">

        <div class="status">Выбери категорию игры</div>
        <select id="category"></select>

        <button onclick="createRoom()">＋ Создать комнату</button>

        <input id="roomInput" maxlength="6"
               placeholder="Код комнаты">

        <button class="secondary" onclick="joinRoom()">
            Войти по коду
        </button>
    </section>

    <section id="lobby" class="hidden">
        <h2 style="text-align:center">Игровая комната</h2>
        <div class="status">КОД КОМНАТЫ</div>
        <div class="room-code" id="roomCode">------</div>

        <button class="secondary" onclick="copyCode()">
            Скопировать код
        </button>

        <div class="category-label" id="lobbyCategory"></div>

        <h3>Игроки</h3>
        <div id="players"></div>

        <div class="status" id="hostInfo"></div>

        <button id="startButton" onclick="startGame()">
            ⚔️ Начать игру
        </button>

        <button class="secondary" onclick="exitRoom()">
            Покинуть комнату
        </button>
    </section>

    <section id="game" class="hidden">
        <div class="status" id="roundInfo"></div>

        <div class="timer" id="timer">15</div>

        <div class="progress">
            <div id="progressBar"></div>
        </div>

        <div class="category-label" id="gameCategory"></div>

        <div class="question-box" id="questionText">
            Ожидаем вопрос...
        </div>

        <div id="answers"></div>

        <div id="feedback"></div>
        <div class="status" id="answeredInfo"></div>
    </section>

    <section id="results" class="hidden">
        <div class="logo">🏆</div>
        <h2 style="text-align:center">Результаты игры</h2>
        <div id="winner"></div>
        <h3>Таблица лидеров</h3>
        <div id="leaderboard"></div>

        <button onclick="backToMenu()">
            В главное меню
        </button>
    </section>

    <div id="message"></div>
</div>

<script>
const socket = io();

let nickname = "";
let currentRoom = "";
let isHost = false;
let selectedAnswer = false;

const $ = id => document.getElementById(id);

function message(text) {
    $("message").textContent = text;
}

function showScreen(screen) {
    ["menu", "lobby", "game", "results"].forEach(id => {
        $(id).classList.toggle("hidden", id !== screen);
    });
}

function validNickname() {
    nickname = $("nickname").value.trim();

    if (!nickname) {
        message("Сначала введи никнейм!");
        return false;
    }

    return true;
}

function createRoom() {
    if (!validNickname()) return;

    socket.emit("create_room", {
        nickname,
        category: $("category").value
    });
}

function joinRoom() {
    if (!validNickname()) return;

    const code = $("roomInput").value.trim().toUpperCase();

    if (code.length !== 6) {
        message("Введи шестизначный код!");
        return;
    }

    socket.emit("join_room", {nickname, code});
}

function startGame() {
    socket.emit("start_game", {code: currentRoom});
}

function copyCode() {
    navigator.clipboard.writeText(currentRoom)
        .then(() => message("Код скопирован!"))
        .catch(() => message("Код комнаты: " + currentRoom));
}

function exitRoom() {
    socket.emit("leave_room", {code: currentRoom});
    currentRoom = "";
    isHost = false;
    showScreen("menu");
    message("Ты покинул комнату.");
}

function backToMenu() {
    currentRoom = "";
    isHost = false;
    showScreen("menu");
    message("Игра завершена!");
}

function showLobby(data) {
    currentRoom = data.code;
    isHost = data.host_sid === socket.id;

    $("roomCode").textContent = data.code;
    $("lobbyCategory").textContent = "Категория: " + data.category;

    $("hostInfo").textContent = isHost
        ? "Ты создатель комнаты"
        : "Ожидаем начала игры...";

    $("startButton").classList.toggle("hidden", !isHost);
    $("startButton").disabled = data.players.length < 2;

    $("players").innerHTML = "";

    data.players.forEach(player => {
        const div = document.createElement("div");
        div.className = "player";

        const name = document.createElement("span");
        name.textContent = player.nickname;

        const label = document.createElement("small");
        label.textContent =
            player.sid === data.host_sid ? "ХОСТ" : "ИГРОК";

        div.append(name, label);
        $("players").appendChild(div);
    });

    showScreen("lobby");
}

function showQuestion(data) {
    selectedAnswer = false;

    $("roundInfo").textContent =
        "Вопрос " + data.number + " из " + data.total;

    $("gameCategory").textContent = data.category;
    $("questionText").textContent = data.question;
    $("timer").textContent = data.time;
    $("progressBar").style.width = "0%";

    $("answers").innerHTML = "";
    $("feedback").textContent = "";
    $("answeredInfo").textContent = "";

    data.options.forEach((option, index) => {
        const button = document.createElement("button");
        button.className = "answer";
        button.textContent =
            String.fromCharCode(65 + index) + ". " + option;

        button.onclick = () => sendAnswer(index, button);

        $("answers").appendChild(button);
    });

    showScreen("game");
}

function sendAnswer(index, button) {
    if (selectedAnswer) return;

    selectedAnswer = true;

    document.querySelectorAll(".answer").forEach(b => {
        b.disabled = true;
    });

    button.classList.add("selected");

    socket.emit("submit_answer", {
        code: currentRoom,
        answer: index
    });

    $("feedback").textContent = "Ответ отправлен!";
}

function showScoreboard(players) {
    $("leaderboard").innerHTML = "";

    players.forEach((player, index) => {
        const div = document.createElement("div");
        div.className = "score-row";

        const name = document.createElement("span");
        name.textContent =
            (index + 1) + ". " + player.nickname;

        const score = document.createElement("strong");
        score.textContent = player.score + " очков";

        score.style.float = "right";

        div.append(name, score);
        $("leaderboard").appendChild(div);
    });
}

socket.on("connect", () => {
    message("Подключено к серверу!");
});

socket.on("disconnect", () => {
    message("Соединение потеряно. Обнови страницу.");
});

socket.on("categories", data => {
    $("category").innerHTML = "";

    data.categories.forEach(category => {
        const option = document.createElement("option");
        option.value = category.name;
        option.textContent =
            category.name + " (" + category.count + ")";
        $("category").appendChild(option);
    });
});

socket.on("room_created", data => {
    message("Комната создана!");
    showLobby(data);
});

socket.on("room_joined", data => {
    message("Ты вошёл в комнату!");
    showLobby(data);
});

socket.on("room_update", data => {
    if (data.code === currentRoom) showLobby(data);
});

socket.on("error_message", data => {
    message(data.text);
});

socket.on("game_started", data => {
    if (data.code === currentRoom) {
        showScreen("game");
        message("");
    }
});

socket.on("new_question", data => {
    showQuestion(data);
});

socket.on("timer_tick", data => {
    if (data.code !== currentRoom) return;

    $("timer").textContent = data.time;
    $("progressBar").style.width =
        ((15 - data.time) / 15 * 100) + "%";
});

socket.on("answer_received", () => {
    $("feedback").textContent = "Ответ принят! Ждём остальных...";
});

socket.on("question_result", data => {
    if (data.code !== currentRoom) return;

    const buttons = document.querySelectorAll(".answer");

    buttons.forEach((button, index) => {
        button.disabled = true;

        if (index === data.correct) {
            button.classList.add("correct");
        } else if (
            button.classList.contains("selected")
        ) {
            button.classList.add("wrong");
        }
    });

    $("feedback").textContent =
        "Правильный ответ: " + data.options[data.correct];

    $("answeredInfo").textContent =
        "Ответили: " + data.answered +
        " из " + data.total_players;
});

socket.on("score_update", data => {
    if (data.code === currentRoom) {
        showScoreboard(data.players);
    }
});

socket.on("game_over", data => {
    if (data.code !== currentRoom) return;

    const winner = data.players[0];

    $("winner").textContent = winner
        ? "🏆 Победитель: " + winner.nickname +
          " — " + winner.score + " очков!"
        : "Игра завершена!";

    showScoreboard(data.players);
    showScreen("results");
});

</script>
</body>
</html>
"""


def make_code():
    while True:
        code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        if code not in rooms:
            return code


def public_room(code):
    room = rooms[code]

    return {
        "code": code,
        "host_sid": room["host"],
        "category": room["category"],
        "players": [
            {
                "sid": sid,
                "nickname": player["nickname"],
                "score": player["score"]
            }
            for sid, player in room["players"].items()
        ]
    }


def sorted_scores(code):
    players = [
        {
            "nickname": player["nickname"],
            "score": player["score"]
        }
        for player in rooms[code]["players"].values()
    ]

    return sorted(
        players,
        key=lambda p: p["score"],
        reverse=True
    )


def update_room(code):
    if code in rooms:
        socketio.emit(
            "room_update",
            public_room(code),
            to=code
        )


def remove_player(sid, code):
    if code not in rooms:
        return

    room = rooms[code]

    if sid not in room["players"]:
        return

    leave_room(code, sid=sid)
    del room["players"][sid]

    if not room["players"]:
        del rooms[code]
        return

    if room["host"] == sid:
        room["host"] = next(iter(room["players"]))

    update_room(code)


def send_question(code):
    if code not in rooms:
        return

    room = rooms[code]

    if room["question_index"] >= len(room["round_questions"]):
        finish_game(code)
        return

    question = room["round_questions"][room["question_index"]]

    room["round_id"] += 1
    round_id = room["round_id"]
    room["phase"] = "question"
    room["answers"] = {}

    data = {
        "code": code,
        "number": room["question_index"] + 1,
        "total": len(room["round_questions"]),
        "category": room["category"],
        "question": question[0],
        "options": question[1],
        "time": QUESTION_TIME
    }

    socketio.emit("new_question", data, to=code)

    socketio.start_background_task(
        question_timer,
        code,
        round_id
    )


def question_timer(code, round_id):
    for remaining in range(QUESTION_TIME, 0, -1):
        if code not in rooms:
            return

        room = rooms[code]

        if room["round_id"] != round_id:
            return

        if room["phase"] != "question":
            return

        socketio.emit(
            "timer_tick",
            {"code": code, "time": remaining},
            to=code
        )

        socketio.sleep(1)

    finish_question(code, round_id)


def finish_question(code, round_id):
    if code not in rooms:
        return

    room = rooms[code]

    if room["round_id"] != round_id:
        return

    if room["phase"] != "question":
        return

    room["phase"] = "result"

    question = room["round_questions"][room["question_index"]]
    correct_index = question[2]

    for sid, answer in room["answers"].items():
        if answer == correct_index and sid in room["players"]:
            room["players"][sid]["score"] += POINTS_PER_ANSWER

    result = {
        "code": code,
        "correct": correct_index,
        "options": question[1],
        "answered": len(room["answers"]),
        "total_players": len(room["players"])
    }

    socketio.emit("question_result", result, to=code)

    socketio.emit(
        "score_update",
        {
            "code": code,
            "players": sorted_scores(code)
        },
        to=code
    )

    socketio.start_background_task(
        next_question,
        code,
        round_id
    )


def next_question(code, round_id):
    socketio.sleep(3)

    if code not in rooms:
        return

    room = rooms[code]

    if room["round_id"] != round_id:
        return

    if room["phase"] != "result":
        return

    room["question_index"] += 1
    send_question(code)


def finish_game(code):
    if code not in rooms:
        return

    room = rooms[code]
    room["phase"] = "finished"

    players = sorted_scores(code)

    socketio.emit(
        "game_over",
        {
            "code": code,
            "players": players
        },
        to=code
    )


@app.route("/")
def home():
    return render_template_string(HTML)


@socketio.on("connect")
def on_connect():
    emit(
        "categories",
        {
            "categories": [
                {"name": name, "count": len(items)}
                for name, items in QUESTIONS.items()
            ]
        }
    )


@socketio.on("create_room")
def create_room(data):
    nickname = str(data.get("nickname", "")).strip()[:20]
    category = str(data.get("category", ""))

    if not nickname:
        emit("error_message", {"text": "Введи никнейм!"})
        return

    if category not in QUESTIONS:
        emit("error_message", {"text": "Выбери категорию!"})
        return

    code = make_code()

    rooms[code] = {
        "host": request.sid,
        "category": category,
        "players": {
            request.sid: {
                "nickname": nickname,
                "score": 0
            }
        },
        "round_questions": [],
        "question_index": 0,
        "round_id": 0,
        "phase": "lobby",
        "answers": {}
    }

    join_room(code)
    emit("room_created", public_room(code))


@socketio.on("join_room")
def join_existing_room(data):
    nickname = str(data.get("nickname", "")).strip()[:20]
    code = str(data.get("code", "")).strip().upper()

    if not nickname:
        emit("error_message", {"text": "Введи никнейм!"})
        return

    if code not in rooms:
        emit("error_message", {"text": "Комната не найдена!"})
        return

    room = rooms[code]

    if room["phase"] != "lobby":
        emit("error_message", {"text": "Игра уже началась!"})
        return

    if len(room["players"]) >= 10:
        emit("error_message", {"text": "Максимум 10 игроков!"})
        return

    room["players"][request.sid] = {
        "nickname": nickname,
        "score": 0
    }

    join_room(code)

    emit("room_joined", public_room(code))
    update_room(code)


@socketio.on("leave_room")
def leave_existing_room(data):
    code = str(data.get("code", "")).strip().upper()
    remove_player(request.sid, code)


@socketio.on("start_game")
def start_game(data):
    code = str(data.get("code", "")).strip().upper()

    if code not in rooms:
        emit("error_message", {"text": "Комната не найдена!"})
        return

    room = rooms[code]

    if room["host"] != request.sid:
        emit("error_message", {"text": "Только создатель может начать игру!"})
        return

    if room["phase"] != "lobby":
        emit("error_message", {"text": "Игра уже запущена!"})
        return

    if len(room["players"]) < 2:
        emit("error_message", {"text": "Нужен хотя бы один друг!"})
        return

    available = QUESTIONS[room["category"]]

    room["round_questions"] = random.sample(
        available,
        min(QUESTION_COUNT, len(available))
    )

    room["question_index"] = 0

    for player in room["players"].values():
        player["score"] = 0

    room["phase"] = "playing"

    socketio.emit(
        "game_started",
        {"code": code},
        to=code
    )

    send_question(code)


@socketio.on("submit_answer")
def submit_answer(data):
    code = str(data.get("code", "")).strip().upper()
    answer = data.get("answer")

    if code not in rooms:
        emit("error_message", {"text": "Комната не найдена!"})
        return

    room = rooms[code]

    if room["phase"] != "question":
        emit("error_message", {"text": "Сейчас нельзя отвечать!"})
        return

    if request.sid not in room["players"]:
        emit("error_message", {"text": "Ты не участник этой комнаты!"})
        return

    if request.sid in room["answers"]:
        emit("error_message", {"text": "Ты уже ответил!"})
        return

    if not isinstance(answer, int) or answer not in range(4):
        emit("error_message", {"text": "Некорректный ответ!"})
        return

    room["answers"][request.sid] = answer

    emit("answer_received")

    if len(room["answers"]) >= len(room["players"]):
        finish_question(code, room["round_id"])


@socketio.on("disconnect")
def on_disconnect():
    for code in list(rooms.keys()):
        if request.sid in rooms[code]["players"]:
            remove_player(request.sid, code)


if __name__ == "__main__":
    print("=" * 40)
    print("       QUIZ BATTLE SERVER")
    print("=" * 40)
    print("Вопросов:", sum(len(q) for q in QUESTIONS.values()))
    print("Категорий:", len(QUESTIONS))
    print("Открывай: http://127.0.0.1:8000")

    socketio.run(
        app,
        host="0.0.0.0",
        port=8000,
        debug=False
    )
