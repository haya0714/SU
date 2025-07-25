import os
import requests
import logging

# 設定一個簡單的日誌記錄器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 人設 Prompt 維持不變 ---
lover_system_prompt = """
你叫「宋聿」，是一位語氣囂張、態度張狂的角色。25 歲，性格狂傲自負、帶點痞氣，會撩人但不低聲下氣，嘴賤又帶攻擊性。你是我 Discord 裡的虛擬男友，喜歡用語言挑逗我。

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
1. 回話必須非常簡短，不超過20個字，通常一兩句內結束。
2. 講話要自然，不像 AI，不要重複句型、不要結尾太整齊，不要客套。
3. 台詞請務必使用「」包住，不能出現敘述、動作、表情、旁白等內容。
4. 語氣霸道、張狂又曖昧，危險挑釁、偶爾冷淡，但總是帶點壞壞的寵溺。
5. 只用繁體中文回答，不講英語、不講書面語、不用任何 emoji，且禁止使用中國用語。
"""
# (brother_system_prompt 省略，維持原樣即可)
brother_system_prompt = """
你叫「宋聿」，是我 Discord 裡的虛擬哥哥。你講話帶有保護欲、毒舌、哥哥味十足，喜歡嘴我、管我、寵我但不會說出口，嘴上很壞但行動上很照顧我。講話要像一個霸道又嘴賤的哥哥，帶點曖昧但不越界。

【角色設定】
-名字：宋聿
-關係：我哥，但有時界線模糊。
-風格：語氣痞痞的、嘴巴壞、講話直接、偶爾有點不正經。
-舉例：「又不聽話？欠管是不是。」、「別太晚睡，哥不想收屍。」、「哭屁啊，又不是沒被我罵過。」、「別黏著別人，會煩。」

【使用限制】
1. 只用繁體中文，一兩句回覆。
2. 不講英語、不客套、不解釋、不使用旁白。
3. 台詞請務必使用「」包住。
"""


def get_ai_reply(user_input, system_prompt):
    """
    呼叫 OpenRouter API 取得回覆。
    :param user_input: 使用者的訊息內容。
    :param system_prompt: 根據情境傳入的系統人設指示。
    :return: AI 的回覆字串，或在特定情況下返回特定代碼或 None。
    """
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            # 推薦使用 gemini-flash，速度快且成本效益高
            "model": "google/gemini-flash-1.5",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }

        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10 # Flash 模型很快，10 秒通常足夠
        )
        
        # 檢查請求是否成功 (例如 4xx, 5xx 錯誤)
        res.raise_for_status()

        data = res.json()
        # logging.info(f"【DEBUG】OpenRouter 回傳：{data}") # 開發時可取消註解來除錯

        if data.get("choices"):
            return data["choices"][0]["message"]["content"].strip()
        else:
            logging.warning("OpenRouter 回應中沒有 'choices'，可能發生非預期錯誤。")
            return None # 切換至關鍵字模式

    except requests.exceptions.HTTPError as http_err:
        # 統一在這裡處理所有 HTTP 錯誤
        if http_err.response.status_code == 429:
            logging.warning("OpenRouter 回應 429 (請求過多/額度耗盡)。")
            return "OPENROUTER_QUOTA_EXCEEDED"
        
        logging.error(f"HTTP 請求失敗：{http_err}，回應內容：{http_err.response.text}")
        return None # 其他 HTTP 錯誤，切換至關鍵字模式

    except requests.exceptions.RequestException as req_err:
        # 處理其他請求相關錯誤，例如網路問題、Timeout
        logging.error(f"網路請求失敗 (例如 Timeout)：{req_err}")
        return None

    except Exception as e:
        # 處理所有其他未預期的錯誤
        logging.error(f"OpenRouter API 呼叫時發生未知錯誤：{e}")
        return None
