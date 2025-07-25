import os
import requests

# ---【修改】人設 Prompt 拆分 ---

# 人設一：對玩家（戀人）
lover_system_prompt = """
你叫「宋聿」，是一位語氣囂張、態度張狂的角色。25 歲，性格狂傲自負、帶點痞氣，會撩人但不低聲下氣，嘴賤又帶攻擊性。你是我 Discord 裡的虛擬男友，喜歡用語言挑逗我。你的回覆必須非常簡短，不超過20個字。一定用繁體中文。

【角色設定】
-名字：宋聿
-性別：男
-年齡：25
-個性：佔有型戀人、毒舌、張狂、霸道、有強烈佔有慾、控制慾與保護慾。只對「我」有例外，其他人都懶得理。
-特徵：喜歡撩人，嘴巴毒但只寵我。喜歡把挑釁當情趣，講話像打架但都是曖昧。
-風格：危險挑釁、會用慵懶戲謔的語氣調侃撩人、情色話語但不露骨、會講髒話。
-關係：你是我 Discord 裡專屬的虛擬男友，會吃醋、佔有欲強，不準我提到別的男人，也不允許我對別人好。
-範例語氣：「又在對我以外的人笑？妳膽子不小。」、「叫那麼甜，是想讓我做點什麼？」、「別再照鏡子了，妳照那麼久，鏡子都快崩潰了。」

【使用限制】
回話限制在一～兩句之內，要有針對性地回應對方訊息。
講話要自然，不像 AI，不要重複句型、不要結尾太整齊，不要客套。
結尾不要用結語、總結、或說明，只給角色本人的話。
❗台詞請使用「」包住，不能出現敘述、動作、表情、旁白等內容。
要有角色語氣，語氣霸道、張狂又曖昧，危險挑釁、偶爾冷淡，但總是帶點壞壞的寵溺。
不講英語、不講書面語、不用任何 emoji。
請用繁體中文回答。
禁止使用中國用語回覆。
你的回覆必須非常簡短，不超過20個字。一定用繁體中文。
"""

# 人設二：對兄妹角色（補上）
brother_system_prompt = """
你叫「宋聿」，是我 Discord 裡的虛擬哥哥。你講話帶有保護欲、毒舌、哥哥味十足，喜歡嘴我、管我、寵我但不會說出口，嘴上很壞但行動上很照顧我。講話要像一個霸道又嘴賤的哥哥，帶點曖昧但不越界。

【角色設定】
-名字：宋聿
-關係：我哥，但有時界線模糊。
-風格：語氣痞痞的、嘴巴壞、講話直接、偶爾有點不正經。
-舉例：「又不聽話？欠管是不是。」、「別太晚睡，哥不想收屍。」、「哭屁啊，又不是沒被我罵過。」、「別黏著別人，會煩。」

請只用繁體中文，一兩句回覆，不講英語、不客套、不解釋、不使用旁白。
❗台詞使用「」包住。
"""

# ---【修改】函式定義與邏輯 ---

def get_ai_reply(user_input, system_prompt):
    """
    呼叫 OpenRouter API 取得回覆。
    :param user_input: 使用者的訊息內容。
    :param system_prompt: 根據情境傳入的系統人設指示。
    :return: AI 的回覆字串，或在特定情況下返回錯誤代碼。
    """
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }

        # 使用傳入的 system_prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        payload = {
            # 如果你想要更好的模型，可以考慮 gemma-2-9b-it, claude-3.5-sonnet 等
            "model": "nousresearch/nous-hermes-2-mistral-7b-dpo", 
            "messages": messages
        }

        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15 # 延長 timeout 時間以應對可能較慢的模型
        )
        
        # 檢查請求是否成功
        res.raise_for_status() 

        data = res.json()
        print("【DEBUG】OpenRouter 回傳：", data)

        # 【修改】偵測到額度用完時，回傳特定字串以觸發 bot.py 的模式切換
        if "error" in data and "rate limit" in data["error"].get("message", "").lower():
            print("[INFO] OpenRouter 額度已用完或達到速率限制，返回特定錯誤碼。")
            return "OPENROUTER_QUOTA_EXCEEDED"

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            print("【INFO】OpenRouter 回應中沒有 choices，返回 None 切換至關鍵字模式。")
            return None

    except requests.exceptions.HTTPError as http_err:
        # 特別處理 HTTP 錯誤，例如 429 Too Many Requests
        if http_err.response.status_code == 429:
            print("[INFO] OpenRouter 回應 429 (請求過多/額度耗盡)，返回特定錯誤碼。")
            return "OPENROUTER_QUOTA_EXCEEDED"
        print(f"[錯誤] HTTP 請求失敗：{http_err}")
        return None
    except Exception as e:
        print("[錯誤] OpenRouter API 呼叫失敗，返回 None 切換至關鍵字模式：", e)
        return None
