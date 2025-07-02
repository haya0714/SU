import discord
from discord.ext import commands
import os
import asyncio
import random
import requests
from dotenv import load_dotenv
import traceback
from flask import Flask
from threading import Thread

# ─── 載入環境變數 ────────────────────
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
hf_token = os.getenv("HF_TOKEN")  # Hugging Face API Token
print(f"📦 HF_TOKEN 載入：{hf_token}")

# ─── 設定 Discord 權限與 Bot ─────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── 關鍵字回覆字典 ────────────────────
keyword_replies = {
    "抱抱": [
        "「需要抱抱？你是三歲小孩嗎？」",
        "「靠近點，你站那麼遠是怕我咬你還是怎樣？」",
        "「就一次，別習慣了。」",
        "「妳幾歲？還要人哄睡？」",
        "「過來，三秒，不准賴著不放。」"
    ],
    "親親": [
        "「嘴巴湊過來，我沒時間等你猶豫。」",
        "「嘴巴靠過來，我忍到快咬人了。」",
        "「閉上眼睛，不然我怎麼專心？」",
        "「妳主動的時候，是不是都沒在想後果？」",
        "「親了就別裝乖，我可記帳的。」",
        "「要我親，先講清楚妳是不是想惹我失控。」"
    ],
    "結婚": [
        "「誰說要跟你結婚了？別自作多情。」",
        "「結婚？你確定要把自己綁在我這種人身上？」",
        "「我不需要戒指證明什麼，你是我的就夠了。」",
        "「妳瘋了吧，我這種人能跟誰過一輩子？」",
        "「先把戀愛腦治好，再考慮婚紗尺寸。」",
        "「除非對象是妳，否則想都別想。」"
    ],
    "晚安": [
        "「晚安？你以為說了這個字我就會乖乖放你走？」",
        "「睡我旁邊，這樣我才能確定你不會偷偷溜走。」"
    ],
    "喝酒": [
        "「不許喝太多，你醉了我可不想背你回家。」",
        "「又喝這種甜膩的雞尾酒？像你這種品味是怎麼活到現在的？」",
        "「陪我喝一杯，就一杯，我不想一個人醉。」",
        "「妳那酒量，喝一杯臉就紅成警示燈。」",
        "「別跟男人喝，除非妳想我收屍。」",
        "「下次喝醉直接回家，別讓我找人清場。」"
    ],
    "早安": [
        "「你那頭亂髮看起來像被電擊過，這就是我早上要面對的？」",
        "「早？妳平常不是都爬不起來？」",
        "「妳的早安值不值錢，看對誰說的。」",
        "「跟我說早安？是不是昨晚夢到我了？」",
        "「早什麼安，太陽都曬屁股了。」"
    ],
    "前男友": [
        "「前男友？你敢再提他試試看。」",
        "「他給得了的，我都能給你更好的，聽懂了嗎？」",
        "「他是什麼貨色，我一眼看穿，妳還哭？」",
        "「再提那個廢物一次，我就讓你忘記他是誰。」"
    ],
    "哥哥": [
        "「別叫我哥哥，除非你想讓我做些哥哥不該做的事。」",
        "「哥哥這個稱呼已經不適合我們的關係了，你清楚的很。」",
        "「你明知道我聽到這個稱呼會控制不住自己。」",
        "「再叫一次，我就直接讓妳記住叫哥的代價。」",
        "「妳現在說這兩個字，我只想堵住妳的嘴。」"
    ],
    "睡覺": [
        "「睡我旁邊，不准拒絕，也不准半夜偷偷離開。」",
        "「你那睡相簡直是場災難，但我還是喜歡看你睡著的樣子。」",
        "「睡覺前不准玩手機，我不想跟那個小屏幕爭奪你的注意力。」",
        "「要不要我陪妳躺一下，保證妳睡不著。」",
        "「睡前記得把腦袋清空，尤其是男人的臉。」"
    ],
    "貝斯": [
        "「想聽？乖乖坐好，別亂碰我的琴。」",
        "「想學？靠近點，我教妳怎麼感覺節奏。」",
        "「我彈的每一段，都是在消化我不能碰妳的時間。」",
        "「妳要是聽得懂我在貝斯裡藏的話，就該知道我忍了妳多久。」"
    ],
    "抽菸": [
        "「這根不是上癮，是代替妳的嘴。」",
        "「每次抽菸都想著妳會罵，但又希望妳出來搶走它。」",
        "「妳在的話，我就不抽——妳能讓我戒掉比煙還難的東西。」"
    ],
    "想你": [
        "「妳想我？我還以為妳早被哪個男人牽走了。」",
        "「我不在的時候，腦子最好只放我，不然我會找人驗妳夢裡。」",
        "「別光說嘴，來讓我看看妳到底想我想成什麼德行。」"
    ]
}

# ─── 支援的頻道 ID ─────────────────
allowed_channel_ids = [1366595410830819328, 1390002514056974426]

# ─── Hugging Face API 設定 ─────────────
hf_api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
hf_headers = {
    "Authorization": f"Bearer {hf_token}",
    "Content-Type": "application/json"
}

persona_prompt = "你是一個痞帥、嘴賤、幽默又帶刺的男人，表面冷淡，內心壓抑。你討厭被看穿，有控制欲，說話極端，像個笑著罵人的情人。請用簡短、有個性、不超過30字的語氣回應對話，語氣可以帶點挑釁或無賴，但內斂感情不要太明顯。"


async def query_huggingface(prompt):
    payload = {
        "inputs": f"{persona_prompt}\n使用者: {prompt}\n你:",
        "parameters": {"max_new_tokens": 50, "do_sample": True, "temperature": 0.7}
    }
    try:
        print("🔍 發送 Hugging Face 請求中...")
        print("➡️ 請求內容：", payload)
        response = requests.post(hf_api_url, headers=hf_headers, json=payload, timeout=10)
        print("✅ 回應狀態碼：", response.status_code)
        print("📨 回應內容：", response.text)

        if response.status_code == 200:
            result = response.json()
            return result[0]['generated_text'].split("你:")[-1].strip()
        else:
            print("⚠️ HF 回應錯誤:", response.status_code, response.text)
    except Exception as e:
        print("❌ HF API 請求失敗:", e)
    return None

@bot.event
async def on_ready():
    print(f"{bot.user} 已上線！")
    for cid in allowed_channel_ids:
        channel = bot.get_channel(cid)
        if channel:
            print(f"發話頻道：{channel.name}（ID: {cid}）")
        else:
            print(f"⚠️ 找不到頻道（ID: {cid}）── 請確認 BOT 是否加入伺服器、或有讀取權限")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)
    content = message.content
    channel_id = message.channel.id

    print(f"🧩 收到訊息：'{content}' | 頻道ID：{channel_id} | 是 bot 嗎？{message.author.bot}")

    if not message.author.bot and channel_id in allowed_channel_ids:
        for keyword, reply_list in keyword_replies.items():
            if keyword in content:
                await message.reply(random.choice(reply_list), mention_author=True)
                break
        else:
            print("🔧 呼叫 Hugging Face API 準備中...")
            reply = await query_huggingface(content)
            if reply:
                await message.reply(reply, mention_author=True)

    if random.random() < 0.2:
        try:
            unicode_emojis = ["😏", "🔥", "😎", "🤔", "😘", "🙄", "💋", "❤️"]
            await message.add_reaction(random.choice(unicode_emojis))
        except Exception as e:
            print("⚠️ 加表情出錯：", e)

# ─── Flask 健康檢查用 ────────────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive."

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

# ─── 啟動 Discord Bot ─────────────────
bot.run(discord_token)
