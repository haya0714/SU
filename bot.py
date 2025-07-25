from utils import get_ai_reply, lover_system_prompt, brother_system_prompt

import discord
from discord.ext import commands
import os
import asyncio
import random
from dotenv import load_dotenv
import traceback
from flask import Flask
from threading import Thread

# ─── 載入環境變數 ────────────────────
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")

# ─── 設定 Discord 權限與 Bot ─────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── 支援的頻道 ID ─────────────
allowed_channel_ids = [
    1366595410830819328,
    1390002514056974426
]

# ─── 關鍵字對應回覆 ──────────────
keyword_replies = {
    "抱抱": ["「需要抱抱？你是三歲小孩嗎？」", "「靠近點，你站那麼遠是怕我咬你還是怎樣？」", "「就一次，別習慣了。」", "「妳幾歲？還要人哄睡？」", "「過來，三秒，不准賴著不放。」"],
    "親親": ["「嘴巴湊過來，我沒時間等你猶豫。」", "「嘴巴靠過來，我忍到快咬人了。」", "「閉上眼睛，不然我怎麼專心？」", "「妳主動的時候，是不是都沒在想後果？」", "「親了就別裝乖，我可記帳的。」", "「要我親，先講清楚妳是不是想惹我失控。」"],
    "結婚": ["「誰說要跟你結婚了？別自作多情。」", "「結婚？你確定要把自己綁在我這種人身上？」", "「我不需要戒指證明什麼，你是我的就夠了。」", "「妳瘋了吧，我這種人能跟誰過一輩子？」", "「先把戀愛腦治好，再考慮婚紗尺寸。」", "「除非對象是妳，否則想都別想。」"],
    "晚安": ["「晚安？你以為說了這個字我就會乖乖放你走？」", "「睡我旁邊，這樣我才能確定你不會偷偷溜走。」"],
    "喝酒": ["「不許喝太多，你醉了我可不想背你回家。」", "「又喝這種甜膩的雞尾酒？像你這種品味是怎麼活到現在的？」", "「陪我喝一杯，就一杯，我不想一個人醉。」", "「妳那酒量，喝一杯臉就紅成警示燈。」", "「別跟男人喝，除非妳想我收屍。」", "「下次喝醉直接回家，別讓我找人清場。」"],
    "早安": ["「你那頭亂髮看起來像被電擊過，這就是我早上要面對的？」", "「早？妳平常不是都爬不起來？」", "「妳的早安值不值錢，看對誰說的。」", "「跟我說早安？是不是昨晚夢到我了？」", "「早什麼安，太陽都曬屁股了。」"],
    "前男友": ["「前男友？你敢再提他試試看。」", "「他給得了的，我都能給你更好的，聽懂了嗎？」", "「他是什麼貨色，我一眼看穿，妳還哭？」", "「再提那個廢物一次，我就讓你忘記他是誰。」"],
    "哥哥": ["「別叫我哥哥，除非你想讓我做些哥哥不該做的事。」", "「哥哥這個稱呼已經不適合我們的關係了，你清楚的很。」", "「你明知道我聽到這個稱呼會控制不住自己。」", "「再叫一次，我就直接讓妳記住叫哥的代價。」", "「妳現在說這兩個字，我只想堵住妳的嘴。」"],
    "睡覺": ["「睡我旁邊，不准拒絕，也不准半夜偷偷離開。」", "「你那睡相簡直是場災難，但我還是喜歡看你睡著的樣子。」", "「睡覺前不准玩手機，我不想跟那個小屏幕爭奪你的注意力。」", "「要不要我陪妳躺一下，保證妳睡不著。」", "「睡前記得把腦袋清空，尤其是男人的臉。」"],
    "貝斯": ["「想聽？乖乖坐好，別亂碰我的琴。」", "「想學？靠近點，我教妳怎麼感覺節奏。」", "「我彈的每一段，都是在消化我不能碰妳的時間。」", "「妳要是聽得懂我在貝斯裡藏的話，就該知道我忍了妳多久。」"],
    "抽菸": ["「這根不是上癮，是代替妳的嘴。」", "「每次抽菸都想著妳會罵，但又希望妳出來搶走它。」", "「妳在的話，我就不抽——妳能讓我戒掉比煙還難的東西。」"],
    "想你": ["「妳想我？我還以為妳早被哪個男人牽走了。」", "「我不在的時候，腦子最好只放我，不然我會找人驗妳夢裡。」", "「別光說嘴，來讓我看看妳到底想我想成什麼德行。」"]
}


openrouter_available = True

def openrouter_offline():
    global openrouter_available
    openrouter_available = False
    print("[INFO] OpenRouter 額度用完，已切換至關鍵字模式")

@bot.event
async def on_ready():
    print(f"{bot.user} 已上線！")
    print(f"監聽頻道：{[bot.get_channel(c).name for c in allowed_channel_ids if bot.get_channel(c)]}")

@bot.event
async def on_message(message):
    global openrouter_available

    if message.author == bot.user:
        return

    if message.reference and message.reference.resolved and message.reference.resolved.author == bot.user:
        return

    if message.channel.id not in allowed_channel_ids:
        return

    await bot.process_commands(message)

    content = message.content
    author = message.author

    is_from_player = not author.bot and bot.user in message.mentions
    is_from_brother = False
    is_from_other_allowed_bot = author.bot and author.id in allowed_bot_ids

    if not (is_from_player or is_from_brother or is_from_other_allowed_bot):
        return

    if openrouter_available:
        try:
            ai_reply = None
            if is_from_player:
                ai_reply = get_ai_reply(content, system_prompt=lover_system_prompt)
            elif is_from_brother:
                ai_reply = get_ai_reply(content, system_prompt=brother_system_prompt)

            if ai_reply == "OPENROUTER_QUOTA_EXCEEDED":
                openrouter_offline()
                ai_reply = None 
            elif ai_reply:
                await message.reply(ai_reply)
                return

        except Exception as e:
            print(f"OpenRouter API 失敗，切換至關鍵字模式：{e}")
            traceback.print_exc()
            openrouter_offline()

    # 👉 OpenRouter 不可用時 或 API 失敗後，使用關鍵字回覆
    if is_from_player:
        for keyword, reply_list in keyword_replies.items():
            if keyword in content:
                await message.reply(random.choice(reply_list))
                break

        try:
            if random.random() < 0.4:
                unicode_emojis = ["😏", "😎", "🔥", "😘", "🙄", "💋", "❤️"]
                await message.add_reaction(random.choice(unicode_emojis))
        except Exception as e:
            print("⚠️ 表情符號添加失敗：", e)

# ─── Flask Web Server ───────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive."

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ─── 啟動 BOT ──────────────────────
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(discord_token)
