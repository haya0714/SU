from utils import get_ai_reply, lover_system_prompt  # <-- 已移除 brother_system_prompt

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
    1400434026124410951,
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

    # --- 基本的訊息過濾，維持不變 ---
    if message.author == bot.user:
        return
    if message.reference and message.reference.resolved and message.reference.resolved.author == bot.user:
        return
    if message.channel.id not in allowed_channel_ids:
        return
    
    # --- 判斷是否為觸發條件 ---
    # 僅當真人使用者 @Bot 時觸發
    if not (not message.author.bot and bot.user in message.mentions):
        return

    # 在處理訊息前先處理指令
    await bot.process_commands(message)

    content = message.content
    reply_content = None # 先宣告一個變數來儲存最終要回覆的內容

    # --- 步驟一：決定回覆內容 (AI 優先) ---
    if openrouter_available:
        # 呼叫 AI，我們知道 get_ai_reply 內部有完整的錯誤處理
        ai_reply = get_ai_reply(content, system_prompt=lover_system_prompt)

        if ai_reply == "OPENROUTER_QUOTA_EXCEEDED":
            openrouter_offline()
            # AI 額度用完，ai_reply 視為 None，交由後續的關鍵字邏輯處理
        elif ai_reply:
            reply_content = ai_reply
    
    # --- 步驟二：如果 AI 沒有回覆，則嘗試關鍵字回覆 ---
    if not reply_content:
        for keyword, reply_list in keyword_replies.items():
            if keyword in content:
                reply_content = random.choice(reply_list)
                break # 找到第一個匹配的關鍵字就跳出

    # --- 步驟三：如果最終有回覆內容，則發送回覆 ---
    if reply_content:
        await message.reply(reply_content)

    # --- 步驟四：無論是否有回覆，都執行表情符號邏輯 ---
    # 這樣可以實現：有時就算 Bot 不回話，也會默默給你一個反應
    try:
        # 40% 的機率添加一個表情符號反應
        if random.random() < 0.4:
            unicode_emojis = ["😏", "😎", "🔥", "😘", "🙄", "💋", "❤️"]
            await message.add_reaction(random.choice(unicode_emojis))
    except Exception as e:
        print(f"⚠️ 表情符號添加失敗：{e}")

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
