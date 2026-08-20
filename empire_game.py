# empire_game.py
# ملف لعبة حرب الإمبراطوريات الأسطورية - تصميم كرتوني ثلاثي الأبعاد فاخر وإدارة تفاعلية متكاملة باللغة العربية

import sqlite3
import os
import io
import random
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import ContextTypes

# إعداد قاعدة البيانات الخاصة باللعبة
DB_PATH = "empire_game.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # جدول الإمبراطوريات / اللاعبين مع نظام الدروع، الجنود، والمدرعات الحربية
    cursor.execute('''CREATE TABLE IF NOT EXISTS empires (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        empire_name TEXT,
                        alliance_id INTEGER,
                        gold INTEGER DEFAULT 1500,
                        soldiers INTEGER DEFAULT 150,
                        armored_vehicles INTEGER DEFAULT 5,
                        shields INTEGER DEFAULT 5,
                        territories_count INTEGER DEFAULT 1,
                        color_code TEXT
                    )''')
                    
    # جدول المقاطعات الخريطة (شبكة 4x4 مع مستويات وأنواع إنتاج)
    cursor.execute('''CREATE TABLE IF NOT EXISTS territories (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        owner_id INTEGER,
                        level INTEGER DEFAULT 1,
                        facility_type TEXT DEFAULT 'مزارع',
                        FOREIGN KEY(owner_id) REFERENCES empires(user_id)
                    )''')
                    
    conn.commit()
    conn.close()
    
    _seed_territories()

def _seed_territories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM territories")
    if cursor.fetchone()[0] == 0:
        names = ["بابل", "روما", "أثينا", "الإسكندرية", "قرطبة", "دمشق", "القسطنطينية", "قرطاج",
                 "طروادة", "سبارتا", "بغداد", "نينوى", "سوسة", "تدمر", "البتراء", "أوغاريت"]
        for i, name in enumerate(names):
            cursor.execute("INSERT INTO territories (id, name, owner_id) VALUES (?, ?, NULL)", (i+1, name))
        conn.commit()
    conn.close()

init_db()

# ==========================================
# محرك رسم الخريطة بتقنية كرتونية ثلاثية الأبعاد فاخرة (باللون الكحلي والذهبي الملكي)
# ==========================================
def generate_3d_map_image():
    width, height = 1400, 1200
    # خلفية باللون الأزرق الداكن الفاخر (Midnight Blue)
    image = Image.new("RGB", (width, height), color=(11, 19, 43))
    draw = ImageDraw.Draw(image)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT T.id, T.name, T.owner_id, E.empire_name, E.color_code 
        FROM territories T 
        LEFT JOIN empires E ON T.owner_id = E.user_id
    """)
    territories = cursor.fetchall()
    conn.close()

    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font = font_title
        font_small = font_title

    # رسم عنوان فاخر أعلى الخريطة باللون الذهبي المطفي
    draw.text((420, 35), "👑 خريطة إمبراطورية مونوبولي الاستراتيجية الأسطورية 👑", fill=(212, 175, 55), font=font_title)

    start_x, start_y = 380, 150
    tile_w, tile_h = 220, 110

    idx = 0
    for row in range(4):
        for col in range(4):
            x = start_x + (col * 140) - (row * 140)
            y = start_y + (row * 90) + (col * 90)
            
            t_data = territories[idx] if idx < len(territories) else None
            
            # ألوان بتصميم كرتوني متناسق مع الأستيل الملكي (كحلي مع إطار ذهبي بارز)
            box_color = (25, 35, 65)
            border_color = (212, 175, 55)
            owner_text = "منطقة محايدة"
            
            if t_data and t_data[2] is not None:
                owner_text = t_data[3] if t_data[3] else "مملكة المسيطر"
                if t_data[4]:
                    try:
                        hex_c = t_data[4].lstrip('#')
                        box_color = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
                    except:
                        box_color = (60, 40, 90)

            points = [
                (x, y + tile_h // 2),
                (x + tile_w // 2, y),
                (x + tile_w, y + tile_h // 2),
                (x + tile_w // 2, y + tile_h)
            ]
            
            # رسم المربع مع تأثير ثلاثي الأبعاد بارز
            draw.polygon(points, fill=box_color, outline=border_color)
            
            t_name = t_data[1] if t_data else f"منطقة {idx+1}"
            
            draw.text((x + 65, y + 30), f"🏰 {t_name}", fill=(255, 255, 255), font=font)
            draw.text((x + 40, y + 60), f"👤 {owner_text[:14]}", fill=(212, 175, 55), font=font_small)
            
            idx += 1

    bio = io.BytesIO()
    bio.name = 'empire_map.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ==========================================
# واجهة الأوامر والأزرار
# ==========================================
def get_main_game_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🗺️ عرض الخريطة", callback_data="عرض الخريطة"),
            InlineKeyboardButton("🛡️ دروع الدفاع", callback_data="دروع الدفاع")
        ],
        [
            InlineKeyboardButton("⚔️ التجنيد", callback_data="التجنيد"),
            InlineKeyboardButton("🏛️ المقاطعات", callback_data="المقاطعات")
        ],
        [
            InlineKeyboardButton("💰 الخزينة", callback_data="الخزينة"),
            InlineKeyboardButton("🎯 قائمة الهجوم", callback_data="قائمة الهجوم")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# أمر الانضمام وبناء الإمبراطورية
async def start_empire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.first_name

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empires WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()

    if not existing:
        royal_colors = ["#1B365D", "#4A154B", "#2C5E1A", "#6E2C00", "#4A235A", "#154360"]
        chosen_color = random.choice(royal_colors)
        
        cursor.execute("INSERT INTO empires (user_id, username, empire_name, color_code) VALUES (?, ?, ?, ?)",
                       (user_id, username, f"إمبراطورية {username}", chosen_color))
        conn.commit()
        
        cursor.execute("SELECT id FROM territories WHERE owner_id IS NULL LIMIT 1")
        free_t = cursor.fetchone()
        if free_t:
            cursor.execute("UPDATE territories SET owner_id = ?, facility_type = 'مزارع' WHERE id = ?", (user_id, free_t[0]))
            conn.commit()
            
        conn.close()
        await update.message.reply_text(
            f"👑 **تهانينا يا قائد {username}!**\n"
            f"تم تأسيس إمبراطوريتك العظمى بنجاح وتم منحك مقاطعة البداية مع رصيد وافر لتبدأ رحلة المجد.\n\n"
            f"استخدم اللوحة أدناه لتدير إمبراطوريتك:",
            reply_markup=get_main_game_keyboard(),
            parse_mode="Markdown"
        )
    else:
        conn.close()
        await update.message.reply_text(
            f"🏰 **أهلاً بك مجدداً يا جلالة الإمبراطور {username}!**\n"
            f"إمبراطوريتك منتظرة أوامرك العسكرية:",
            reply_markup=get_main_game_keyboard(),
            parse_mode="Markdown"
        )

# معالجة تفاعل الأزرار بطريقة آمنة ومتكاملة تمنع أخطاء التعديل
async def handle_game_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "عرض الخريطة":
        map_file = generate_3d_map_image()
        try:
            # إذا كانت الرسالة السابقة تحتوي على صورة، نقوم بتعديلها عبر InputMediaPhoto لمنع الأخطاء
            if query.message.photo:
                await query.message.edit_media(
                    media=InputMediaPhoto(media=map_file, caption="🗺️ **خريطة العالم الاستراتيجية (ثلاثية الأبعاد)**\nالمناطق الملونة تعود للأباطرة المسيطرين!", parse_mode="Markdown"),
                    reply_markup=get_main_game_keyboard()
                )
            else:
                await query.message.reply_photo(
                    photo=map_file,
                    caption="🗺️ **خريطة العالم الاستراتيجية (ثلاثية الأبعاد)**\nالمناطق الملونة تعود للأباطرة المسيطرين!",
                    reply_markup=get_main_game_keyboard(),
                    parse_mode="Markdown"
                )
        except Exception:
            await query.message.reply_photo(
                photo=map_file,
                caption="🗺️ **خريطة العالم الاستراتيجية (ثلاثية الأبعاد)**\nالمناطق الملونة تعود للأباطرة المسيطرين!",
                reply_markup=get_main_game_keyboard(),
                parse_mode="Markdown"
            )
        
    elif data == "دروع الدفاع":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT shields, gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        shields, gold = res if res else (5, 0)
        
        await safe_edit_or_reply(query, 
            f"🛡️ **نظام دروع الحماية الملكية**\n\n"
            f"دروعك الحالية: **{shields} من 5 دروع** (الحد الأقصى).\n"
            f"• كل هجوم يتعرض له دفاعك يستهلك درعاً واحداً.\n"
            f"• تكلفة شحن درع جديد: **200 قطعة ذهب**.\n\n"
            f"رصيدك الحالي في الخزينة: 💰 {gold} ذهبة",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("شراء درع جديد", callback_data="شراء درع")],
                [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
            ])
        )
        
    elif data == "شراء درع":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT shields, gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        
        if res:
            shields, gold = res
            if shields >= 5:
                await query.answer("دروعك في الحد الأقصى (5 دروع)! لا تحتاج للمزيد حالياً.", show_alert=True)
            elif gold < 200:
                await query.answer("عفواً، رصيدك من الذهب لا يكفي لشراء درع (تحتاج 200 ذهب).", show_alert=True)
            else:
                cursor.execute("UPDATE empires SET shields = shields + 1, gold = gold - 200 WHERE user_id = ?", (user_id,))
                conn.commit()
                await query.answer("تم شراء وشحن درع دفاعي بنجاح!", show_alert=True)
        conn.close()
        
        await handle_game_callbacks_refresh_shields(query, user_id)

    elif data == "التجنيد":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT soldiers, armored_vehicles, gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        soldiers, armored, gold = res if res else (150, 5, 0)
        
        await safe_edit_or_reply(query,
            f"⚔️ **ثكنة تجنيد الجيش والمدرعات الحربية**\n\n"
            f"• جنودك الحاليون: **{soldiers} جندي**\n"
            f"• مدرعاتك الحربية: **{armored} مدرعة**\n\n"
            f"خيارات التجنيد المتاحة:\n"
            f"1. تجنيد 50 جندي (التكلفة: 100 ذهب)\n"
            f"2. صنع مدرعة حربية ثقيلة (التكلفة: 200 ذهب)",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("تجنيد جنود", callback_data="تجنيد جنود")],
                [InlineKeyboardButton("صنع مدرعة", callback_data="صنع مدرعة")],
                [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
            ])
        )

    elif data == "تجنيد جنود":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        if res and res[0] >= 100:
            cursor.execute("UPDATE empires SET soldiers = soldiers + 50, gold = gold - 100 WHERE user_id = ?", (user_id,))
            conn.commit()
            await query.answer("تم تجنيد 50 جندي بنجاح وانضموا لصفوف جيشك!", show_alert=True)
        else:
            await query.answer("رصيدك من الذهب لا يكفي لتجنيد الجنود (تحتاج 100 ذهب).", show_alert=True)
        conn.close()
        await handle_game_callbacks_refresh_recruitment(query, user_id)

    elif data == "صنع مدرعة":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        if res and res[0] >= 200:
            cursor.execute("UPDATE empires SET armored_vehicles = armored_vehicles + 1, gold = gold - 200 WHERE user_id = ?", (user_id,))
            conn.commit()
            await query.answer("تم تصنيع مدرعة حربية ثقيلة بنجاح!", show_alert=True)
        else:
            await query.answer("رصيدك من الذهب لا يكفي لصنع مدرعة (تحتاج 200 ذهب).", show_alert=True)
        conn.close()
        await handle_game_callbacks_refresh_recruitment(query, user_id)

    elif data == "المقاطعات":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, level, facility_type FROM territories WHERE owner_id = ?", (user_id,))
        territories = cursor.fetchall()
        conn.close()

        text = "🏛️ **إدارة مقاطعاتك ومستويات الإنتاج**\n\n• من المستوى 1 إلى 5: (تجميع سريع وسهل للذهب)\n• من المستوى 6 فما فوق: (صعوبة متوسطة وتتطلب استراتيجية)\n\nمناطقك الحالية:\n"
        keyboard_buttons = []
        for t in territories:
            t_id, t_name, t_lvl, t_fac = t
            text += f"• **{t_name}** | المستوى: {t_lvl} | المنشأة: {t_fac}\n"
            keyboard_buttons.append([InlineKeyboardButton(f"ترقية {t_name}", callback_data=f"ترقية {t_id}")])

        keyboard_buttons.append([InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")])
        
        await safe_edit_or_reply(query, text, InlineKeyboardMarkup(keyboard_buttons))

    elif data.startswith("ترقية "):
        t_id = int(data.split(" ")[1])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT level, facility_type FROM territories WHERE id = ? AND owner_id = ?", (t_id, user_id))
        t_data = cursor.fetchone()
        
        if t_data:
            current_lvl, current_fac = t_data
            cursor.execute("SELECT gold FROM empires WHERE user_id = ?", (user_id,))
            gold_res = cursor.fetchone()
            gold = gold_res[0] if gold_res else 0
            
            upgrade_cost = (current_lvl * 150) if current_lvl <= 5 else (current_lvl * 500)
            
            if gold < upgrade_cost:
                await query.answer(f"الذهب غير كافٍ للترقية! تحتاج إلى {upgrade_cost} قطعة ذهبية.", show_alert=True)
            else:
                new_fac = "منجم ذهب أسطوري" if current_fac == "مزارع" else "مزارع"
                cursor.execute("UPDATE territories SET level = level + 1, facility_type = ? WHERE id = ?", (new_fac, t_id))
                cursor.execute("UPDATE empires SET gold = gold - ? WHERE user_id = ?", (upgrade_cost, user_id))
                conn.commit()
                await query.answer(f"تم ترقية المقاطعة بنجاح إلى المستوى {current_lvl + 1}!", show_alert=True)
        conn.close()
        
        await safe_edit_or_reply(query, "🏰 **تمت ترقية المقاطعة بنجاح وزادت قدرتها الإنتاجية!**", get_main_game_keyboard())

    elif data == "الخزينة":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT gold, soldiers, armored_vehicles, territories_count FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        gold, soldiers, armored, territories_count = res if res else (1500, 150, 5, 1)
        
        await safe_edit_or_reply(query,
            f"💰 **الخزينة الملكية والموارد العامة**\n\n"
            f"• رصيد الذهب: **{gold} قطعة ذهبية**\n"
            f"• جنود الجيش: **{soldiers} جندي**\n"
            f"• المدرعات الحربية: **{armored} مدرعة**\n"
            f"• المقاطعات المسيطر عليها: **{territories_count} مقاطعة**\n\n"
            f"تذكر: الترقية من المستوى 1 إلى 5 سهلة وسريعة، وبعد المستوى 5 تصبح التكلفة والصعوبة متوسطة لتحدي الأباطرة!",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
            ])
        )

    elif data == "قائمة الهجوم":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT T.id, T.name, T.owner_id, E.username FROM territories T LEFT JOIN empires E ON T.owner_id = E.user_id WHERE T.owner_id IS NULL OR T.owner_id != ?", (user_id,))
        targets = cursor.fetchall()
        conn.close()

        if not targets:
            await query.answer("لا توجد مقاطعات متاحة للهجوم حالياً، سيطرت على الخريطة بأكملها!", show_alert=True)
            return

        text = "⚔️ **قائمة أهداف الغزو العسكري المتاحة:**\nاختر مقاطعة لشن الهجوم عليها وسلب مواردها:\n"
        keyboard_buttons = []
        for target in targets[:8]:
            t_id, t_name, owner_id, owner_name = target
            owner_label = f"مملكة: {owner_name}" if owner_name else "منطقة محايدة مستقلة"
            text += f"• **{t_name}** ({owner_label})\n"
            keyboard_buttons.append([InlineKeyboardButton(f"هجوم {t_name}", callback_data=f"هجوم {t_id}")])

        keyboard_buttons.append([InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")])
        await safe_edit_or_reply(query, text, InlineKeyboardMarkup(keyboard_buttons))

    elif data.startswith("هجوم "):
        target_t_id = int(data.split(" ")[1])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT soldiers, armored_vehicles FROM empires WHERE user_id = ?", (user_id,))
        attacker_data = cursor.fetchone()
        
        cursor.execute("SELECT name, owner_id FROM territories WHERE id = ?", (target_t_id,))
        target_t_data = cursor.fetchone()
        
        if not attacker_data or not target_t_data:
            conn.close()
            await query.answer("حدث خطأ في بيانات الهجوم!", show_alert=True)
            return

        att_soldiers, att_armored = attacker_data
        t_name, owner_id = target_t_data

        attacker_power = (att_soldiers * 1) + (att_armored * 50)

        if owner_id is None:
            defender_power = 80
        else:
            cursor.execute("SELECT soldiers, armored_vehicles, shields FROM empires WHERE user_id = ?", (owner_id,))
            defender_empire = cursor.fetchone()
            if defender_empire:
                def_soldiers, def_armored, def_shields = defender_empire
                if def_shields > 0:
                    cursor.execute("UPDATE empires SET shields = shields - 1 WHERE user_id = ?", (owner_id,))
                    conn.commit()
                    conn.close()
                    await safe_edit_or_reply(query,
                        f"🛡️ **فشل الهجوم العسكري!**\n\n"
                        f"لقد هاجمت مقاطعة **{t_name}**، لكن إمبراطورية العدو كانت محمية بـ **درع دفاعي ملكي**!\n"
                        f"تم امتصاص ضربة الهجوم وتدمير درع واحد للعدو دون تغيير في سيطرة المقاطعة.",
                        get_main_game_keyboard()
                    )
                    return
                defender_power = (def_soldiers * 1) + (def_armored * 50) + 150
            else:
                defender_power = 100

        if attacker_power >= defender_power:
            loot = random.randint(300, 700)
            cursor.execute("UPDATE territories SET owner_id = ?, level = 1, facility_type = 'مزارع' WHERE id = ?", (user_id, target_t_id))
            cursor.execute("UPDATE empires SET gold = gold + ?, territories_count = territories_count + 1 WHERE user_id = ?", (loot, user_id))
            
            if owner_id:
                cursor.execute("UPDATE empires SET territories_count = MAX(0, territories_count - 1) WHERE user_id = ?", (owner_id,))
            
            conn.commit()
            conn.close()

            await safe_edit_or_reply(query,
                f"🎉 **انتصار ساحق ومجيد يا جلالة الإمبراطور!**\n\n"
                f"قواتك الباسلة دكت حصون مقاطعة **{t_name}** وسحقت دفاعاتها!\n"
                f"• تم ضم المقاطعة إلى حدود إمبراطوريتك.\n"
                f"• تم غنم غنائم الحرب: **+ {loot} قطعة ذهبية** إلى خزينتك الملكية.",
                get_main_game_keyboard()
            )
        else:
            lost_soldiers = min(att_soldiers, random.randint(20, 50))
            cursor.execute("UPDATE empires SET soldiers = soldiers - ? WHERE user_id = ?", (lost_soldiers, user_id))
            conn.commit()
            conn.close()

            await safe_edit_or_reply(query,
                f"⚠️ **تصدى العدو لهجومك باقتدار!**\n\n"
                f"فشلت القوات في اختراق تحصينات مقاطعة **{t_name}**.\n"
                f"• خسائر المعركة: فقدان **{lost_soldiers} جندي** من صفوف الجيش.",
                get_main_game_keyboard()
            )

    elif data == "الرئيسية":
        await safe_edit_or_reply(query,
            "🏰 **لوحة تحكم الإمبراطورية الرئيسية:**",
            get_main_game_keyboard()
        )

# دالة مساعدة لتحديث الرسائل النصية بأمان وتجنب مشاكل الصور أو النصوص الفارغة
async def safe_edit_or_reply(query, text, reply_markup):
    try:
        if query.message.photo:
            await query.message.delete()
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception:
        try:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass

async def handle_game_callbacks_refresh_shields(query, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT shields, gold FROM empires WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    shields, gold = res if res else (5, 0)
    
    await safe_edit_or_reply(query,
        f"🛡️ **نظام دروع الحماية الملكية**\n\n"
        f"دروعك الحالية: **{shields} من 5 دروع**.\n"
        f"تكلفة شحن درع جديد: **200 قطعة ذهب**.\n\n"
        f"رصيدك الحالي: 💰 {gold} ذهبة",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("شراء درع جديد", callback_data="شراء درع")],
            [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
        ])
    )

async def handle_game_callbacks_refresh_recruitment(query, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT soldiers, armored_vehicles, gold FROM empires WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    soldiers, armored, gold = res if res else (150, 5, 0)
    
    await safe_edit_or_reply(query,
        f"⚔️ **ثكنة تجنيد الجيش والمدرعات الحربية**\n\n"
        f"• جنودك الحاليون: **{soldiers} جندي**\n"
        f"• مدرعاتك الحربية: **{armored} مدرعة**\n"
        f"• رصيد الذهب: 💰 {gold}",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("تجنيد جنود", callback_data="تجنيد جنود")],
            [InlineKeyboardButton("صنع مدرعة", callback_data="صنع مدرعة")],
            [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
        ])
    )
